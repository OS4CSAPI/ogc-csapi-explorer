#!/usr/bin/env python3
"""
localizer.py — Standalone LOB triangulation consumer/producer.

Reads LOB observations from 3 MA nodes via CSAPI GET, computes UAS
position estimates via weighted least-squares bearing intersection,
and publishes results via CSAPI POST.

Three independent actors.  Zero direct coupling.  All communication
through CSAPI.  See: LOB_Localizer_Architecture_Correction.md

Usage:
    python localizer.py                  # run in foreground (Ctrl-C to stop)
    python localizer.py --once           # single poll cycle, then exit
    python localizer.py --dry-run        # poll + compute, but don't POST

Requires: Python 3.10+, no external dependencies (stdlib only).
"""

import argparse
import base64
import json
import math
import ssl as _ssl
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

# ── System IDs for the 3 MA nodes ────────────────────────────────────────
# These are the only hardcoded IDs.  Datastream IDs are discovered at
# startup by querying each system's datastreams for the matching outputName.
SYSTEM_IDS = {
    "AZ-MA-1": "0420",
    "AZ-MA-2": "0490",
    "AZ-MA-3": "049g",
}

# ── LOB discovery predicate ──────────────────────────────────────────────
# Each MA node's LOB datastream has outputName matching this pattern.
# The actual outputName is "{node_prefix}_lob" (e.g. "az_ma_1_lob").
LOB_OUTPUT_SUFFIX = "_lob"

# ── Localizer output ─────────────────────────────────────────────────────
LOCALIZER_SYSTEM_UID = "urn:os4csapi:system:fusion:az-string-alpha-localizer"
LOCALIZER_OUTPUT_NAME = "az_string_alpha_location_estimate"

# ── Timing ────────────────────────────────────────────────────────────────
POLL_INTERVAL      = 5     # seconds — matches simulator tick rate
MAX_LOB_AGE_S      = 15    # staleness gate vs wall-clock (3× poll interval)
CORRELATION_WINDOW = 10    # max timestamp spread within a fusion group (seconds)

# ── Quality gates ─────────────────────────────────────────────────────────
RESIDUAL_CAP = 500         # metres — reject wild intersections
MIN_LOBS     = 2           # need at least 2 bearings for a fix

# ── Constants ─────────────────────────────────────────────────────────────
R_EARTH = 6_371_000        # metres
LAT_REF = 31.655           # centroid of sensor network (°N)

# ═══════════════════════════════════════════════════════════════════════════
#  Networking
# ═══════════════════════════════════════════════════════════════════════════

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

_AUTH_HEADER = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()

_MAX_RETRIES = 5
_RETRY_DELAY = 3


def _with_retry(fn, label="request"):
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
    """GET from the SensorHub API.  Returns parsed JSON or None on 404."""
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


def api_post(path: str, body: dict,
             content_type: str = "application/om+json") -> dict | None:
    """POST to the SensorHub API.  Returns parsed JSON or location header."""
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
                    return {"id": location.rstrip("/").split("/")[-1]}
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
#  Phase 0: Dynamic Discovery
# ═══════════════════════════════════════════════════════════════════════════

def discover_lob_datastreams() -> dict[str, str]:
    """
    Query the server for each MA system's LOB datastream ID.
    Returns {node_name: ds_id}, e.g. {"AZ-MA-1": "04c0", ...}
    Raises RuntimeError if any system or LOB DS is missing.
    """
    lob_ds = {}
    for name, sys_id in SYSTEM_IDS.items():
        result = api_get(f"systems/{sys_id}/datastreams")
        if not result or "items" not in result:
            raise RuntimeError(f"System {name} ({sys_id}): no datastreams found")

        suffix = name.lower().replace("-", "_")  # "az_ma_1"
        expected_output = f"{suffix}_lob"          # "az_ma_1_lob"

        match = None
        for ds in result["items"]:
            if ds.get("outputName") == expected_output:
                match = ds
                break
            # Fallback: any outputName ending with _lob
            if not match and ds.get("outputName", "").endswith(LOB_OUTPUT_SUFFIX):
                match = ds

        if not match:
            raise RuntimeError(
                f"System {name} ({sys_id}): no LOB datastream found "
                f"(expected outputName={expected_output})"
            )
        lob_ds[name] = match["id"]
        print(f"  ✓ {name} LOB DS: {match['id']}  (outputName={match['outputName']})")

    return lob_ds


