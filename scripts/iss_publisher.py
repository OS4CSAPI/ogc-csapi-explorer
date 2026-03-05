#!/usr/bin/env python3
"""
iss_publisher.py — Live ISS position publisher for OS4CSAPI.

Fetches NORAD GP element sets from CelesTrak, propagates them with SGP4,
and POSTs geodetic positions (lat, lon, alt) as CSAPI observations to
the OSH server every 30 seconds.

Also updates a SamplingFeature LineString (orbit track) every 5 minutes,
covering ±45 minutes of predicted/past ground track.

Resource IDs (created on server):
  System:      04ng  (ISS Tracker)
  DataStream:  04fg  (ISS Position)

Usage:
    python iss_publisher.py                    # run forever (30s cadence)
    python iss_publisher.py --dry-run          # print, don't POST
    python iss_publisher.py --interval 10      # 10s cadence
    python iss_publisher.py --once             # single observation then exit
    python iss_publisher.py --tle-refresh 7200 # refresh TLE every 2h (default 1h)

Requires: Python 3.10+, sgp4 (pip install sgp4)
"""

import argparse
import base64
import json
import math
import ssl
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    from sgp4.api import Satrec, WGS72
except ImportError:
    print("ERROR: sgp4 package not found. Install it with: pip install sgp4")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

SYSTEM_ID     = "04ng"
DATASTREAM_ID = "04fg"

# CelesTrak GP query for ISS (NORAD 25544)
CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON"

# Orbit track: ±45 min window, 60-second resolution
TRACK_HALF_WINDOW_MIN = 45
TRACK_STEP_SEC        = 60

_AUTH_HEADER = "Basic " + base64.b64encode(
    f"{AUTH_USER}:{AUTH_PASS}".encode()
).decode()

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ═══════════════════════════════════════════════════════════════════════════
#  HTTP helpers (matches simulate_scenario.py pattern)
# ═══════════════════════════════════════════════════════════════════════════

def _request(method: str, url: str, body: dict | None = None,
             content_type: str = "application/json",
             accept: str = "application/json",
             timeout: int = 15) -> dict | str | None:
    """Generic HTTP request with auth + TLS bypass."""
    headers = {
        "Authorization": _AUTH_HEADER,
        "Accept": accept,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = content_type
        data = json.dumps(body).encode()

    req = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            location = resp.headers.get("Location", "")
            raw = resp.read().decode()
            if location:
                return {"id": location.rstrip("/").split("/")[-1], "_location": location}
            if resp.status == 204 or not raw.strip():
                return None
            return json.loads(raw)
    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} {method} {url}: {body_text[:500]}")


def api_post(path: str, body: dict, content_type: str = "application/om+json"):
    return _request("POST", f"{BASE_URL}/{path}", body=body, content_type=content_type)


def api_put(path: str, body: dict, content_type: str = "application/geo+json"):
    return _request("PUT", f"{BASE_URL}/{path}", body=body, content_type=content_type)


def api_get(path: str):
    return _request("GET", f"{BASE_URL}/{path}")


# ═══════════════════════════════════════════════════════════════════════════
#  CelesTrak TLE / OMM fetch
# ═══════════════════════════════════════════════════════════════════════════

_cached_satrec: Satrec | None = None
_tle_fetched_at: float = 0.0
_tle_epoch_str: str = ""


def fetch_tle_from_celestrak() -> Satrec:
    """Fetch the latest ISS GP elements from CelesTrak (OMM JSON format)."""
    global _cached_satrec, _tle_fetched_at, _tle_epoch_str

    req = Request(CELESTRAK_URL, headers={"Accept": "application/json"})
    # CelesTrak uses proper TLS
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if isinstance(data, list) and len(data) > 0:
        omm = data[0]
    else:
        raise RuntimeError(f"Unexpected CelesTrak response: {str(data)[:200]}")

    # Build Satrec from OMM fields (CelesTrak JSON doesn't include TLE lines)
    sat = Satrec()
    sat.sgp4init(
        WGS72,                                    # gravity model
        'i',                                      # improved mode
        int(omm.get("NORAD_CAT_ID", 25544)),      # satnum
        _epoch_to_jdsatepoch(omm["EPOCH"]),        # epoch (days since 1949-12-31)
        float(omm.get("BSTAR", 0.0)),             # bstar drag
        float(omm.get("MEAN_MOTION_DOT", 0.0)) / (2.0 * math.pi / 1440.0**2),  # ndot (ignored for SGP4, pass 0 is fine)
        float(omm.get("MEAN_MOTION_DDOT", 0.0)),  # nddot
        float(omm["ECCENTRICITY"]),                # ecco
        math.radians(float(omm["ARG_OF_PERICENTER"])),  # argpo (rad)
        math.radians(float(omm["INCLINATION"])),         # inclo (rad)
        math.radians(float(omm["MEAN_ANOMALY"])),        # mo (rad)
        float(omm["MEAN_MOTION"]) * 2.0 * math.pi / 1440.0,  # no_kozai (rad/min)
        math.radians(float(omm["RA_OF_ASC_NODE"])),      # nodeo (rad)
    )

    _cached_satrec = sat
    _tle_fetched_at = time.time()
    _tle_epoch_str = omm.get("EPOCH", "unknown")
    return sat


