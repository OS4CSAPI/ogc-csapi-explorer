"""
FastAPI wrapper for the OS4CSAPI Data Simulator.

Provides REST endpoints to start/stop/status the UAV flythrough simulation
and to clear observations from the server.

Deployed on Oracle VM behind Caddy reverse proxy.
"""

import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import the simulator engine (shared module)
from engine import (
    BASE_URL,
    NODES,
    UAV_WAYPOINTS,
    haversine_m,
    bearing_deg,
    total_path_length_m,
    interpolate_position,
    build_lob_observation,
    find_system_id,
    find_datastream_id,
    api_get,
    api_post,
    iso_now,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Simulation state (shared between FastAPI handlers and worker thread)
# ═══════════════════════════════════════════════════════════════════════════

class SimState:
    """Thread-safe mutable state for the running simulation."""

    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

        # Config (set on /start)
        self.duration_s: int = 3600
        self.interval_s: float = 5.0
        self.speed_kmh: float = 12.0
        self.start_offset_s: float = 0.0

        # Live telemetry
        self.tick: int = 0
        self.uav_lat: float = 0.0
        self.uav_lon: float = 0.0
        self.detecting: list[str] = []
        self.published: int = 0
        self.errors: int = 0
        self.detecting_ticks: int = 0
        self.started_at: float | None = None
        self.message: str = ""

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            elapsed = time.time() - self.started_at if self.started_at else 0
            return {
                "running": self.running,
                "tick": self.tick,
                "uav_lat": round(self.uav_lat, 6),
                "uav_lon": round(self.uav_lon, 6),
                "detecting": list(self.detecting),
                "published": self.published,
                "errors": self.errors,
                "detecting_ticks": self.detecting_ticks,
                "elapsed_s": round(elapsed, 1),
                "message": self.message,
                "config": {
                    "duration_s": self.duration_s,
                    "interval_s": self.interval_s,
                    "speed_kmh": self.speed_kmh,
                    "start_offset_s": self.start_offset_s,
                },
            }

    def reset(self):
        self.tick = 0
        self.uav_lat = 0.0
        self.uav_lon = 0.0
        self.detecting = []
        self.published = 0
        self.errors = 0
        self.detecting_ticks = 0
        self.started_at = None
        self.message = ""


state = SimState()


# ═══════════════════════════════════════════════════════════════════════════
#  Simulation worker (runs in a background thread)
# ═══════════════════════════════════════════════════════════════════════════

# ── Detection range seeding (ensures rings survive clears) ──────────────

DETECTION_RANGE = {
    "minRange_m": 667,
    "nominalRange_m": 1833,
    "maxRange_m": 3000,
    "shape": "circular",
    "confidence": 0.7,
    "basis": "estimated",
}

def seed_detection_ranges() -> int:
    """Ensure each detection-capabilities datastream has a valid observation.

    Checks the latest observation in each DS — if it's missing the expected
    range fields (minRange_m etc.), posts a fresh observation.  Returns the
    number of datastreams that were (re-)seeded.
    """
    seeded = 0
    for ds_id in DETECTION_DS_IDS:
        try:
            resp = api_get(f"datastreams/{ds_id}/observations?resultTime=latest&limit=1")
            items = resp.get("items", []) if resp else []
            result = items[0].get("result", {}) if items else {}
            if isinstance(result.get("minRange_m"), (int, float)):
                continue  # already has valid detection range data
        except Exception:
            pass  # treat any error as "needs seeding"

        # Post a fresh detection-range observation
        now = time.time()
        obs = {
            "phenomenonTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "resultTime":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "result": {
                "timestamp":      now,
                "shape":           DETECTION_RANGE["shape"],
                "minRange_m":     DETECTION_RANGE["minRange_m"],
                "nominalRange_m": DETECTION_RANGE["nominalRange_m"],
                "maxRange_m":     DETECTION_RANGE["maxRange_m"],
                "confidence":     DETECTION_RANGE["confidence"],
                "basis":          DETECTION_RANGE["basis"],
            },
        }
        try:
            api_post(f"datastreams/{ds_id}/observations", obs)
            seeded += 1
        except Exception:
            pass  # non-fatal — rings just won't show
    return seeded


