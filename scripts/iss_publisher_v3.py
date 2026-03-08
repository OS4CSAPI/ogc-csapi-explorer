#!/usr/bin/env python3
"""
iss_publisher_v3.py — Dual-product satellite publisher for CSAPI/OSH servers.

Publishes TWO products from ISS NORAD TLE data:
  1. Position fixes (11 fields, every 30s) → ISS Position Publisher system
  2. Orbit ground-track predictions (100 points, every 5min) → ISS Orbit Track Publisher system

Uses OSHConnect-Python for CSAPI transport, SGP4 for orbital propagation.
Fetches NORAD GP element sets from CelesTrak, propagates with SGP4.

Configure via environment variables:
    OSH_ADDRESS        Server hostname            (default: os4csapi-osh.duckdns.org)
    OSH_PORT           Server port                (default: 443)
    OSH_USER           Auth username              (default: os4csapi)
    OSH_PASS           Auth password              (default: ogc134mm)
    OSH_ROOT           SensorHub root path        (default: sensorhub)
    POS_SYSTEM_UID     Position system URN        (default: urn:os4csapi:system:iss-position-publisher:v1)
    POS_DS_NAME        Position datastream name   (default: ISS Position (SGP4))
    TRACK_SYSTEM_UID   Orbit track system URN     (default: urn:os4csapi:system:iss-orbittrack-publisher:v1)
    TRACK_DS_NAME      Orbit track DS name        (default: ISS Orbit Ground Track)
    NORAD_ID           NORAD catalog number       (default: 25544)

Usage:
    python iss_publisher_v3.py                    # run forever
    python iss_publisher_v3.py --dry-run          # print, don't POST
    python iss_publisher_v3.py --interval 10      # 10s position cadence
    python iss_publisher_v3.py --once             # single observation then exit
    python iss_publisher_v3.py --tle-refresh 7200 # refresh TLE every 2h (default 1h)
    python iss_publisher_v3.py --track-interval 600  # orbit track every 10min (default 300s)
    python iss_publisher_v3.py --no-track         # disable orbit track publishing

Requires: Python 3.12+, sgp4, oshconnect
"""

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen  # retained for CelesTrak only

try:
    from sgp4.api import Satrec, WGS72
except ImportError:
    print("ERROR: sgp4 package not found. Install it with: pip install sgp4")
    sys.exit(1)

try:
    from oshconnect import OSHConnect, Node, Datastream
    _HAS_OSHCONNECT = True
except ImportError:
    _HAS_OSHCONNECT = False


# ═══════════════════════════════════════════════════════════════════════════
#  Configuration (env vars with sensible defaults)
# ═══════════════════════════════════════════════════════════════════════════

OSH_ADDRESS     = os.environ.get("OSH_ADDRESS", "os4csapi-osh.duckdns.org")
OSH_PORT        = int(os.environ.get("OSH_PORT", "443"))
OSH_USER        = os.environ.get("OSH_USER", "os4csapi")
OSH_PASS        = os.environ.get("OSH_PASS", "ogc134mm")
OSH_ROOT        = os.environ.get("OSH_ROOT", "sensorhub")
NORAD_ID        = os.environ.get("NORAD_ID", "25544")
ASSET_NAME      = os.environ.get("ASSET_NAME", "ISS (ZARYA)")

# Position publisher
POS_SYSTEM_UID  = os.environ.get("POS_SYSTEM_UID",
                                  "urn:os4csapi:system:iss-position-publisher:v1")
POS_DS_NAME     = os.environ.get("POS_DS_NAME", "ISS Position (SGP4)")

# Orbit track publisher
TRACK_SYSTEM_UID = os.environ.get("TRACK_SYSTEM_UID",
                                   "urn:os4csapi:system:iss-orbittrack-publisher:v1")
TRACK_DS_NAME    = os.environ.get("TRACK_DS_NAME", "ISS Orbit Ground Track")