def _epoch_to_jdsatepoch(epoch_str: str) -> float:
    """Convert OMM EPOCH string to days since 1949-12-31 00:00 UT (sgp4 epoch)."""
    dt = datetime.strptime(epoch_str, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    # sgp4 epoch = Julian date - 2433281.5  (JD of 1949-12-31 00:00 UT)
    jd, fr = _datetime_to_jd(dt)
    return (jd + fr) - 2433281.5


def get_satrec(refresh_interval: float = 3600.0) -> Satrec:
    """Return cached Satrec, refreshing TLE if stale."""
    global _cached_satrec, _tle_fetched_at
    if _cached_satrec is None or (time.time() - _tle_fetched_at) > refresh_interval:
        fetch_tle_from_celestrak()
    return _cached_satrec


# ═══════════════════════════════════════════════════════════════════════════
#  SGP4 propagation → geodetic (lat, lon, alt)
# ═══════════════════════════════════════════════════════════════════════════

def propagate_to_geodetic(sat: Satrec, dt: datetime) -> tuple[float, float, float]:
    """
    Propagate satellite to given datetime → (lat_deg, lon_deg, alt_km).
    Uses SGP4 to get ECI position, then converts to geodetic.
    """
    # SGP4 expects Julian date split into two parts
    jd, fr = _datetime_to_jd(dt)
    e, r, v = sat.sgp4(jd, fr)

    if e != 0:
        raise RuntimeError(f"SGP4 propagation error code {e}")

    # r is ECI position in km [x, y, z]
    x, y, z = r  # km, ECI (TEME)

    # Convert ECI (TEME) → geodetic (lat, lon, alt)
    lat, lon, alt = eci_to_geodetic(x, y, z, dt)
    return lat, lon, alt


def _datetime_to_jd(dt: datetime) -> tuple[float, float]:
    """Convert datetime to Julian date (jd, fraction) for sgp4."""
    # Julian date calculation
    y = dt.year
    m = dt.month
    d = dt.day

    if m <= 2:
        y -= 1
        m += 12

    A = y // 100
    B = 2 - A + A // 4
    jd_day = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

    fr = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0 +
          dt.microsecond / 3_600_000_000.0) / 24.0

    return jd_day, fr


def eci_to_geodetic(x_km: float, y_km: float, z_km: float,
                    dt: datetime) -> tuple[float, float, float]:
    """
    Convert ECI (TEME) position vector to geodetic (lat, lon, alt).
    Uses GMST for sidereal time rotation.
    """
    # Earth parameters (WGS-72 to match sgp4)
    a_e = 6378.135       # equatorial radius, km
    f   = 1.0 / 298.26   # flattening

    # GMST (Greenwich Mean Sidereal Time) in radians
    gmst = _gmst_rad(dt)

    # ECI → ECEF rotation (just rotate around Z by -GMST)
    cos_g = math.cos(gmst)
    sin_g = math.sin(gmst)
    x_ecef = x_km * cos_g + y_km * sin_g
    y_ecef = -x_km * sin_g + y_km * cos_g
    z_ecef = z_km

    # ECEF → geodetic (iterative)
    lon = math.atan2(y_ecef, x_ecef)
    r_xy = math.sqrt(x_ecef**2 + y_ecef**2)

    e2 = 2 * f - f**2  # first eccentricity squared
    lat = math.atan2(z_ecef, r_xy)  # initial estimate

    for _ in range(10):
        sin_lat = math.sin(lat)
        N = a_e / math.sqrt(1 - e2 * sin_lat**2)
        lat_new = math.atan2(z_ecef + e2 * N * sin_lat, r_xy)
        if abs(lat_new - lat) < 1e-12:
            break
        lat = lat_new

    sin_lat = math.sin(lat)
    N = a_e / math.sqrt(1 - e2 * sin_lat**2)
    alt = r_xy / math.cos(lat) - N if abs(math.cos(lat)) > 1e-10 else abs(z_ecef) - N * (1 - e2)

    return math.degrees(lat), math.degrees(lon), alt


