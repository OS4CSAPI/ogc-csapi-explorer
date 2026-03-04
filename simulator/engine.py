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


# ═══════════════════════════════════════════════════════════════════════════
#  WLS Bearing Intersection Algorithm (Localizer)
# ═══════════════════════════════════════════════════════════════════════════

R_EARTH_WLS = 6_371_000
LAT_REF     = 31.655  # centroid of sensor network (°N)

# Localizer configuration
LOCALIZER_SYSTEM_UID  = "urn:os4csapi:system:fusion:az-string-alpha-localizer"
LOCALIZER_OUTPUT_NAME = "az_string_alpha_location_estimate"
LOB_OUTPUT_SUFFIX     = "_lob"
POLL_INTERVAL         = 5      # seconds
MAX_LOB_AGE_S         = 15     # staleness gate
CORRELATION_WINDOW    = 10     # max spread within a fusion group
RESIDUAL_CAP          = 500    # metres
MIN_LOBS              = 2


# System IDs for the 3 MA nodes (for LOB datastream discovery)
SYSTEM_IDS = {
    "AZ-MA-1": "0420",
    "AZ-MA-2": "0490",
    "AZ-MA-3": "049g",
}


def wls_bearing_intersection(lobs: list[dict]) -> dict | None:
    """
    Weighted least-squares bearing intersection.

    Each lob: {sensorLat, sensorLon, bearingTrue, bearingStdDev, ...}
    Returns: {estimatedLat, estimatedLon, cep50_m, residual_m, n} or None.
    """
    cos_ref = math.cos(math.radians(LAT_REF))

    sensors = []
    for lob in lobs:
        if not all(isinstance(lob.get(k), (int, float))
                   for k in ("sensorLon", "sensorLat", "bearingTrue", "bearingStdDev")):
            continue
        x = lob["sensorLon"] * (math.pi / 180) * R_EARTH_WLS * cos_ref
        y = lob["sensorLat"] * (math.pi / 180) * R_EARTH_WLS
        theta = math.radians(lob["bearingTrue"])
        sigma = max(lob["bearingStdDev"], 0.5)
        w = 1.0 / (math.radians(sigma) ** 2)
        sensors.append((x, y, theta, w))

    if len(sensors) < 2:
        return None

    ata = [[0.0, 0.0], [0.0, 0.0]]
    atb = [0.0, 0.0]

    for x_i, y_i, theta_i, w_i in sensors:
        a0 = math.cos(theta_i)
        a1 = -math.sin(theta_i)
        b_i = a0 * x_i + a1 * y_i
        ata[0][0] += w_i * a0 * a0
        ata[0][1] += w_i * a0 * a1
        ata[1][0] += w_i * a1 * a0
        ata[1][1] += w_i * a1 * a1
        atb[0]    += w_i * a0 * b_i
        atb[1]    += w_i * a1 * b_i

    det = ata[0][0] * ata[1][1] - ata[0][1] * ata[1][0]
    if abs(det) < 1e-12:
        return None

    x_hat = (ata[1][1] * atb[0] - ata[0][1] * atb[1]) / det
    y_hat = (ata[0][0] * atb[1] - ata[1][0] * atb[0]) / det

    residuals = []
    for x_i, y_i, theta_i, _w in sensors:
        d = abs(math.cos(theta_i) * (x_hat - x_i) - math.sin(theta_i) * (y_hat - y_i))
        residuals.append(d)

    mean_residual = sum(residuals) / len(residuals)
    cep50 = mean_residual * 1.2

    est_lon = x_hat / (math.pi / 180 * R_EARTH_WLS * cos_ref)
    est_lat = y_hat / (math.pi / 180 * R_EARTH_WLS)

    return {
        "estimatedLat": round(est_lat, 6),
        "estimatedLon": round(est_lon, 6),
        "cep50_m": round(cep50, 1),
        "residual_m": round(mean_residual, 1),
        "n": len(lobs),
    }


def build_location_estimate(
    wls_result: dict,
    contributing_sensors: list[str],
    track_id: int = 1,
    classification: str = "UAS",
) -> dict:
    """Build a CSAPI observation for the location estimate datastream."""
    now = iso_now()
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": {
            "timestamp": epoch_seconds(),
            "trackId": track_id,
            "estimatedLat": wls_result["estimatedLat"],
            "estimatedLon": wls_result["estimatedLon"],
            "cep50_m": wls_result["cep50_m"],
            "classification": classification,
            "numContributingLobs": wls_result["n"],
            "contributingSensors": ",".join(contributing_sensors),
            "residual_m": wls_result["residual_m"],
        },
    }


def discover_lob_datastreams() -> dict[str, str]:
    """
    Query the server for each MA system's LOB datastream ID.
    Returns {node_name: ds_id}.
    """
    lob_ds = {}
    for name, sys_id in SYSTEM_IDS.items():
        result = api_get(f"systems/{sys_id}/datastreams")
        if not result or "items" not in result:
            raise RuntimeError(f"System {name} ({sys_id}): no datastreams found")

        suffix = name.lower().replace("-", "_")
        expected_output = f"{suffix}_lob"

        match = None
        for ds in result["items"]:
            if ds.get("outputName") == expected_output:
                match = ds
                break
            if not match and ds.get("outputName", "").endswith(LOB_OUTPUT_SUFFIX):
                match = ds

        if not match:
            raise RuntimeError(f"System {name} ({sys_id}): no LOB datastream")
        lob_ds[name] = match["id"]

    return lob_ds


def discover_localizer_ds() -> str:
    """Find the localizer's output datastream ID."""
    result = api_get(f"systems?uid={LOCALIZER_SYSTEM_UID}")
    sys_id = None
    if result and "items" in result:
        for item in result["items"]:
            props = item.get("properties", item)
            if props.get("uid") == LOCALIZER_SYSTEM_UID:
                sys_id = item.get("id", props.get("id"))
                break
    if not sys_id:
        raise RuntimeError("Localizer system not found. Run bootstrap_localizer.py first.")

    ds_result = api_get(f"systems/{sys_id}/datastreams")
    if ds_result and "items" in ds_result:
        for ds in ds_result["items"]:
            if ds.get("outputName") == LOCALIZER_OUTPUT_NAME:
                return ds["id"]

    raise RuntimeError("Localizer datastream not found. Run bootstrap_localizer.py first.")
