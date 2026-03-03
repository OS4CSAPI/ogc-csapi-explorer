"""
engine.py — Core simulation logic for the OS4CSAPI UAV flythrough.

Extracted from scripts/simulate_scenario.py so it can be imported by:
  • simulator/main.py  (FastAPI service)
  • scripts/simulate_scenario.py  (CLI tool)

No dependencies beyond the Python stdlib.
"""

import base64
import json
import math
import random
import ssl
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ═══════════════════════════════════════════════════════════════════════════
#  Server configuration
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ═══════════════════════════════════════════════════════════════════════════
#  Sensor network geometry
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
#  UAV trajectory — 14 waypoints SW → NE along a wash channel
# ═══════════════════════════════════════════════════════════════════════════

UAV_WAYPOINTS = [
    # Phase 1 — SW approach, outside all detection envelopes
    (-110.310, 31.658),
    (-110.298, 31.659),
    # Phase 2 — Enter MA-1 detection
    (-110.285, 31.660),
    (-110.276, 31.661),
    # Phase 3 — Dual detection (MA-1 + MA-2)
    (-110.270, 31.663),
    (-110.264, 31.665),
    # Phase 4 — Triple detection: all three nodes
    (-110.258, 31.668),
    (-110.252, 31.670),
    (-110.246, 31.671),
    # Phase 5 — Exit MA-1, dual (MA-2 + MA-3)
    (-110.240, 31.672),
    (-110.234, 31.673),
    # Phase 6 — Exit MA-2, single MA-3, then clear
    (-110.226, 31.675),
    (-110.218, 31.678),
    (-110.208, 31.682),
]

# ═══════════════════════════════════════════════════════════════════════════
#  Geo math helpers
# ═══════════════════════════════════════════════════════════════════════════

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in metres between two WGS-84 points."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Bearing in degrees (0=N, 90=E) from point 1 to point 2."""
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
    """Return (lon, lat) at the given fraction [0..1] along the polyline."""
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
#  HTTP helpers (with retry for transient DNS / network failures)
# ═══════════════════════════════════════════════════════════════════════════

_AUTH_HEADER = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()
_MAX_RETRIES = 5
_RETRY_DELAY = 3


def _with_retry(fn, label="request"):
    """Execute *fn* with retries on transient network errors."""
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except HTTPError:
            raise
        except (URLError, OSError, ConnectionError, TimeoutError) as e:
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_DELAY * (attempt + 1)
                print(f"  ↻ Retry {label} in {wait}s ({type(e).__name__})")
                time.sleep(wait)
            else:
                raise


def api_get(path: str) -> dict | None:
    """GET from the SensorHub API. Returns parsed JSON or None on 404."""
    def fn():
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
    return _with_retry(fn, f"GET {path}")


def api_post(path: str, body: dict, content_type: str = "application/om+json") -> dict | str | None:
    """POST to the SensorHub API. Returns parsed JSON or location header."""
    def fn():
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
    return _with_retry(fn, f"POST {path}")


# ═══════════════════════════════════════════════════════════════════════════
#  Datastream discovery
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
            if ds.get("outputName") == output_name or ds.get("name", "").lower().startswith(
                output_name.replace("_", " ").split()[0]
            ):
                if ds.get("outputName") == output_name:
                    return ds.get("id")
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
    uav_lat: float,
    uav_lon: float,
    track_id: int = 1,
) -> dict:
    """Build an LOB observation for one sensor node detecting the UAV."""
    azimuth = bearing_deg(node["lat"], node["lon"], uav_lat, uav_lon)
    dist = haversine_m(node["lat"], node["lon"], uav_lat, uav_lon)
    noise = random.gauss(0, 1.0)
    azimuth_noisy = (azimuth + noise) % 360
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
            "classification": "UAS",
        },
    }