def discover_localizer_ds() -> str:
    """
    Find the localizer's output datastream by querying its system.
    Returns ds_id or raises.
    """
    # Find localizer system by UID
    result = api_get(f"systems?uid={LOCALIZER_SYSTEM_UID}")
    sys_id = None
    if result and "items" in result:
        for item in result["items"]:
            props = item.get("properties", item)
            if props.get("uid") == LOCALIZER_SYSTEM_UID:
                sys_id = item.get("id", props.get("id"))
                break

    if not sys_id:
        raise RuntimeError(
            f"Localizer system not found (uid={LOCALIZER_SYSTEM_UID}). "
            f"Run bootstrap_localizer.py first."
        )

    # Find output datastream
    ds_result = api_get(f"systems/{sys_id}/datastreams")
    if ds_result and "items" in ds_result:
        for ds in ds_result["items"]:
            if ds.get("outputName") == LOCALIZER_OUTPUT_NAME:
                print(f"  ✓ Localizer output DS: {ds['id']}  (system={sys_id})")
                return ds["id"]

    raise RuntimeError(
        f"Localizer datastream not found (outputName={LOCALIZER_OUTPUT_NAME}). "
        f"Run bootstrap_localizer.py first."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  WLS Bearing Intersection Algorithm
# ═══════════════════════════════════════════════════════════════════════════

def wls_bearing_intersection(lobs: list[dict]) -> dict | None:
    """
    Weighted least-squares bearing intersection.

    Each lob: {sensorLat, sensorLon, bearingTrue, bearingStdDev, ...}
    Returns: {estimatedLat, estimatedLon, cep50_m, residual_m, n} or None.

    Math: minimizes Σ w_i · d_i² where d_i is the perpendicular distance
    from the candidate point to bearing line i, and w_i = 1/σ_i².
    """
    cos_ref = math.cos(math.radians(LAT_REF))

    sensors = []
    for lob in lobs:
        # Skip LOBs missing required fields
        if not all(isinstance(lob.get(k), (int, float)) for k in ("sensorLon", "sensorLat", "bearingTrue", "bearingStdDev")):
            continue
        x = lob["sensorLon"] * (math.pi / 180) * R_EARTH * cos_ref
        y = lob["sensorLat"] * (math.pi / 180) * R_EARTH
        theta = math.radians(lob["bearingTrue"])
        sigma = max(lob["bearingStdDev"], 0.5)  # floor at 0.5°
        w = 1.0 / (math.radians(sigma) ** 2)
        sensors.append((x, y, theta, w))

    if len(sensors) < 2:
        return None  # not enough valid LOBs

    # Build normal equations:  A^T W A x = A^T W b
    ata = [[0.0, 0.0], [0.0, 0.0]]
    atb = [0.0, 0.0]

    for x_i, y_i, theta_i, w_i in sensors:
        # Normal to bearing direction (sin θ, cos θ) is (cos θ, -sin θ)
        a0 = math.cos(theta_i)
        a1 = -math.sin(theta_i)
        b_i = a0 * x_i + a1 * y_i

        ata[0][0] += w_i * a0 * a0
        ata[0][1] += w_i * a0 * a1
        ata[1][0] += w_i * a1 * a0
        ata[1][1] += w_i * a1 * a1
        atb[0]    += w_i * a0 * b_i
        atb[1]    += w_i * a1 * b_i

    # Solve 2×2 system
    det = ata[0][0] * ata[1][1] - ata[0][1] * ata[1][0]
    if abs(det) < 1e-12:
        return None  # near-parallel bearings — no solution

    x_hat = (ata[1][1] * atb[0] - ata[0][1] * atb[1]) / det
    y_hat = (ata[0][0] * atb[1] - ata[1][0] * atb[0]) / det

    # Residuals (metres)
    residuals = []
    for x_i, y_i, theta_i, _w in sensors:
        d = abs(math.cos(theta_i) * (x_hat - x_i) - math.sin(theta_i) * (y_hat - y_i))
        residuals.append(d)

    mean_residual = sum(residuals) / len(residuals)
    cep50 = mean_residual * 1.2  # simplified CEP50 ≈ 0.675 × DRMS ≈ 1.2 × mean residual

    # Convert back to WGS-84
    est_lon = x_hat / (math.pi / 180 * R_EARTH * cos_ref)
    est_lat = y_hat / (math.pi / 180 * R_EARTH)

    return {
        "estimatedLat": round(est_lat, 6),
        "estimatedLon": round(est_lon, 6),
        "cep50_m": round(cep50, 1),
        "residual_m": round(mean_residual, 1),
        "n": len(lobs),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Observation Builder
# ═══════════════════════════════════════════════════════════════════════════

def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def epoch_seconds() -> float:
    return round(time.time(), 3)


def build_location_estimate(
    wls_result: dict,
    contributing_sensors: list[str],
    contributing_lobs: list[dict] | None = None,
    track_id: int = 1,
    classification: str = "UAS",
) -> dict:
    """Build a CSAPI observation for the location estimate datastream.
    
    When contributing_lobs is provided, the LOB data used for this fix
    is embedded as a JSON-encoded array so consumers can render the exact
    bearing lines that produced the estimate — zero temporal mismatch.
    """
    now = iso_now()
    result = {
        "timestamp": epoch_seconds(),
        "trackId": track_id,
        "estimatedLat": wls_result["estimatedLat"],
        "estimatedLon": wls_result["estimatedLon"],
        "cep50_m": wls_result["cep50_m"],
        "classification": classification,
        "numContributingLobs": wls_result["n"],
        "contributingSensors": ",".join(contributing_sensors),
        "residual_m": wls_result["residual_m"],
    }
    if contributing_lobs is not None:
        result["contributingLobsJson"] = json.dumps([
            {
                "sensorName": lob.get("name", ""),
                "sensorLat": lob.get("sensorLat"),
                "sensorLon": lob.get("sensorLon"),
                "bearingTrue": lob.get("bearingTrue"),
                "bearingStdDev": lob.get("bearingStdDev"),
            }
            for lob in contributing_lobs
        ])
    return {
        "phenomenonTime": now,
        "resultTime": now,
        "result": result,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Main Loop
# ═══════════════════════════════════════════════════════════════════════════

def run_localizer(once: bool = False, dry_run: bool = False):
    print("\n── Phase 0: Discovery ──")
    lob_datastreams = discover_lob_datastreams()
    localizer_ds = discover_localizer_ds()
    print(f"\n  LOB inputs:  {lob_datastreams}")
    print(f"  Output DS:   {localizer_ds}")

    # Dedup state: {ds_id: last_seen_obs_id}
    last_seen: dict[str, str] = {}

    # Stats
    cycles = 0
    fixes_published = 0
    lobs_consumed = 0

    print(f"\n── Localizer running (poll={POLL_INTERVAL}s, staleness={MAX_LOB_AGE_S}s, "
          f"corr_window={CORRELATION_WINDOW}s) ──\n")

    try:
        while True:
            cycles += 1
            now = time.time()

            # ── 1. CONSUME: Read latest LOB from each MA node ────────────
            lobs = []
            for name, ds_id in lob_datastreams.items():
                try:
                    obs_resp = api_get(f"datastreams/{ds_id}/observations?resultTime=latest")
                except Exception as e:
                    print(f"  ⚠ {name}: GET failed ({type(e).__name__})")
                    continue

                if not obs_resp:
                    continue

                # Handle both single-object and items-array responses
                if "items" in obs_resp and obs_resp["items"]:
                    obs = obs_resp["items"][0]
                elif "result" in obs_resp:
                    obs = obs_resp
                else:
                    continue

                # DEDUP: skip if already processed this exact observation
                obs_id = obs.get("id", "")
                if obs_id and last_seen.get(ds_id) == obs_id:
                    continue  # already processed
                if obs_id:
                    last_seen[ds_id] = obs_id

                result = obs.get("result")
                if not result:
                    continue

                obs_time = result.get("timestamp", 0)

                # STALENESS GATE: reject old observations
                if abs(now - obs_time) > MAX_LOB_AGE_S:
                    continue  # stale — skip

                lobs.append({
                    **result,
                    "name": name,
                    "obs_id": obs_id,
                })
                lobs_consumed += 1

            if not lobs:
                if cycles <= 3 or cycles % 12 == 0:  # don't spam
                    print(f"  [{cycles}] No fresh LOBs (0 passed staleness gate)")
                if once:
                    break
                time.sleep(POLL_INTERVAL)
                continue

            # ── 2. CORRELATE: Group by classification ─────────────────────
            by_class: dict[str, list[dict]] = {}
            for lob in lobs:
                cls = lob.get("classification", "UNKNOWN")
                by_class.setdefault(cls, []).append(lob)

            for cls, group in by_class.items():
                # CORRELATION WINDOW: ensure LOBs are temporally close to each other
                timestamps = [l["timestamp"] for l in group]
                spread = max(timestamps) - min(timestamps)
                if spread > CORRELATION_WINDOW:
                    print(f"  [{cycles}] {cls}: {len(group)} LOBs but spread={spread:.1f}s > {CORRELATION_WINDOW}s — skip")
                    continue

                # MINIMUM LOBs: need 2+ for a fix
                if len(group) < MIN_LOBS:
                    print(f"  [{cycles}] {cls}: only {len(group)} LOB — need {MIN_LOBS}+")
                    continue

                # ── 3. COMPUTE: WLS triangulation ─────────────────────────
                estimate = wls_bearing_intersection(group)
                if estimate is None:
                    print(f"  [{cycles}] {cls}: WLS returned None (near-parallel bearings)")
                    continue

                # RESIDUAL CAP: reject wild intersections
                if estimate["residual_m"] > RESIDUAL_CAP:
                    print(f"  [{cycles}] {cls}: residual={estimate['residual_m']}m > {RESIDUAL_CAP}m — reject")
                    continue

                sensors = [l["name"] for l in group]
                obs_body = build_location_estimate(
                    estimate,
                    contributing_sensors=sensors,
                    contributing_lobs=group,
                    classification=cls,
                )

                print(f"  [{cycles}] FIX: {cls}  lat={estimate['estimatedLat']:.6f}  "
                      f"lon={estimate['estimatedLon']:.6f}  "
                      f"cep50={estimate['cep50_m']}m  "
                      f"residual={estimate['residual_m']}m  "
                      f"n={estimate['n']}  sensors={','.join(sensors)}")

                # ── 4. PRODUCE: Publish back to CSAPI ─────────────────────
                if not dry_run:
                    try:
                        result = api_post(
                            f"datastreams/{localizer_ds}/observations",
                            obs_body,
                        )
                        fixes_published += 1
                    except Exception as e:
                        print(f"  ⚠ POST failed: {e}")
                else:
                    print(f"         (dry-run — not published)")
                    fixes_published += 1

            if once:
                break
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n── Stopped by user ──")

    print(f"\n── Stats ──")
    print(f"  Cycles:          {cycles}")
    print(f"  LOBs consumed:   {lobs_consumed}")
    print(f"  Fixes published: {fixes_published}")


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="LOB Localizer — standalone CSAPI consumer/producer"
    )
    parser.add_argument("--once", action="store_true",
                        help="Run a single poll cycle, then exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Poll + compute, but don't POST results")
    args = parser.parse_args()

    print("=" * 60)
    print("  OS4CSAPI — LOB Localizer")
    print("=" * 60)
    print(f"  Server:        {BASE_URL}")
    print(f"  MA systems:    {list(SYSTEM_IDS.keys())}")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Staleness:     {MAX_LOB_AGE_S}s")
    print(f"  Correlation:   {CORRELATION_WINDOW}s")
    if args.dry_run:
        print(f"  Mode:          DRY RUN (no POST)")
    if args.once:
        print(f"  Mode:          SINGLE CYCLE")

    run_localizer(once=args.once, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