# Orbit track generation parameters
TRACK_DURATION_MIN    = 100   # ~1 full orbit
TRACK_POINT_INTERVAL  = 60    # seconds between track points

CELESTRAK_URL = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={NORAD_ID}&FORMAT=JSON"

# Reconnect threshold
RECONNECT_THRESHOLD = 5


# ═══════════════════════════════════════════════════════════════════════════
#  OSHConnect server connection (with retry / backoff)
# ═══════════════════════════════════════════════════════════════════════════

def _discover_system_ds(app, node, system_uid: str, ds_name: str):
    """Find a system by UID and a datastream by name. Returns (system, datastream) or raises."""
    from oshconnect.csapi4py.constants import APIResourceTypes

    # Discover all systems if not already done
    if not app._systems:
        app.discover_systems()

        # Patch resource IDs (OSHConnect-Python bug workaround)
        raw_res = node.get_api_helper().retrieve_resource(
            APIResourceTypes.SYSTEM, req_headers={})
        if raw_res.ok:
            uid_to_id = {}
            for item in raw_res.json().get("items", []):
                uid = item.get("properties", {}).get("uid", "")
                rid = item.get("id", "")
                if uid and rid:
                    uid_to_id[uid] = rid
            for s in app._systems:
                if s.urn in uid_to_id:
                    s._resource_id = uid_to_id[s.urn]

    # Find system
    system = None
    for s in app._systems:
        if s.urn == system_uid:
            system = s
            break
    if system is None:
        available = [s.urn for s in app._systems]
        raise RuntimeError(
            f"System '{system_uid}' not found on server. Available: {available}")

    # Find datastream
    if not hasattr(node, '_mqtt_client'):
        node._mqtt_client = None

    ds_resources = system.discover_datastreams()
    ds = None
    for res in ds_resources:
        if res.name == ds_name:
            ds = Datastream(parent_node=node, datastream_resource=res)
            break

    if ds is None:
        available = [r.name for r in ds_resources]
        raise RuntimeError(
            f"Datastream '{ds_name}' not found for system '{system_uid}'. "
            f"Available: {available}")

    return system, ds


def connect_and_discover(*, enable_track: bool = True):
    """Connect to OSH server and discover both systems + datastreams."""
    if not _HAS_OSHCONNECT:
        print("  FATAL: oshconnect package not found. Install with:")
        print("    pip install git+https://github.com/OS4CSAPI/OSHConnect-Python.git")
        sys.exit(1)

    app = OSHConnect("satellite-publisher-v3")
    node = Node(
        protocol="https",
        address=OSH_ADDRESS,
        port=OSH_PORT,
        username=OSH_USER,
        password=OSH_PASS,
        server_root=OSH_ROOT,
    )
    app.add_node(node)

    if not hasattr(node, '_mqtt_client'):
        node._mqtt_client = None

    # Position system (always required)
    pos_sys, pos_ds = _discover_system_ds(app, node, POS_SYSTEM_UID, POS_DS_NAME)
    print(f"  Position:   system={pos_sys.urn}, ds={pos_ds._underlying_resource.name} "
          f"(id={pos_ds.get_id()})")

    # Orbit track system (optional)
    track_ds = None
    if enable_track:
        try:
            track_sys, track_ds = _discover_system_ds(
                app, node, TRACK_SYSTEM_UID, TRACK_DS_NAME)
            print(f"  Track:      system={track_sys.urn}, ds={track_ds._underlying_resource.name} "
                  f"(id={track_ds.get_id()})")
        except RuntimeError as e:
            print(f"  [WARN] Orbit track system not found — track publishing disabled: {e}")
            track_ds = None

    return app, node, pos_ds, track_ds


