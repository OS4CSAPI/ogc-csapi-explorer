#!/usr/bin/env python3
"""
iss_publisher.py — Live satellite position publisher for CSAPI/OSH servers.

Uses OSHConnect-Python for CSAPI transport, SGP4 for orbital propagation.
Fetches NORAD GP element sets from CelesTrak, propagates with SGP4,
and publishes geodetic positions (lat, lon, alt) as CSAPI observations.

Configure via environment variables:
    OSH_ADDRESS      Server hostname          (default: os4csapi-osh.duckdns.org)
    OSH_PORT         Server port              (default: 443)
    OSH_USER         Auth username            (default: os4csapi)
    OSH_PASS         Auth password            (default: ogc134mm)
    OSH_ROOT         SensorHub root path      (default: sensorhub)
    SYSTEM_UID       System URN to discover   (default: urn:os4csapi:system:iss-tracker:v1)
    DATASTREAM_NAME  Datastream name to match (default: ISS Position (SGP4))
    NORAD_ID         NORAD catalog number     (default: 25544)

Usage:
    python iss_publisher.py                    # run forever (30s cadence)
    python iss_publisher.py --dry-run          # print, don't POST
    python iss_publisher.py --interval 10      # 10s cadence
    python iss_publisher.py --once             # single observation then exit
    python iss_publisher.py --tle-refresh 7200 # refresh TLE every 2h (default 1h)

Requires: Python 3.12+, sgp4, oshconnect
"""

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen  # retained for CelesTrak only

try:
    from sgp4.api import Satrec, WGS72
except ImportError:
    print("ERROR: sgp4 package not found. Install it with: pip install sgp4")
    sys.exit(1)

try:
    from oshconnect import OSHConnect, Node, Datastream
except ImportError:
    print("ERROR: oshconnect package not found. Install it with:")
    print("  pip install git+https://github.com/OS4CSAPI/OSHConnect-Python.git")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
#  Configuration (env vars with sensible defaults)
# ═══════════════════════════════════════════════════════════════════════════

OSH_ADDRESS     = os.environ.get("OSH_ADDRESS", "os4csapi-osh.duckdns.org")
OSH_PORT        = int(os.environ.get("OSH_PORT", "443"))
OSH_USER        = os.environ.get("OSH_USER", "os4csapi")
OSH_PASS        = os.environ.get("OSH_PASS", "ogc134mm")
OSH_ROOT        = os.environ.get("OSH_ROOT", "sensorhub")
SYSTEM_UID      = os.environ.get("SYSTEM_UID", "urn:os4csapi:system:iss-tracker:v1")
DATASTREAM_NAME = os.environ.get("DATASTREAM_NAME", "ISS Position (SGP4)")
NORAD_ID        = os.environ.get("NORAD_ID", "25544")

CELESTRAK_URL = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={NORAD_ID}&FORMAT=JSON"

# Reconnect threshold: after this many consecutive publish errors,
# tear down and re-discover the server connection.
RECONNECT_THRESHOLD = 5


# ═══════════════════════════════════════════════════════════════════════════
#  OSHConnect server connection (with retry / backoff)
# ═══════════════════════════════════════════════════════════════════════════

