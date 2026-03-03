#!/usr/bin/env python3
"""
simulate_scenario.py — Standalone data simulator for the OS4CSAPI demo.

Publishes observations every INTERVAL seconds to the live Oracle server,
simulating a UAV flying through the sensor network's detection ranges.

Each tick generates:
  • 1 LOB observation per detecting AZ-MA node (bearing from sensor to UAV)

The webapp's Live Mode (5-second polling) will pick up each new observation
and render it as bearing lines / observation points on the map.

Usage:
    python simulate_scenario.py                     # 1-hour flight, 5s ticks
    python simulate_scenario.py --duration 300      # 5-minute flight
    python simulate_scenario.py --interval 2        # 2s ticks
    python simulate_scenario.py --dry-run           # print, don't POST
    python simulate_scenario.py --speed 15          # UAV ground speed km/h

Requires: Python 3.10+ (stdlib only — no pip packages).
"""

import argparse
import base64
import json
import math
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ═══════════════════════════════════════════════════════════════════════════
#  Server configuration (matches bootstrap_v4.py)
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ═══════════════════════════════════════════════════════════════════════════
#  Sensor network geometry (live server positions from bootstrap_v4.py)
# ═══════════════════════════════════════════════════════════════════════════

NODES = [
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1",
        "lat": 31.6490196,
        "lon": -110.2758537,
        "detection_max_m": 3000,
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-2",
        "name": "AZ-MA-2",
        "lat": 31.6569236,
        "lon": -110.2659979,
        "detection_max_m": 3000,
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-3",
        "name": "AZ-MA-3",
        "lat": 31.6637961,
        "lon": -110.2515496,
        "detection_max_m": 3000,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  UAV trajectory — follows a river/wash channel from SW to NE, passing
#  NORTH of all three sensor nodes through their overlapping 3 km detection
#  envelopes.  Waypoints are interpolated at each tick.
#
#  Detection narrative (~2 km north of sensor line):
#    1. SW approach      — outside all envelopes
#    2. Enter MA-1       → brief single-node detection
#    3. Enter MA-2       → dual triangulation  (MA-1 + MA-2)
#    4. Enter MA-3       → TRIPLE detection    (climax)
#    5. Exit  MA-1       → dual  (MA-2 + MA-3)
#    6. Exit  MA-2       → single (MA-3 only)
#    7. Exit  MA-3       → NE departure, outside all
#
#  Total path ≈ 10.8 km.  At --speed 12 use --duration 3600.
# ═══════════════════════════════════════════════════════════════════════════

# Waypoints: (lon, lat) — UAV flies SW → NE along a wash/drainage channel
# Route runs ~1 km north of the sensor line to ensure all 3 nodes detect.
# Sensor positions: MA-1 (31.649, -110.276), MA-2 (31.657, -110.266), MA-3 (31.664, -110.252)
UAV_WAYPOINTS = [
    # ── Phase 1 — SW approach, outside all detection envelopes ────
    (-110.310, 31.658),    # start: far SW
    (-110.298, 31.659),    # heading NE along drainage

    # ── Phase 2 — Enter MA-1 detection (~2.5 km from node) ────────
    (-110.285, 31.660),    # inside MA-1 envelope
    (-110.276, 31.661),    # passing north of MA-1

    # ── Phase 3 — Dual detection (MA-1 + MA-2) ───────────────────
    (-110.270, 31.663),    # dual overlap zone
    (-110.264, 31.665),    # between MA-1 and MA-2

    # ── Phase 4 — Triple detection: all three nodes ───────────────
    (-110.258, 31.668),    # approaching MA-3, still in MA-1+MA-2
    (-110.252, 31.670),    # peak: closest to MA-3, triple zone
    (-110.246, 31.671),    # still triple

    # ── Phase 5 — Exit MA-1, dual (MA-2 + MA-3) ──────────────────
    (-110.240, 31.672),    # leaving MA-1
    (-110.234, 31.673),    # MA-2 + MA-3 only

    # ── Phase 6 — Exit MA-2, single MA-3, then clear ─────────────
    (-110.226, 31.675),    # MA-3 only
    (-110.218, 31.678),    # exiting MA-3
    (-110.208, 31.682),    # clear of all detection
]

# ═══════════════════════════════════════════════════════════════════════════
#  Geo math helpers
# ═══════════════════════════════════════════════════════════════════════════

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two WGS-84 points."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return bearing in degrees (0=N, 90=E) from point 1 to point 2."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def total_path_length_m(waypoints: list[tuple[float, float]]) -> float:
    """Sum of segment lengths in metres."""
    total = 0.0
    for i in range(len(waypoints) - 1):
        total += haversine_m(waypoints[i][1], waypoints[i][0],
                             waypoints[i + 1][1], waypoints[i + 1][0])
    return total


def interpolate_position(waypoints: list[tuple[float, float]], fraction: float) -> tuple[float, float]:
    """
    Return (lon, lat) at the given fraction [0..1] along the polyline.
    """
    if fraction <= 0:
        return waypoints[0]
    if fraction >= 1:
        return waypoints[-1]

    total = total_path_length_m(waypoints)
    target = fraction * total
    accum = 0.0

    for i in range(len(waypoints) - 1):
        seg = haversine_m(waypoints[i][1], waypoints[i][0],
                          waypoints[i + 1][1], waypoints[i + 1][0])
        if accum + seg >= target:
            t = (target - accum) / seg if seg > 0 else 0
            lon = waypoints[i][0] + t * (waypoints[i + 1][0] - waypoints[i][0])
            lat = waypoints[i][1] + t * (waypoints[i + 1][1] - waypoints[i][1])
            return (lon, lat)
        accum += seg

    return waypoints[-1]


# ═══════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ═══════════════════════════════════════════════════════════════════════════

_AUTH_HEADER = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()


def api_get(path: str) -> dict | None:
    """GET from the SensorHub API. Returns parsed JSON or None on 404."""
    url = f"{BASE_URL}/{path}"
    req = Request(url, headers={
        "Authorization": _AUTH_HEADER,
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def api_post(path: str, body: dict, content_type: str = "application/om+json") -> dict | str | None:
    """POST to the SensorHub API. Returns parsed JSON or location header."""
    url = f"{BASE_URL}/{path}"
    data = json.dumps(body).encode()
    req = Request(url, data=data, method="POST", headers={
        "Authorization": _AUTH_HEADER,
        "Content-Type": content_type,
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
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
        raise RuntimeError(f"HTTP {e.code} POST {url}: {body_text[:300]}")


# ═══════════════════════════════════════════════════════════════════════════
#  Datastream discovery — find IDs by system UID + outputName
# ═══════════════════════════════════════════════════════════════════════════

def find_system_id(uid: str) -> str | None:
    """Look up the server-side numeric ID for a system UID."""
    result = api_get(f"systems?uid={uid}")
    if result and "items" in result:
        for item in result["items"]:
            props = item.get("properties", item)
            if props.get("uid") == uid:
                return item.get("id", props.get("id"))
    return None


def find_datastream_id(system_id: str, output_name: str) -> str | None:
    """Find a datastream ID on a system by its outputName."""
    result = api_get(f"systems/{system_id}/datastreams")
    if result and "items" in result:
        for ds in result["items"]:
            if ds.get("outputName") == output_name or ds.get("name", "").lower().startswith(output_name.replace("_", " ").split()[0]):
                # Prefer exact outputName match
                if ds.get("outputName") == output_name:
                    return ds.get("id")
        # Fallback: name-based match
        for ds in result["items"]:
            if output_name.replace("_", " ").lower() in ds.get("name", "").lower():
                return ds.get("id")
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  Observation builders
# ═══════════════════════════════════════════════════════════════════════════

def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def epoch_seconds() -> float:
    return time.time()


def build_lob_observation(
    node: dict,
    uav_lat: float, uav_lon: float,
    track_id: int = 1,
) -> dict:
    """
    Build an LOB observation for one sensor node detecting the UAV.
    Schema: AZ-MA-N LOB datastream (v2.3 flat format).
    """
    azimuth = bearing_deg(node["lat"], node["lon"], uav_lat, uav_lon)
    dist = haversine_m(node["lat"], node["lon"], uav_lat, uav_lon)
    # Add small random noise to bearing (±2°) for realism
    import random
    noise = random.gauss(0, 1.0)
    azimuth_noisy = (azimuth + noise) % 360

    # Bearing std dev — higher when target is farther
    std_dev = 1.0 + (dist / node["detection_max_m"]) * 3.0

    now = iso_now()
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": {
            "timestamp": epoch_seconds(),
            "trackId": track_id,
            "bearingTrue": round(azimuth_noisy, 2),
            "bearingStdDev": round(std_dev, 2),
            "sensorLat": node["lat"],
            "sensorLon": node["lon"],
        },
    }


def build_track_update_observation(
    node: dict,
    uav_lat: float, uav_lon: float,
    track_id: int = 1,
    frame_idx: int = 0,
) -> dict:
    """
    Build a Track Update observation for one sensor node.
    Schema: AZ-MA-N Track Updates (v2.3 flat format).
    """
    import random
    azimuth = bearing_deg(node["lat"], node["lon"], uav_lat, uav_lon)
    elevation_deg = 5.0 + random.gauss(0, 1.0)  # UAV is slightly above horizon
    azimuth_noisy = (azimuth + random.gauss(0, 1.5)) % 360

    # Direction cosines from azimuth + elevation
    az_rad = math.radians(azimuth_noisy)
    el_rad = math.radians(elevation_deg)
    x = math.sin(az_rad) * math.cos(el_rad)
    y = math.cos(az_rad) * math.cos(el_rad)
    z = math.sin(el_rad)

    dist = haversine_m(node["lat"], node["lon"], uav_lat, uav_lon)
    activity = max(0.1, 1.0 - (dist / node["detection_max_m"]))
    confidence = max(0.3, 1.0 - (dist / node["detection_max_m"]) * 0.7 + random.gauss(0, 0.05))
    confidence = min(confidence, 1.0)

    now = iso_now()
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": {
            "timestamp": epoch_seconds(),
            "odasTimeStamp": frame_idx,
            "id": track_id,
            "tag": "dynamic",
            "x": round(x, 4),
            "y": round(y, 4),
            "z": round(z, 4),
            "activity": round(activity, 3),
            "bearingTrue": round(azimuth_noisy, 2),
            "elevation": round(elevation_deg, 2),
            "bearingStdDev": round(1.5, 2),
            "classLabel": "uas",
            "classConfidence": round(confidence, 3),
        },
    }


def build_scene_summary_observation(
    track_count: int,
    activity_level: float,
    frame_idx: int = 0,
) -> dict:
    """Build a Scene Summary observation."""
    now = iso_now()
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": {
            "timestamp": epoch_seconds(),
            "odasTimeStamp": frame_idx,
            "trackCount": track_count,
            "activityLevel": round(activity_level, 3),
        },
    }