def _gmst_rad(dt: datetime) -> float:
    """Compute Greenwich Mean Sidereal Time in radians for a given UTC datetime."""
    # Julian centuries from J2000.0
    jd, fr = _datetime_to_jd(dt)
    jd_full = jd + fr
    T = (jd_full - 2451545.0) / 36525.0

    # GMST in seconds (IAU 1982 formula)
    gmst_sec = (67310.54841 +
                (876600.0 * 3600 + 8640184.812866) * T +
                0.093104 * T**2 -
                6.2e-6 * T**3)

    # Convert to radians (86400 sec = 2π rad)
    gmst_rad = (gmst_sec % 86400) / 86400.0 * 2 * math.pi
    if gmst_rad < 0:
        gmst_rad += 2 * math.pi

    return gmst_rad


# ═══════════════════════════════════════════════════════════════════════════
#  Orbit track (SamplingFeature LineString)
# ═══════════════════════════════════════════════════════════════════════════

_last_track_update: float = 0.0
TRACK_UPDATE_INTERVAL = 300  # 5 minutes


def build_orbit_track(sat: Satrec, now: datetime) -> list[list[float]]:
    """
    Build a LineString coordinate array for the orbit ground track.
    Covers ±TRACK_HALF_WINDOW_MIN around `now` at TRACK_STEP_SEC resolution.
    """
    coords = []
    start = now - timedelta(minutes=TRACK_HALF_WINDOW_MIN)
    end = now + timedelta(minutes=TRACK_HALF_WINDOW_MIN)
    t = start
    while t <= end:
        try:
            lat, lon, alt = propagate_to_geodetic(sat, t)
            coords.append([round(lon, 4), round(lat, 4)])
        except Exception:
            pass  # skip propagation errors near epoch boundaries
        t += timedelta(seconds=TRACK_STEP_SEC)
    return coords


def update_sampling_feature(sat: Satrec, now: datetime, dry_run: bool = False):
    """
    Create or update the SamplingFeature with an orbit track LineString.
    """
    global _last_track_update

    if (time.time() - _last_track_update) < TRACK_UPDATE_INTERVAL:
        return  # not time yet

    coords = build_orbit_track(sat, now)
    if len(coords) < 2:
        print("  [WARN] Not enough track points, skipping SF update")
        return

    sf_body = {
        "type": "Feature",
        "properties": {
            "uid": "urn:os4csapi:sf:iss-orbit-track:v1",
            "featureType": "sams:SF_SpatialSamplingFeature",
            "name": "ISS Orbit Track",
            "description": f"Ground track of ISS orbit (±{TRACK_HALF_WINDOW_MIN} min). Updated every {TRACK_UPDATE_INTERVAL}s.",
            "validTime": [now.strftime("%Y-%m-%dT%H:%M:%SZ"), ".."],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords,
        },
    }

    if dry_run:
        print(f"  [DRY] Would update SF with {len(coords)} track points")
    else:
        try:
            # Try to find existing SF first
            existing = None
            try:
                existing = api_get(f"systems/{SYSTEM_ID}/samplingFeatures")
            except Exception:
                pass  # server may not support this query; fall through to create

            if existing and "items" in existing and len(existing["items"]) > 0:
                sf_id = existing["items"][0]["id"]
                api_put(f"samplingFeatures/{sf_id}", sf_body)
                print(f"  [SF] Updated orbit track ({len(coords)} pts, id={sf_id})")
            else:
                # Create new
                result = api_post(
                    f"systems/{SYSTEM_ID}/samplingFeatures",
                    sf_body,
                    content_type="application/geo+json",
                )
                sf_id = result.get("id", "?") if result else "?"
                print(f"  [SF] Created orbit track ({len(coords)} pts, id={sf_id})")
        except Exception as e:
            print(f"  [SF] ERROR: {e}")

    _last_track_update = time.time()