def connect_and_discover() -> tuple[OSHConnect, Node, Datastream]:
    """Connect to OSH server and discover system + datastream by stable identifiers."""
    app = OSHConnect("satellite-publisher")
    node = Node(
        protocol="https",
        address=OSH_ADDRESS,
        port=OSH_PORT,
        username=OSH_USER,
        password=OSH_PASS,
        server_root=OSH_ROOT,
    )
    app.add_node(node)

    # Workaround: OSHConnect-Python bug — StreamableResource.__init__ accesses
    # node._mqtt_client unconditionally, but it's only set when enable_mqtt=True.
    # We don't need MQTT for HTTP-only publishing, so stub it out.
    if not hasattr(node, '_mqtt_client'):
        node._mqtt_client = None

    # Discover systems and find ours by URN
    # NOTE: OSHConnect-Python bug — find_system() checks system.uid but the
    # attribute is actually system.urn.  Work around by iterating directly.
    app.discover_systems()

    # Workaround #2: Node.discover_systems() constructs System objects without
    # passing resource_id, so System._resource_id is never set.  This causes
    # discover_datastreams() to fail with AttributeError.  Fix by re-reading
    # the systems list and patching the server-side ID onto each System.
    from oshconnect.csapi4py.constants import APIResourceTypes
    raw_res = node.get_api_helper().retrieve_resource(APIResourceTypes.SYSTEM, req_headers={})
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

    system = None
    for s in app._systems:
        if s.urn == SYSTEM_UID:
            system = s
            break
    if system is None:
        available = [s.urn for s in app._systems]
        raise RuntimeError(
            f"System '{SYSTEM_UID}' not found on server. Available: {available}"
        )

    # Discover datastreams for our system only.
    # Workaround #3: OSHConnect.discover_datastreams() passes 'id=...' to
    # Datastream() but the constructor doesn't accept it → TypeError.
    # Instead, call system.discover_datastreams() directly (returns raw
    # DatastreamResource models) and construct Datastream wrappers ourselves.
    ds_resources = system.discover_datastreams()
    ds = None
    for res in ds_resources:
        if res.name == DATASTREAM_NAME:
            ds = Datastream(parent_node=node, datastream_resource=res)
            break

    if ds is None:
        available = [r.name for r in ds_resources]
        raise RuntimeError(
            f"Datastream '{DATASTREAM_NAME}' not found for system '{SYSTEM_UID}'. "
            f"Available: {available}"
        )

    print(f"  Connected: system={system.urn}, datastream={ds._underlying_resource.name} "
          f"(id={ds.get_id()})")
    return app, node, ds


def connect_with_retry(
    max_attempts: int = 10,
    base_delay: float = 5.0,
    max_delay: float = 120.0,
) -> tuple[OSHConnect, Node, Datastream]:
    """Connect to OSH server with exponential backoff + jitter."""
    for attempt in range(1, max_attempts + 1):
        try:
            return connect_and_discover()
        except Exception as e:
            if attempt == max_attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = delay * 0.2 * (random.random() - 0.5)  # +/-10%
            wait = delay + jitter
            print(f"  [WARN] Connection attempt {attempt}/{max_attempts} failed: {e}")
            print(f"         Retrying in {wait:.1f}s...")
            time.sleep(wait)
    # unreachable, but keeps type checker happy
    raise RuntimeError("connect_with_retry: exhausted all attempts")


# ═══════════════════════════════════════════════════════════════════════════
#  CelesTrak TLE / OMM fetch (unchanged — not a CSAPI operation)
# ═══════════════════════════════════════════════════════════════════════════

_cached_satrec: Satrec | None = None
_tle_fetched_at: float = 0.0
_tle_epoch_str: str = ""