def build_classification_observation(
    dist_m: float,
    track_id: int = 1,
) -> dict:
    """
    Build a Classification Probabilities observation.
    UAS probability is highest when close; degrades with distance.
    """
    import random
    max_r = 900
    closeness = max(0, 1.0 - dist_m / max_r)
    p_uas = min(1.0, closeness * 0.85 + random.gauss(0, 0.05))
    p_uas = max(0.05, p_uas)
    remaining = 1.0 - p_uas
    p_vehicle   = remaining * 0.3
    p_footsteps = remaining * 0.1
    p_impulsive = remaining * 0.05
    p_unknown   = remaining * 0.55

    now = iso_now()
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": {
            "timestamp": epoch_seconds(),
            "trackId": track_id,
            "p_uas": round(p_uas, 4),
            "p_vehicle": round(p_vehicle, 4),
            "p_footsteps": round(p_footsteps, 4),
            "p_impulsive": round(p_impulsive, 4),
            "p_unknown": round(p_unknown, 4),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Main simulation loop
# ═══════════════════════════════════════════════════════════════════════════

def run_simulation(duration_s: int, interval_s: float, uav_speed_kmh: float, dry_run: bool, start_offset_s: float = 0.0):
    """
    Discover datastream IDs, then run the simulation loop.
    """
    print("=" * 70)
    print("  OS4CSAPI Data Simulator — UAV Flythrough Scenario")
    print("=" * 70)
    print(f"  Server:     {BASE_URL}")
    print(f"  Duration:   {duration_s}s ({duration_s / 60:.0f} min)")
    print(f"  Interval:   {interval_s}s")
    print(f"  UAV speed:  {uav_speed_kmh} km/h")
    print(f"  Dry run:    {dry_run}")
    print()

    # ── Discover datastream IDs ──────────────────────────────────────
    print("Discovering datastream IDs...")
    node_ds: dict[str, str] = {}  # node_uid → lob_datastream_id

    for node in NODES:
        sys_id = find_system_id(node["uid"])
        if not sys_id:
            print(f"  ERROR: System {node['uid']} not found on server!")
            sys.exit(1)
        print(f"  {node['name']}: system_id={sys_id}")

        # Only discover the LOB datastream — 1 per sensor
        suffix = node["name"].lower().replace("-", "_")  # e.g., "az_ma_1"
        lob_name = f"{suffix}_lob"
        ds_id = find_datastream_id(sys_id, lob_name)
        if ds_id:
            node_ds[node["uid"]] = ds_id
            print(f"    {lob_name} → {ds_id}")
        else:
            print(f"    {lob_name} → NOT FOUND")
            sys.exit(1)

    # ── Compute path metrics ─────────────────────────────────────────
    path_len = total_path_length_m(UAV_WAYPOINTS)
    uav_speed_ms = uav_speed_kmh * 1000 / 3600
    flight_time = path_len / uav_speed_ms
    total_ticks = int(duration_s / interval_s)

    print()
    print(f"  Path length: {path_len:.0f} m")
    print(f"  UAV speed:   {uav_speed_ms:.1f} m/s")
    print(f"  Flight time: {flight_time:.0f}s ({flight_time / 60:.1f} min)")
    print(f"  Total ticks: {total_ticks}")

    # If flight_time < duration, the UAV will loop; if duration < flight_time,
    # it won't complete the path.  We use modular fraction for looping.
    print()
    if flight_time < duration_s:
        loops = duration_s / flight_time
        print(f"  UAV will complete ~{loops:.1f} passes over the network.")
    else:
        coverage = duration_s / flight_time * 100
        print(f"  UAV will cover ~{coverage:.0f}% of the path in this run.")

    print()
    print("-" * 70)
    print("  SIMULATION RUNNING — press Ctrl+C to stop")
    print("-" * 70)
    print()

    if start_offset_s > 0:
        print(f"  Start offset: {start_offset_s:.0f}s ({start_offset_s / 60:.1f} min into route)")

    stats = {"published": 0, "errors": 0, "detecting_ticks": 0}
    start_time = time.time()
    tick = 0

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration_s:
                break

            # ── Compute UAV position ────────────────────────────────────────
            # Distance travelled so far (add offset to skip approach phase)
            dist_travelled = (elapsed + start_offset_s) * uav_speed_ms
            # Fraction along path (modular for looping)
            fraction = (dist_travelled % path_len) / path_len
            uav_lon, uav_lat = interpolate_position(UAV_WAYPOINTS, fraction)

            # ── Determine which nodes detect the UAV ──────────────────
            detecting_nodes = []
            for node in NODES:
                dist = haversine_m(node["lat"], node["lon"], uav_lat, uav_lon)
                if dist <= node["detection_max_m"]:
                    detecting_nodes.append((node, dist))

            tick += 1
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

            if detecting_nodes:
                stats["detecting_ticks"] += 1
                node_names = ", ".join(n["name"] for n, _ in detecting_nodes)
                print(f"  [{ts}] tick {tick:4d} | UAV at ({uav_lat:.6f}, {uav_lon:.6f}) | "
                      f"Detected by: {node_names}")

                for node, dist in detecting_nodes:
                    ds_id = node_ds.get(node["uid"])
                    if not ds_id:
                        continue

                    obs = build_lob_observation(node, uav_lat, uav_lon, track_id=1)
                    if dry_run:
                        print(f"        [DRY] LOB → ds {ds_id}: "
                              f"bearing={obs['result']['bearingTrue']}°")
                    else:
                        try:
                            api_post(f"datastreams/{ds_id}/observations", obs)
                            stats["published"] += 1
                        except Exception as e:
                            print(f"        ERROR LOB: {e}")
                            stats["errors"] += 1
            else:
                print(f"  [{ts}] tick {tick:4d} | UAV at ({uav_lat:.6f}, {uav_lon:.6f}) | "
                      f"(no detection)")

            # ── Wait for next tick ────────────────────────────────────
            next_tick = start_time + tick * interval_s
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C — stopping simulation.")

    # ── Summary ───────────────────────────────────────────────────────
    elapsed_total = time.time() - start_time
    print()
    print("=" * 70)
    print("  SIMULATION COMPLETE")
    print("=" * 70)
    print(f"  Elapsed:          {elapsed_total:.1f}s ({elapsed_total / 60:.1f} min)")
    print(f"  Ticks:            {tick}")
    print(f"  Detection ticks:  {stats['detecting_ticks']} / {tick} "
          f"({stats['detecting_ticks'] / max(tick, 1) * 100:.0f}%)")
    print(f"  Published:        {stats['published']} observations")
    print(f"  Errors:           {stats['errors']}")
    print()


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="OS4CSAPI Data Simulator — UAV flythrough scenario")
    parser.add_argument("--duration", type=int, default=3600,
                        help="Simulation duration in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Seconds between observation ticks (default: 5)")
    parser.add_argument("--speed", type=float, default=12.0,
                        help="UAV ground speed in km/h (default: 12)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print observations instead of POSTing them")
    parser.add_argument("--start-offset", type=float, default=0.0,
                        help="Skip N seconds into route (skip approach phase, e.g., 800)")
    args = parser.parse_args()

    run_simulation(
        duration_s=args.duration,
        interval_s=args.interval,
        uav_speed_kmh=args.speed,
        dry_run=args.dry_run,
        start_offset_s=args.start_offset,
    )


if __name__ == "__main__":
    main()