def simulation_worker(st: SimState):
    """
    Run the simulation loop; mirrors run_simulation() from
    simulate_scenario.py but reports telemetry via SimState.
    """
    try:
        # ── Ensure detection ranges are present ──────────────────────
        seed_detection_ranges()

        # ── Verify SENREP infrastructure ─────────────────────────────
        try:
            resp = api_get("datastreams/044g")
            if resp and resp.get("id") == "044g":
                print("[sim] SENREP infrastructure verified (DS 044g exists)")
            else:
                print("[sim] WARNING: SENREP DS 044g not found — report submission will fail")
        except Exception:
            print("[sim] WARNING: Could not verify SENREP DS 044g")

        # ── Discover datastream IDs ──────────────────────────────────
        with st.lock:
            st.message = "Discovering datastreams..."

        node_ds: dict[str, str] = {}
        for node in NODES:
            sys_id = find_system_id(node["uid"])
            if not sys_id:
                with st.lock:
                    st.message = f"ERROR: System {node['uid']} not found"
                    st.running = False
                return

            suffix = node["name"].lower().replace("-", "_")
            lob_name = f"{suffix}_lob"
            ds_id = find_datastream_id(sys_id, lob_name)
            if not ds_id:
                with st.lock:
                    st.message = f"ERROR: Datastream {lob_name} not found"
                    st.running = False
                return
            node_ds[node["uid"]] = ds_id

        # ── Path metrics ─────────────────────────────────────────────
        path_len = total_path_length_m(UAV_WAYPOINTS)
        uav_speed_ms = st.speed_kmh * 1000 / 3600

        with st.lock:
            st.message = "Running"
            st.started_at = time.time()

        start_time = time.time()
        tick = 0

        while not st.stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed >= st.duration_s:
                break

            # Compute UAV position
            dist_travelled = (elapsed + st.start_offset_s) * uav_speed_ms
            fraction = (dist_travelled % path_len) / path_len
            uav_lon, uav_lat = interpolate_position(UAV_WAYPOINTS, fraction)

            # Detection check
            detecting_nodes = []
            for node in NODES:
                dist = haversine_m(node["lat"], node["lon"], uav_lat, uav_lon)
                if dist <= node["detection_max_m"]:
                    detecting_nodes.append((node, dist))

            tick += 1

            # Update shared state
            with st.lock:
                st.tick = tick
                st.uav_lat = uav_lat
                st.uav_lon = uav_lon
                st.detecting = [n["name"] for n, _ in detecting_nodes]
                if detecting_nodes:
                    st.detecting_ticks += 1

            # POST observations
            if detecting_nodes:
                for node, dist in detecting_nodes:
                    ds_id = node_ds.get(node["uid"])
                    if not ds_id:
                        continue
                    obs = build_lob_observation(node, uav_lat, uav_lon, track_id=1)
                    try:
                        api_post(f"datastreams/{ds_id}/observations", obs)
                        with st.lock:
                            st.published += 1
                    except Exception:
                        with st.lock:
                            st.errors += 1

            # Wait for next tick
            next_tick = start_time + tick * st.interval_s
            remaining = next_tick - time.time()
            if remaining > 0:
                # Use stop_event.wait() so we can interrupt quickly
                st.stop_event.wait(timeout=remaining)

        with st.lock:
            st.message = "Completed" if not st.stop_event.is_set() else "Stopped"
            st.running = False

    except Exception as exc:
        with st.lock:
            st.message = f"ERROR: {exc}"
            st.running = False





# ═══════════════════════════════════════════════════════════════════════════
#  Observation clearing (reuses logic from clear_observations.py)
# ═══════════════════════════════════════════════════════════════════════════

# Detection-capabilities datastreams — NEVER cleared (static config, auto-seeded)
DETECTION_DS_IDS = ["04dg", "04e0", "04eg"]  # MA-1, MA-2, MA-3

# SENREP datastreams — cleared only on /reset (Tier 3)
SENREP_DS_IDS = ["044g", "04i0"]  # original + v1.1

# Sim/localizer datastreams — cleared on /clear (Tier 2)
SIM_DS_IDS = [
    "0430", "043g", "04c0", "0440", "0410", "041g", "042g",  # MA-1 (04c0 = LOB)
    "0450", "045g", "04cg", "046g", "0470", "047g", "0480",  # MA-2 (04cg = LOB)
    "048g", "0490", "04d0", "04a0", "04ag", "04b0", "04bg",  # MA-3 (04d0 = LOB)
    "04g0",  # UAS Location Estimate (compound localizer)
    "04hg",  # Location Estimate (localizer v2)
]

# Combined list (for reference)
ALL_DS_IDS = SIM_DS_IDS + SENREP_DS_IDS + DETECTION_DS_IDS