def fetch_tle_from_celestrak() -> Satrec:
    """Fetch the latest GP elements from CelesTrak (OMM JSON format)."""
    global _cached_satrec, _tle_fetched_at, _tle_epoch_str

    req = Request(CELESTRAK_URL, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if isinstance(data, list) and len(data) > 0:
        omm = data[0]
    else:
        raise RuntimeError(f"Unexpected CelesTrak response: {str(data)[:200]}")

    sat = Satrec()
    sat.sgp4init(
        WGS72,                                                      # gravity model
        'i',                                                        # improved mode
        int(omm.get("NORAD_CAT_ID", NORAD_ID)),                    # satnum
        _epoch_to_jdsatepoch(omm["EPOCH"]),                         # epoch
        float(omm.get("BSTAR", 0.0)),                              # bstar drag
        float(omm.get("MEAN_MOTION_DOT", 0.0)) / (2.0 * math.pi / 1440.0**2),
        float(omm.get("MEAN_MOTION_DDOT", 0.0)),                   # nddot
        float(omm["ECCENTRICITY"]),                                 # ecco
        math.radians(float(omm["ARG_OF_PERICENTER"])),              # argpo
        math.radians(float(omm["INCLINATION"])),                    # inclo
        math.radians(float(omm["MEAN_ANOMALY"])),                   # mo
        float(omm["MEAN_MOTION"]) * 2.0 * math.pi / 1440.0,       # no_kozai
        math.radians(float(omm["RA_OF_ASC_NODE"])),                 # nodeo
    )

    _cached_satrec = sat
    _tle_fetched_at = time.time()
    _tle_epoch_str = omm.get("EPOCH", "unknown")
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
#  SGP4 propagation → geodetic (unchanged — orbital mechanics)
# ═══════════════════════════════════════════════════════════════════════════

def propagate_to_geodetic(sat: Satrec, dt: datetime) -> tuple[float, float, float]:
    """Propagate satellite to given datetime → (lat_deg, lon_deg, alt_km)."""
    jd, fr = _datetime_to_jd(dt)
    e, r, v = sat.sgp4(jd, fr)

    if e != 0:
        raise RuntimeError(f"SGP4 propagation error code {e}")

    x, y, z = r  # km, ECI (TEME)
    lat, lon, alt = eci_to_geodetic(x, y, z, dt)
    return lat, lon, alt


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
    # Earth parameters (WGS-72 to match sgp4)
    a_e = 6378.135       # equatorial radius, km
    f   = 1.0 / 298.26   # flattening

    gmst = _gmst_rad(dt)

    # ECI → ECEF rotation
    cos_g = math.cos(gmst)
    sin_g = math.sin(gmst)
    x_ecef = x_km * cos_g + y_km * sin_g
    y_ecef = -x_km * sin_g + y_km * cos_g
    z_ecef = z_km

    # ECEF → geodetic (iterative)
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
    alt = r_xy / math.cos(lat) - N if abs(math.cos(lat)) > 1e-10 else abs(z_ecef) - N * (1 - e2)

    return math.degrees(lat), math.degrees(lon), alt


def _gmst_rad(dt: datetime) -> float:
    """Compute Greenwich Mean Sidereal Time in radians for a given UTC datetime."""
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
#  Observation builder (unchanged)
# ═══════════════════════════════════════════════════════════════════════════

def build_observation(lat: float, lon: float, alt_km: float,
                      now: datetime) -> dict:
    """Build an observation dict matching the datastream schema."""
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
    print("  Satellite Position Publisher (OSHConnect-Python)")
    print("=" * 70)
    print(f"  Server:       https://{OSH_ADDRESS}:{OSH_PORT}/{OSH_ROOT}/api")
    print(f"  System UID:   {SYSTEM_UID}")
    print(f"  Datastream:   {DATASTREAM_NAME}")
    print(f"  NORAD ID:     {NORAD_ID}")
    print(f"  Interval:     {interval}s")
    print(f"  TLE refresh:  {tle_refresh}s")
    print(f"  Dry run:      {dry_run}")
    print()

    # ── Connect to OSH server ────────────────────────────────────
    if not dry_run:
        print("  Connecting to OSH server...")
        app, node, ds = connect_with_retry()
    else:
        app, node, ds = None, None, None

    # ── Fetch initial TLE ────────────────────────────────────────
    print("  Fetching TLE from CelesTrak...")
    try:
        sat = fetch_tle_from_celestrak()
        print(f"  TLE epoch: {_tle_epoch_str}")
    except Exception as e:
        print(f"  FATAL: Could not fetch TLE: {e}")
        sys.exit(1)

    stats = {"published": 0, "errors": 0, "reconnects": 0}
    tick = 0
    consecutive_errors = 0
    start_time = time.time()

    print()
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
            print(f"  [{ts}] #{tick:5d} | lat={lat:+9.4f} lon={lon:+10.4f} alt={alt_km:7.1f} km")

            # Build and publish observation
            obs = build_observation(lat, lon, alt_km, now)
            if dry_run:
                print(f"           [DRY] {json.dumps(obs['result'], separators=(',', ':'))}")
            else:
                try:
                    ds.insert_observation_dict(obs)
                    stats["published"] += 1
                    consecutive_errors = 0
                except Exception as e:
                    consecutive_errors += 1
                    stats["errors"] += 1
                    print(f"           [ERR] Publish failed ({consecutive_errors}x): {e}")

                    # Too many consecutive errors → reconnect
                    if consecutive_errors >= RECONNECT_THRESHOLD:
                        print(f"  [WARN] {RECONNECT_THRESHOLD} consecutive errors, reconnecting...")
                        try:
                            app, node, ds = connect_with_retry()
                            stats["reconnects"] += 1
                            consecutive_errors = 0
                        except Exception as re_err:
                            print(f"  [ERR] Reconnect failed: {re_err}")
                            # Will keep trying on next tick

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
    print(f"  Published:    {stats['published']} observations")
    print(f"  Errors:       {stats['errors']}")
    print(f"  Reconnects:   {stats['reconnects']}")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Satellite position publisher using OSHConnect-Python + SGP4")
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