# ═══════════════════════════════════════════════════════════════════════════
#  Observation builder
# ═══════════════════════════════════════════════════════════════════════════

def build_observation(lat: float, lon: float, alt_km: float,
                      now: datetime) -> dict:
    """Build an om+json observation matching the ISS Position datastream schema."""
    iso = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    return {
        "phenomenonTime": iso,
        "resultTime": iso,
        "result": {
            "timestamp": now.timestamp(),
            "lat_deg": round(lat, 6),
            "lon_deg": round(lon, 6),
            "alt_km": round(alt_km, 3),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Main loop
# ═══════════════════════════════════════════════════════════════════════════

def run(*, interval: float = 30.0, dry_run: bool = False,
        once: bool = False, tle_refresh: float = 3600.0):
    """Main publisher loop."""
    print("=" * 70)
    print("  ISS Position Publisher — OS4CSAPI")
    print("=" * 70)
    print(f"  Server:       {BASE_URL}")
    print(f"  System:       {SYSTEM_ID}")
    print(f"  DataStream:   {DATASTREAM_ID}")
    print(f"  Interval:     {interval}s")
    print(f"  TLE refresh:  {tle_refresh}s")
    print(f"  Dry run:      {dry_run}")
    print()

    # Fetch initial TLE
    print("  Fetching TLE from CelesTrak...")
    try:
        sat = fetch_tle_from_celestrak()
        print(f"  TLE epoch: {_tle_epoch_str}")
    except Exception as e:
        print(f"  FATAL: Could not fetch TLE: {e}")
        sys.exit(1)

    stats = {"published": 0, "errors": 0, "sf_updates": 0}
    tick = 0
    start_time = time.time()

    try:
        while True:
            now = datetime.now(timezone.utc)

            # Refresh TLE if stale
            try:
                sat = get_satrec(tle_refresh)
            except Exception as e:
                print(f"  [WARN] TLE refresh failed (using cached): {e}")

            # Propagate to current position
            try:
                lat, lon, alt_km = propagate_to_geodetic(sat, now)
            except Exception as e:
                print(f"  [ERR] Propagation failed: {e}")
                time.sleep(interval)
                continue

            tick += 1
            ts = now.strftime("%H:%M:%S")
            print(f"  [{ts}] #{tick:5d} | lat={lat:+9.4f}° lon={lon:+10.4f}° alt={alt_km:7.1f} km")

            # Build and publish observation
            obs = build_observation(lat, lon, alt_km, now)
            if dry_run:
                print(f"           [DRY] {json.dumps(obs['result'], separators=(',', ':'))}")
            else:
                try:
                    api_post(f"datastreams/{DATASTREAM_ID}/observations", obs)
                    stats["published"] += 1
                except Exception as e:
                    print(f"           [ERR] POST failed: {e}")
                    stats["errors"] += 1

            # Update orbit track SamplingFeature periodically
            try:
                sf_before = _last_track_update
                update_sampling_feature(sat, now, dry_run=dry_run)
                if _last_track_update != sf_before:
                    stats["sf_updates"] += 1
            except Exception as e:
                print(f"           [ERR] SF update: {e}")

            if once:
                break

            # Sleep until next tick
            next_tick = start_time + tick * interval
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C — stopping publisher.")

    # Summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"  Summary ({elapsed:.0f}s elapsed)")
    print(f"  Published:    {stats['published']} observations")
    print(f"  SF updates:   {stats['sf_updates']}")
    print(f"  Errors:       {stats['errors']}")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ISS position publisher for OS4CSAPI (SGP4 + CelesTrak)")
    parser.add_argument("--interval", type=float, default=30.0,
                        help="Seconds between observations (default: 30)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print observations but don't POST them")
    parser.add_argument("--once", action="store_true",
                        help="Publish a single observation then exit")
    parser.add_argument("--tle-refresh", type=float, default=3600.0,
                        help="Seconds between TLE refreshes (default: 3600)")
    args = parser.parse_args()

    run(
        interval=args.interval,
        dry_run=args.dry_run,
        once=args.once,
        tle_refresh=args.tle_refresh,
    )


if __name__ == "__main__":
    main()