def clear_observations(ds_ids: list[str], protected_ds_ids: list[str] | None = None) -> dict[str, int]:
    """Delete observations from specified datastreams.

    NOTE: OSH has a scope leak bug where querying /datastreams/{id}/observations
    returns observations from ALL datastreams, and the returned datastream@id
    may not match the queried DS.

    Strategy: use an **allowlist** — only delete observations whose claimed
    ``datastream@id`` is in the target ``ds_ids`` set.  Anything not explicitly
    targeted is left untouched, so ISS feeds, bootstrap data, and any future
    datastreams are safe by default.

    The ``protected_ds_ids`` list is kept as a **second safety net**: even if
    an observation's ``datastream@id`` happens to match a target, it won't be
    deleted if it's in the protected set.  We also dedup by obs ID to avoid
    double-deleting across DS iterations.
    """
    import urllib.request
    import urllib.error
    import ssl
    import base64 as b64
    import json as _json

    allowed = set(ds_ids)
    protected = set(protected_ds_ids or [])

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    auth = "Basic " + b64.b64encode(b"os4csapi:ogc134mm").decode()

    total_deleted = 0
    errors = 0
    protected_skipped = 0
    already_seen = set()  # prevent double-delete across DS iterations

    for ds_id in ds_ids:
        page = 0
        while True:
            url = f"{BASE_URL}/datastreams/{ds_id}/observations?limit=50"
            req = urllib.request.Request(url, headers={
                "Authorization": auth,
                "Accept": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    data = _json.loads(resp.read().decode())
            except Exception:
                errors += 1
                break

            items = data.get("items", [])
            if not items:
                break

            for obs in items:
                obs_id = obs.get("id")
                if not obs_id:
                    continue
                if obs_id in already_seen:
                    continue
                already_seen.add(obs_id)

                obs_ds = obs.get("datastream@id", "")

                # Safety net: never delete observations in protected set
                if obs_ds in protected:
                    protected_skipped += 1
                    continue

                # ALLOWLIST: ONLY delete if the observation's own datastream
                # is one we were asked to clear.  Due to the scope leak, many
                # observations from unrelated DSs will appear here — skip them.
                if obs_ds not in allowed:
                    protected_skipped += 1
                    continue

                del_url = f"{BASE_URL}/datastreams/{ds_id}/observations/{obs_id}"
                del_req = urllib.request.Request(del_url, method="DELETE", headers={
                    "Authorization": auth,
                })
                try:
                    with urllib.request.urlopen(del_req, timeout=10, context=ctx) as _r:
                        pass
                    total_deleted += 1
                except Exception:
                    errors += 1

            page += 1
            if page > 500:  # safety cap
                break

    return {"deleted": total_deleted, "errors": errors, "protected_skipped": protected_skipped}


def clear_sampling_features() -> dict[str, int]:
    """Delete SENREP track SamplingFeatures from the server.

    Strategy: search BOTH the top-level ``/samplingFeatures`` endpoint AND
    every system's nested ``/systems/{id}/samplingFeatures`` endpoint.  The
    OSH server may expose features at one level or the other depending on
    internal state.

    Safety: only features whose UID starts with ``urn:os4csapi:track:`` are
    deleted — these are the track FOIs created when operators submit INIT
    SENREPs.  Bootstrap data, LOBs, detection rings, etc. are never touched.
    """
    import urllib.request
    import urllib.error
    import ssl
    import base64 as b64
    import json as _json

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    auth = "Basic " + b64.b64encode(b"os4csapi:ogc134mm").decode()

    SENREP_SF_UID_PREFIX = "urn:os4csapi:track:"

    total_deleted = 0
    errors = 0
    deleted_ids: set[str] = set()  # de-dup across top-level and nested scans

    def _delete_matching_sfs(list_url: str) -> None:
        """Paginate through a samplingFeatures endpoint and delete matches."""
        nonlocal total_deleted, errors
        offset = 0
        while True:
            sep = "&" if "?" in list_url else "?"
            url = f"{list_url}{sep}limit=50&offset={offset}"
            req = urllib.request.Request(url, headers={
                "Authorization": auth,
                "Accept": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    data = _json.loads(resp.read().decode())
            except Exception:
                errors += 1
                break

            items = data.get("items", [])
            if not items:
                break

            for sf in items:
                sf_id = sf.get("id")
                sf_uid = (
                    sf.get("properties", {}).get("uid", "")
                    or sf.get("uid", "")
                )
                if not sf_id or sf_id in deleted_ids:
                    continue
                # SAFETY: only delete SENREP track FOIs
                if not sf_uid.startswith(SENREP_SF_UID_PREFIX):
                    continue
                del_url = f"{BASE_URL}/samplingFeatures/{sf_id}"
                del_req = urllib.request.Request(
                    del_url, method="DELETE",
                    headers={"Authorization": auth},
                )
                try:
                    with urllib.request.urlopen(del_req, timeout=10, context=ctx) as _r:
                        pass
                    total_deleted += 1
                    deleted_ids.add(sf_id)
                except Exception:
                    errors += 1

            offset += len(items)
            if offset > 500:  # safety cap
                break

    # ── Pass 1: top-level endpoint ──────────────────────────────────────
    _delete_matching_sfs(f"{BASE_URL}/samplingFeatures")

    # ── Pass 2: nested under each system ────────────────────────────────
    system_ids: list[str] = []
    offset = 0
    while True:
        url = f"{BASE_URL}/systems?limit=100&offset={offset}"
        req = urllib.request.Request(url, headers={
            "Authorization": auth,
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = _json.loads(resp.read().decode())
        except Exception:
            errors += 1
            break

        items = data.get("items", [])
        if not items:
            break
        for sys in items:
            sid = sys.get("id")
            if sid:
                system_ids.append(sid)
        offset += len(items)
        if offset > 2000:  # safety cap
            break

    for sys_id in system_ids:
        _delete_matching_sfs(f"{BASE_URL}/systems/{sys_id}/samplingFeatures")

    return {"deleted": total_deleted, "errors": errors}


# ═══════════════════════════════════════════════════════════════════════════
#  FastAPI app
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # On shutdown, stop any running simulation
    state.stop_event.set()
    if state.thread and state.thread.is_alive():
        state.thread.join(timeout=5)


app = FastAPI(
    title="OS4CSAPI Simulator",
    description="UAV flythrough data simulator for the OS4CSAPI demo",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────

class StartRequest(BaseModel):
    duration_s: int = Field(3600, ge=10, le=86400, description="Duration in seconds")
    interval_s: float = Field(5.0, ge=1, le=60, description="Tick interval in seconds")
    speed_kmh: float = Field(12.0, ge=1, le=100, description="UAV speed in km/h")
    start_offset_s: float = Field(0.0, ge=0, le=10000, description="Skip into route (seconds)")


class MessageResponse(BaseModel):
    ok: bool
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "server": BASE_URL}


@app.get("/status")
def get_status():
    return state.snapshot()


@app.post("/start", response_model=MessageResponse)
def start_simulation(req: StartRequest = StartRequest()):
    with state.lock:
        if state.running:
            return MessageResponse(ok=False, message="Simulation already running")

        state.reset()
        state.running = True
        state.stop_event.clear()
        state.duration_s = req.duration_s
        state.interval_s = req.interval_s
        state.speed_kmh = req.speed_kmh
        state.start_offset_s = req.start_offset_s

    t = threading.Thread(target=simulation_worker, args=(state,), daemon=True)
    state.thread = t
    t.start()
    return MessageResponse(ok=True, message="Simulation started")


@app.post("/stop", response_model=MessageResponse)
def stop_simulation():
    with state.lock:
        if not state.running:
            return MessageResponse(ok=False, message="No simulation running")

    state.stop_event.set()
    if state.thread:
        state.thread.join(timeout=10)
    return MessageResponse(ok=True, message="Simulation stopped")


@app.post("/clear", response_model=MessageResponse)
def clear_sim_data():
    with state.lock:
        if state.running:
            return MessageResponse(ok=False, message="Stop simulator before clearing")

    result = clear_observations(SIM_DS_IDS, protected_ds_ids=DETECTION_DS_IDS + SENREP_DS_IDS)
    # Re-seed detection ranges so they're recent and discoverable despite scope-leak
    reseeded = seed_detection_ranges()
    return MessageResponse(
        ok=True,
        message=f"Cleared sim data: {result['deleted']} deleted ({result['errors']} errors, {result['protected_skipped']} protected, {reseeded} ranges re-seeded)",
    )


@app.post("/reset", response_model=MessageResponse)
def reset_demo():
    """Tier 3: Full demo reset — clears sim data AND SENREP reports."""
    with state.lock:
        if state.running:
            return MessageResponse(ok=False, message="Stop simulator before resetting")

    # Clear sampling features FIRST — the OSH server may cascade-delete them
    # when observations are removed, so we must find them before obs cleanup.
    sf_result = clear_sampling_features()
    result = clear_observations(SIM_DS_IDS + SENREP_DS_IDS, protected_ds_ids=DETECTION_DS_IDS)
    # Re-seed detection ranges so they're recent and discoverable despite scope-leak
    reseeded = seed_detection_ranges()
    obs_msg = f"{result['deleted']} observations ({result['errors']} errors, {result['protected_skipped']} protected)"
    sf_msg = f"{sf_result['deleted']} sampling features ({sf_result['errors']} errors)"
    return MessageResponse(
        ok=True,
        message=f"Full reset: {obs_msg}, {sf_msg}, {reseeded} ranges re-seeded",
    )