def connect_with_retry(
    *,
    enable_track: bool = True,
    max_attempts: int = 10,
    base_delay: float = 5.0,
    max_delay: float = 120.0,
):
    """Connect to OSH server with exponential backoff + jitter."""
    for attempt in range(1, max_attempts + 1):
        try:
            return connect_and_discover(enable_track=enable_track)
        except Exception as e:
            if attempt == max_attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = delay * 0.2 * (random.random() - 0.5)
            wait = delay + jitter
            print(f"  [WARN] Connection attempt {attempt}/{max_attempts} failed: {e}")
            print(f"         Retrying in {wait:.1f}s...")
            time.sleep(wait)
    raise RuntimeError("connect_with_retry: exhausted all attempts")


# ═══════════════════════════════════════════════════════════════════════════
#  CelesTrak TLE / OMM fetch
# ═══════════════════════════════════════════════════════════════════════════

_cached_satrec: Satrec | None = None
_tle_fetched_at: float = 0.0
_tle_epoch_str: str = ""
_tle_epoch_dt: datetime | None = None


def fetch_tle_from_celestrak() -> Satrec:
    """Fetch the latest GP elements from CelesTrak (OMM JSON format)."""
    global _cached_satrec, _tle_fetched_at, _tle_epoch_str, _tle_epoch_dt

    req = Request(CELESTRAK_URL, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if isinstance(data, list) and len(data) > 0:
        omm = data[0]
    else:
        raise RuntimeError(f"Unexpected CelesTrak response: {str(data)[:200]}")

    sat = Satrec()
    sat.sgp4init(
        WGS72,
        'i',
        int(omm.get("NORAD_CAT_ID", NORAD_ID)),
        _epoch_to_jdsatepoch(omm["EPOCH"]),
        float(omm.get("BSTAR", 0.0)),
        float(omm.get("MEAN_MOTION_DOT", 0.0)) / (2.0 * math.pi / 1440.0**2),
        float(omm.get("MEAN_MOTION_DDOT", 0.0)),
        float(omm["ECCENTRICITY"]),
        math.radians(float(omm["ARG_OF_PERICENTER"])),
        math.radians(float(omm["INCLINATION"])),
        math.radians(float(omm["MEAN_ANOMALY"])),
        float(omm["MEAN_MOTION"]) * 2.0 * math.pi / 1440.0,
        math.radians(float(omm["RA_OF_ASC_NODE"])),
    )

    _cached_satrec = sat
    _tle_fetched_at = time.time()
    _tle_epoch_str = omm.get("EPOCH", "unknown")
    try:
        _tle_epoch_dt = datetime.strptime(
            _tle_epoch_str, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        _tle_epoch_dt = None
    return sat


def _epoch_to_jdsatepoch(epoch_str: str) -> float:
    """Convert OMM EPOCH string to days since 1949-12-31 00:00 UT (sgp4 epoch)."""
    dt = datetime.strptime(epoch_str, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    jd, fr = _datetime_to_jd(dt)
    return (jd + fr) - 2433281.5


def get_satrec(refresh_interval: float = 3600.0) -> Satrec:
    """Return cached Satrec, refreshing TLE if stale."""
    global _cached_satrec, _tle_fetched_at
    if _cached_satrec is None or (time.time() - _tle_fetched_at) > refresh_interval:
        fetch_tle_from_celestrak()
    return _cached_satrec


# ═══════════════════════════════════════════════════════════════════════════
#  SGP4 propagation → geodetic
# ═══════════════════════════════════════════════════════════════════════════

def propagate_to_geodetic(sat: Satrec, dt: datetime) -> tuple[float, float, float, float]:
    """Propagate satellite to given datetime → (lat_deg, lon_deg, alt_km, velocity_km_s)."""
    jd, fr = _datetime_to_jd(dt)
    e, r, v = sat.sgp4(jd, fr)

    if e != 0:
        raise RuntimeError(f"SGP4 propagation error code {e}")

    x, y, z = r   # km, ECI (TEME)
    vx, vy, vz = v  # km/s, ECI (TEME)

    lat, lon, alt = eci_to_geodetic(x, y, z, dt)
    velocity_km_s = math.sqrt(vx**2 + vy**2 + vz**2)

    return lat, lon, alt, velocity_km_s


def _datetime_to_jd(dt: datetime) -> tuple[float, float]:
    """Convert datetime to Julian date (jd, fraction) for sgp4."""
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
    """Convert ECI (TEME) position vector to geodetic (lat, lon, alt)."""
    a_e = 6378.135        # equatorial radius, km (WGS-72)
    f   = 1.0 / 298.26   # flattening

    gmst = _gmst_rad(dt)

    cos_g = math.cos(gmst)
    sin_g = math.sin(gmst)
    x_ecef = x_km * cos_g + y_km * sin_g
    y_ecef = -x_km * sin_g + y_km * cos_g
    z_ecef = z_km

    lon = math.atan2(y_ecef, x_ecef)
    r_xy = math.sqrt(x_ecef**2 + y_ecef**2)

    e2 = 2 * f - f**2
    lat = math.atan2(z_ecef, r_xy)

    for _ in range(10):
        sin_lat = math.sin(lat)
        N = a_e / math.sqrt(1 - e2 * sin_lat**2)
        lat_new = math.atan2(z_ecef + e2 * N * sin_lat, r_xy)
        if abs(lat_new - lat) < 1e-12:
            break
        lat = lat_new

    sin_lat = math.sin(lat)
    N = a_e / math.sqrt(1 - e2 * sin_lat**2)
    alt = (r_xy / math.cos(lat) - N
           if abs(math.cos(lat)) > 1e-10
           else abs(z_ecef) - N * (1 - e2))

    return math.degrees(lat), math.degrees(lon), alt


def _gmst_rad(dt: datetime) -> float:
    """Compute Greenwich Mean Sidereal Time in radians."""
    jd, fr = _datetime_to_jd(dt)
    jd_full = jd + fr
    T = (jd_full - 2451545.0) / 36525.0

    gmst_sec = (67310.54841 +
                (876600.0 * 3600 + 8640184.812866) * T +
                0.093104 * T**2 -
                6.2e-6 * T**3)

    gmst_rad = (gmst_sec % 86400) / 86400.0 * 2 * math.pi
    if gmst_rad < 0:
        gmst_rad += 2 * math.pi

    return gmst_rad


# ═══════════════════════════════════════════════════════════════════════════
#  Position error estimate
# ═══════════════════════════════════════════════════════════════════════════

def estimate_position_error_m(tle_age_sec: float) -> float:
    """Rough SGP4 position error based on TLE age.

    At epoch: ~1 km.  Grows ~1-2 km/day of TLE age.
    Returns meters.
    """
    age_days = abs(tle_age_sec) / 86400.0
    error_km = 1.0 + 1.5 * age_days   # conservative linear model
    return round(error_km * 1000.0, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  Observation builders
# ═══════════════════════════════════════════════════════════════════════════

def build_position_observation(
    lat: float, lon: float, alt_km: float, velocity_km_s: float,
    now: datetime,
) -> dict:
    """Build an 11-field position observation dict."""
    iso = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    tle_age_sec = 0.0
    source_epoch_iso = _tle_epoch_str
    if _tle_epoch_dt is not None:
        tle_age_sec = (now - _tle_epoch_dt).total_seconds()
        source_epoch_iso = _tle_epoch_dt.strftime("%Y-%m-%dT%H:%M:%S.") + \
            f"{_tle_epoch_dt.microsecond // 1000:03d}Z"

    return {
        "phenomenonTime": iso,
        "resultTime": iso,
        "result": {
            "timestamp": now.timestamp(),
            "lat_deg": round(lat, 6),
            "lon_deg": round(lon, 6),
            "alt_km": round(alt_km, 3),
            "velocity_km_s": round(velocity_km_s, 3),
            "noradId": int(NORAD_ID),
            "assetName": ASSET_NAME,
            "sourceEpoch": source_epoch_iso,
            "sourceAgeSec": round(tle_age_sec, 1),
            "posErrorM": estimate_position_error_m(tle_age_sec),
            "method": "SGP4",
        },
    }


def build_orbit_track_observation(sat: Satrec, now: datetime) -> dict:
    """Build a predicted ground-track observation (100 points, ~100 min ahead)."""
    iso = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    points = []
    num_points = TRACK_DURATION_MIN * 60 // TRACK_POINT_INTERVAL
    for i in range(num_points):
        dt = now + timedelta(seconds=i * TRACK_POINT_INTERVAL)
        try:
            lat, lon, alt, _ = propagate_to_geodetic(sat, dt)
            points.append({
                "timestamp": round(dt.timestamp(), 1),
                "lat_deg": round(lat, 4),
                "lon_deg": round(lon, 4),
                "alt_km": round(alt, 1),
            })
        except RuntimeError:
            continue  # skip failed propagation point

    return {
        "phenomenonTime": iso,
        "resultTime": iso,
        "result": {
            "computedAt": now.timestamp(),
            "noradId": int(NORAD_ID),
            "assetName": ASSET_NAME,
            "durationMin": TRACK_DURATION_MIN,
            "numPoints": len(points),
            "method": "SGP4",
            "trackPointsJson": json.dumps(points, separators=(",", ":")),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Main loop
# ═══════════════════════════════════════════════════════════════════════════

def run(*, interval: float = 30.0, dry_run: bool = False,
        once: bool = False, tle_refresh: float = 3600.0,
        track_interval: float = 300.0, enable_track: bool = True):
    """Main publisher loop — publishes position fixes + orbit tracks."""
    print("=" * 70)
    print("  Satellite Publisher v3 (Position + Orbit Track)")
    print("=" * 70)
    print(f"  Server:         https://{OSH_ADDRESS}:{OSH_PORT}/{OSH_ROOT}/api")
    print(f"  Position UID:   {POS_SYSTEM_UID}")
    print(f"  Position DS:    {POS_DS_NAME}  (every {interval}s)")
    if enable_track:
        print(f"  Track UID:      {TRACK_SYSTEM_UID}")
        print(f"  Track DS:       {TRACK_DS_NAME}  (every {track_interval}s)")
    else:
        print(f"  Track:          DISABLED")
    print(f"  NORAD ID:       {NORAD_ID}")
    print(f"  TLE refresh:    {tle_refresh}s")
    print(f"  Dry run:        {dry_run}")
    print()

    # ── Connect to OSH server ────────────────────────────────────
    pos_ds = None
    track_ds = None
    if not dry_run:
        print("  Connecting to OSH server...")
        app, node, pos_ds, track_ds = connect_with_retry(enable_track=enable_track)
        if track_ds is None and enable_track:
            print("  [INFO] Orbit track system not available — position-only mode.")
    else:
        app, node = None, None

    # ── Fetch initial TLE ────────────────────────────────────────
    print("  Fetching TLE from CelesTrak...")
    try:
        sat = fetch_tle_from_celestrak()
        print(f"  TLE epoch: {_tle_epoch_str}")
    except Exception as e:
        print(f"  FATAL: Could not fetch TLE: {e}")
        sys.exit(1)

    stats = {"pos_published": 0, "track_published": 0, "errors": 0, "reconnects": 0}
    tick = 0
    consecutive_errors = 0
    start_time = time.time()
    last_track_time = 0.0  # force track publish on first tick

    print()
    try:
        while True:
            now = datetime.now(timezone.utc)

            # Refresh TLE if stale
            try:
                sat = get_satrec(tle_refresh)
            except Exception as e:
                print(f"  [WARN] TLE refresh failed (using cached): {e}")

            # ── Position observation ──────────────────────────────
            try:
                lat, lon, alt_km, vel = propagate_to_geodetic(sat, now)
            except Exception as e:
                print(f"  [ERR] Propagation failed: {e}")
                time.sleep(interval)
                continue

            tick += 1
            ts = now.strftime("%H:%M:%S")
            print(f"  [{ts}] #{tick:5d} | lat={lat:+9.4f} lon={lon:+10.4f} "
                  f"alt={alt_km:7.1f}km vel={vel:.3f}km/s")

            obs = build_position_observation(lat, lon, alt_km, vel, now)
            if dry_run:
                r = obs["result"]
                print(f"           [DRY-POS] lat={r['lat_deg']} lon={r['lon_deg']} "
                      f"alt={r['alt_km']} vel={r['velocity_km_s']} "
                      f"err={r['posErrorM']}m age={r['sourceAgeSec']}s")
            elif pos_ds is not None:
                try:
                    pos_ds.insert_observation_dict(obs)
                    stats["pos_published"] += 1
                    consecutive_errors = 0
                except Exception as e:
                    consecutive_errors += 1
                    stats["errors"] += 1
                    print(f"           [ERR] Position publish failed ({consecutive_errors}x): {e}")

            # ── Orbit track observation (less frequent) ───────────
            time_since_track = time.time() - last_track_time
            if enable_track and time_since_track >= track_interval:
                print(f"           Generating orbit track ({TRACK_DURATION_MIN}min, "
                      f"{TRACK_DURATION_MIN * 60 // TRACK_POINT_INTERVAL} points)...")
                track_obs = build_orbit_track_observation(sat, now)
                n_pts = track_obs["result"]["numPoints"]

                if dry_run:
                    print(f"           [DRY-TRACK] {n_pts} points, "
                          f"{TRACK_DURATION_MIN}min horizon")
                elif track_ds is not None:
                    try:
                        track_ds.insert_observation_dict(track_obs)
                        stats["track_published"] += 1
                        print(f"           [TRACK] Published {n_pts}-point orbit track")
                    except Exception as e:
                        stats["errors"] += 1
                        print(f"           [ERR] Track publish failed: {e}")
                last_track_time = time.time()

            # ── Reconnect if too many errors ──────────────────────
            if consecutive_errors >= RECONNECT_THRESHOLD and not dry_run:
                print(f"  [WARN] {RECONNECT_THRESHOLD} consecutive errors, reconnecting...")
                try:
                    app, node, pos_ds, track_ds = connect_with_retry(
                        enable_track=enable_track)
                    stats["reconnects"] += 1
                    consecutive_errors = 0
                except Exception as re_err:
                    print(f"  [ERR] Reconnect failed: {re_err}")

            if once:
                break

            # Sleep until next tick (drift-compensated)
            next_tick = start_time + tick * interval
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C -- stopping publisher.")

    # Summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"  Summary ({elapsed:.0f}s elapsed)")
    print(f"  Position obs:   {stats['pos_published']}")
    print(f"  Track obs:      {stats['track_published']}")
    print(f"  Errors:         {stats['errors']}")
    print(f"  Reconnects:     {stats['reconnects']}")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Dual-product satellite publisher: position + orbit track (v3)")
    parser.add_argument("--interval", type=float, default=30.0,
                        help="Seconds between position observations (default: 30)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print observations but don't POST them")
    parser.add_argument("--once", action="store_true",
                        help="Publish a single observation then exit")
    parser.add_argument("--tle-refresh", type=float, default=3600.0,
                        help="Seconds between TLE refreshes (default: 3600)")
    parser.add_argument("--track-interval", type=float, default=300.0,
                        help="Seconds between orbit track publications (default: 300)")
    parser.add_argument("--no-track", action="store_true",
                        help="Disable orbit track publishing (position-only mode)")
    args = parser.parse_args()

    run(
        interval=args.interval,
        dry_run=args.dry_run,
        once=args.once,
        tle_refresh=args.tle_refresh,
        track_interval=args.track_interval,
        enable_track=not args.no_track,
    )


if __name__ == "__main__":
    main()
