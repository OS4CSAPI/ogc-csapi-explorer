#!/usr/bin/env python3
"""
Smoke test for the OS4CSAPI production server.

Verifies all known resources exist and have valid observations.
This is a READ-ONLY script — no writes to the server.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --verbose
    python scripts/smoke_test.py --strict         # tighter staleness thresholds
    python scripts/smoke_test.py --json            # machine-readable output
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request
from base64 import b64encode
from datetime import datetime, timezone

# ── Server config ────────────────────────────────────────────────────
BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = b64encode(b"os4csapi:ogc134mm").decode()
HEADERS = {
    "Authorization": f"Basic {AUTH}",
    "Accept": "application/json",
}

# ── Expected resources ───────────────────────────────────────────────
EXPECTED_SYSTEMS = {
    "040g": "SET Ft Huachuca",
    "0410": "Monitoring Site Node",
    "041g": "VHF Relay/Repeater",
    "0420": "ODAS AZ-MA-1",
    "0490": "ODAS AZ-MA-2",
    "049g": "ODAS AZ-MA-3",
    "04o0": "Localizer",
    "04og": "ISS Position Publisher",
    "04p0": "ISS Orbit Track Publisher",
    "0520": "NWS KTUS",
    "052g": "NWS KDMA",
    "0530": "NWS KFHU",
    "053g": "NWS KLUF",
    "0540": "NWS KPHX",
    "054g": "NWS KDCA",
    "0550": "NWS KIAD",
    "055g": "NWS KNYG",
    "0560": "NWS KDAY",
    "056g": "NWS KFFO",
    # ── NDBC buoys ──
    "0570": "NDBC 44025 Long Island",
    "057g": "NDBC 41009 Canaveral",
    "0580": "NDBC 42036 W Tampa",
    "058g": "NDBC 46025 Santa Monica",
    "0590": "NDBC 46013 Bodega Bay",
}

EXPECTED_DEPLOYMENTS = {
    "040g": "Intelligence Collection Operation",
    "048g": "Orbital Tracking Demo",
    "04mg": "NWS Weather Demo",
    "04sg": "NDBC Buoy Demo",
}

# Datastreams grouped by feed for clearer reporting
# IDs verified against production server 2026-03-10
DATASTREAMS = {
    # ── UAS / MA infrastructure ──
    "SENREP":                         {"id": "044g", "system": "040g"},
    # AZ-MA-1 (system 0420)
    "AZ-MA-1 LOB":                    {"id": "04c0", "system": "0420"},
    "AZ-MA-1 Classification":         {"id": "0430", "system": "0420"},
    "AZ-MA-1 Detection Capabilities": {"id": "04dg", "system": "0420"},
    "AZ-MA-1 Health":                 {"id": "043g", "system": "0420"},
    "AZ-MA-1 Scene Summary":          {"id": "0440", "system": "0420"},
    "AZ-MA-1 SSL Potential Sources":   {"id": "0410", "system": "0420"},
    "AZ-MA-1 SST Tracked Sources":     {"id": "041g", "system": "0420"},
    "AZ-MA-1 Track Updates":          {"id": "042g", "system": "0420"},
    # AZ-MA-2 (system 0490)
    "AZ-MA-2 LOB":                    {"id": "04cg", "system": "0490"},
    "AZ-MA-2 Classification":         {"id": "0450", "system": "0490"},
    "AZ-MA-2 Detection Capabilities": {"id": "04e0", "system": "0490"},
    "AZ-MA-2 Health":                 {"id": "045g", "system": "0490"},
    "AZ-MA-2 Scene Summary":          {"id": "046g", "system": "0490"},
    "AZ-MA-2 SSL Potential Sources":   {"id": "0470", "system": "0490"},
    "AZ-MA-2 SST Tracked Sources":     {"id": "047g", "system": "0490"},
    "AZ-MA-2 Track Updates":          {"id": "0480", "system": "0490"},
    # AZ-MA-3 (system 049g)
    "AZ-MA-3 LOB":                    {"id": "04d0", "system": "049g"},
    "AZ-MA-3 Classification":         {"id": "048g", "system": "049g"},
    "AZ-MA-3 Detection Capabilities": {"id": "04eg", "system": "049g"},
    "AZ-MA-3 Health":                 {"id": "0490", "system": "049g"},
    "AZ-MA-3 Scene Summary":          {"id": "04a0", "system": "049g"},
    "AZ-MA-3 SSL Potential Sources":   {"id": "04ag", "system": "049g"},
    "AZ-MA-3 SST Tracked Sources":     {"id": "04b0", "system": "049g"},
    "AZ-MA-3 Track Updates":          {"id": "04bg", "system": "049g"},
    # ── Localizer ──
    "UAS Location Estimate":          {"id": "04l0", "system": "04o0"},
    # ── ISS ──
    "ISS Position SGP4":              {"id": "04gg", "system": "04og"},
    "ISS Orbit Ground Track":         {"id": "04h0", "system": "04p0"},
    # ── NWS ──
    "NWS KTUS Surface Obs":           {"id": "04qg", "system": "0520"},
    "NWS KDMA Surface Obs":           {"id": "04r0", "system": "052g"},
    "NWS KFHU Surface Obs":           {"id": "04rg", "system": "0530"},
    "NWS KLUF Surface Obs":           {"id": "04s0", "system": "053g"},
    "NWS KPHX Surface Obs":           {"id": "04sg", "system": "0540"},
    "NWS KDCA Surface Obs":           {"id": "04t0", "system": "054g"},
    "NWS KIAD Surface Obs":           {"id": "04tg", "system": "0550"},
    "NWS KNYG Surface Obs":           {"id": "04u0", "system": "055g"},
    "NWS KDAY Surface Obs":           {"id": "04ug", "system": "0560"},
    "NWS KFFO Surface Obs":           {"id": "04v0", "system": "056g"},
    # ── NDBC buoys ──
    "NDBC 44025 Buoy Obs":             {"id": "04vg", "system": "0570"},
    "NDBC 41009 Buoy Obs":             {"id": "0500", "system": "057g"},
    "NDBC 42036 Buoy Obs":             {"id": "050g", "system": "0580"},
    "NDBC 46025 Buoy Obs":             {"id": "0510", "system": "058g"},
    "NDBC 46013 Buoy Obs":             {"id": "051g", "system": "0590"},
}

# These DS we MUST have fresh observations for (active feeds)
# Others (like MA sub-DS) may or may not have data depending on sim state
CRITICAL_DATASTREAMS = [
    "ISS Position SGP4",
    "ISS Orbit Ground Track",
    "NWS KTUS Surface Obs",
    "NWS KDMA Surface Obs",
    "NWS KFHU Surface Obs",
    "NWS KLUF Surface Obs",
    "NWS KPHX Surface Obs",
    "NWS KDCA Surface Obs",
    "NWS KIAD Surface Obs",
    "NWS KNYG Surface Obs",
    "NWS KDAY Surface Obs",
    "NWS KFFO Surface Obs",
    "AZ-MA-1 LOB",
    "AZ-MA-2 LOB",
    "AZ-MA-3 LOB",
    "UAS Location Estimate",
    "SENREP",
    "NDBC 44025 Buoy Obs",
    "NDBC 41009 Buoy Obs",
    "NDBC 42036 Buoy Obs",
    "NDBC 46025 Buoy Obs",
    "NDBC 46013 Buoy Obs",
]

# ── Helpers ──────────────────────────────────────────────────────────

def api_get(path: str, timeout: int = 15):
    """GET a JSON resource from the server. Returns (status, data | None)."""
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, str(e)


def obs_age_minutes(result_time_str: str) -> float:
    """Parse an ISO-8601 resultTime and return age in minutes."""
    rt = result_time_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(rt)
    delta = datetime.now(timezone.utc) - dt
    return delta.total_seconds() / 60.0


class Check:
    """A single named check with pass/fail/skip and detail message."""
    def __init__(self, name: str):
        self.name = name
        self.passed = None  # None = skipped
        self.detail = ""

    def ok(self, detail: str = ""):
        self.passed = True
        self.detail = detail

    def fail(self, detail: str):
        self.passed = False
        self.detail = detail

    def skip(self, detail: str = ""):
        self.passed = None
        self.detail = detail

    @property
    def symbol(self):
        if self.passed is True:
            return "\u2705"  # ✅
        elif self.passed is False:
            return "\u274c"  # ❌
        else:
            return "\u23ed\ufe0f"  # ⏭️

    def __str__(self):
        msg = f"  {self.symbol}  {self.name}"
        if self.detail:
            msg += f"  —  {self.detail}"
        return msg


# ── Checks ───────────────────────────────────────────────────────────

def check_global_datastreams(verbose: bool) -> Check:
    """The global /datastreams endpoint must not 500 and must return all DS."""
    c = Check("Global /datastreams endpoint")
    status, data = api_get("/datastreams?limit=200")
    if status != 200:
        c.fail(f"HTTP {status}")
        return c
    count = len(data.get("items", []))
    if count < 40:
        c.fail(f"Only {count} datastreams (expected >= 40)")
    else:
        c.ok(f"{count} datastreams")
    return c


def check_global_systems(verbose: bool) -> Check:
    c = Check("Global /systems endpoint")
    status, data = api_get("/systems?limit=100")
    if status != 200:
        c.fail(f"HTTP {status}")
        return c
    count = len(data.get("items", []))
    if count < 24:
        c.fail(f"Only {count} systems (expected >= 24)")
    else:
        c.ok(f"{count} systems")
    return c


def check_global_deployments(verbose: bool) -> Check:
    c = Check("Global /deployments endpoint")
    status, data = api_get("/deployments?limit=100")
    if status != 200:
        c.fail(f"HTTP {status}")
        return c
    count = len(data.get("items", []))
    if count < 4:
        c.fail(f"Only {count} deployments (expected >= 4)")
    else:
        c.ok(f"{count} deployments")
    return c


def check_system_exists(sys_id: str, expected_name: str, verbose: bool) -> Check:
    c = Check(f"System {sys_id} ({expected_name})")
    status, data = api_get(f"/systems/{sys_id}")
    if status != 200:
        c.fail(f"HTTP {status}")
        return c
    actual = data.get("properties", {}).get("name", "?")
    c.ok(f"exists — \"{actual}\"")
    return c


def check_deployment_exists(dep_id: str, expected_name: str, verbose: bool) -> Check:
    c = Check(f"Deployment {dep_id} ({expected_name})")
    status, data = api_get(f"/deployments/{dep_id}")
    if status != 200:
        c.fail(f"HTTP {status}")
        return c
    actual = data.get("properties", {}).get("name", "?")
    c.ok(f"exists — \"{actual}\"")
    return c


def check_datastream_obs(ds_name: str, ds_info: dict, is_critical: bool, verbose: bool, strict: bool = False) -> Check:
    """Check a datastream has at least one observation."""
    ds_id = ds_info["id"]
    c = Check(f"DS {ds_id} — {ds_name}")

    # First verify the DS itself exists
    status, data = api_get(f"/datastreams/{ds_id}")
    if status != 200:
        if is_critical:
            c.fail(f"DS not found (HTTP {status})")
        else:
            c.skip(f"DS not found (HTTP {status}) — non-critical")
        return c

    # Fetch latest observation
    status, obs_data = api_get(f"/datastreams/{ds_id}/observations?limit=1&resultTime=latest")
    if status != 200:
        c.fail(f"Observations query HTTP {status}")
        return c

    items = obs_data.get("items", [])
    if len(items) == 0:
        if is_critical:
            c.fail("No observations")
        else:
            c.skip("No observations — non-critical")
        return c

    obs = items[0]
    rt = obs.get("resultTime", "")
    age_min = obs_age_minutes(rt) if rt else float("inf")

    # Staleness thresholds (minutes):
    #   ISS:       5 min  — publisher runs continuously on Oracle
    #   NWS:     480 min  — publisher may run periodically (~8 hr grace)
    #   Simulator: 360 min (6 hr) — may not always be running
    # Use --strict to tighten: ISS 2m, NWS 120m, Sim 10m

    if "ISS" in ds_name:
        max_age = 2 if strict else 5
        if age_min > max_age:
            c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
        else:
            c.ok(f"fresh — {age_min:.1f} min old")

    elif "NWS" in ds_name or "NDBC" in ds_name:
        max_age = 120 if strict else 480
        if age_min > max_age:
            c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
        else:
            # Also check result has lat/lon/temp
            result = obs.get("result", {})
            lat = result.get("lat_deg")
            lon = result.get("lon_deg")
            # NWS uses temperature_c, NDBC uses air_temp_c
            temp = result.get("temperature_c") if "NWS" in ds_name else result.get("air_temp_c")
            missing = []
            if lat is None:
                missing.append("lat")
            if lon is None:
                missing.append("lon")
            if temp is None:
                missing.append("temp")
            if missing:
                c.fail(f"Missing fields: {', '.join(missing)}")
            else:
                temp_str = "NaN" if (isinstance(temp, float) and math.isnan(temp)) else f"{temp}°C"
                c.ok(f"fresh — {age_min:.0f} min old, {temp_str}")

    # Simulator feeds (LOB, SENREP, Location Estimate)
    else:
        max_age = 10 if strict else 360
        if age_min > max_age:
            if is_critical:
                c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
            else:
                c.skip(f"Stale — {age_min:.0f} min old — non-critical")
        else:
            c.ok(f"fresh — {age_min:.1f} min old")

    return c


# ── Main ─────────────────────────────────────────────────────────────

def run_smoke_test(verbose: bool = False, json_output: bool = False, strict: bool = False):
    t0 = time.time()
    results: list[Check] = []

    # 1. Global endpoints
    results.append(check_global_datastreams(verbose))
    results.append(check_global_systems(verbose))
    results.append(check_global_deployments(verbose))

    # 2. Individual systems
    for sys_id, name in EXPECTED_SYSTEMS.items():
        results.append(check_system_exists(sys_id, name, verbose))

    # 3. Individual deployments
    for dep_id, name in EXPECTED_DEPLOYMENTS.items():
        results.append(check_deployment_exists(dep_id, name, verbose))

    # 4. Critical datastream observations
    for ds_name in CRITICAL_DATASTREAMS:
        ds_info = DATASTREAMS[ds_name]
        results.append(check_datastream_obs(ds_name, ds_info, is_critical=True, verbose=verbose, strict=strict))

    elapsed = time.time() - t0
    passed = sum(1 for r in results if r.passed is True)
    failed = sum(1 for r in results if r.passed is False)
    skipped = sum(1 for r in results if r.passed is None)
    total = len(results)

    if json_output:
        out = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": round(elapsed, 1),
            "totals": {"passed": passed, "failed": failed, "skipped": skipped, "total": total},
            "checks": [
                {"name": r.name, "passed": r.passed, "detail": r.detail}
                for r in results
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print()
        print("=" * 60)
        print("  OS4CSAPI Production Smoke Test")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)
        print()

        # Group output
        sections = [
            ("Global Endpoints", [r for r in results if r.name.startswith("Global")]),
            ("Systems", [r for r in results if r.name.startswith("System")]),
            ("Deployments", [r for r in results if r.name.startswith("Deployment")]),
            ("Datastream Observations", [r for r in results if r.name.startswith("DS")]),
        ]

        for section_name, checks in sections:
            print(f"  ── {section_name} ──")
            for c in checks:
                print(str(c))
            print()

        # Summary
        print("-" * 60)
        status_line = f"  {passed} passed, {failed} failed, {skipped} skipped  ({total} total, {elapsed:.1f}s)"
        if failed > 0:
            print(f"  \u274c  SMOKE TEST FAILED")
        else:
            print(f"  \u2705  SMOKE TEST PASSED")
        print(status_line)
        print("-" * 60)
        print()

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OS4CSAPI production smoke test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show extra detail")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Machine-readable JSON output")
    parser.add_argument("--strict", action="store_true", help="Tighter staleness thresholds (ISS 2m, NWS 120m, Sim 10m)")
    args = parser.parse_args()

    sys.exit(run_smoke_test(verbose=args.verbose, json_output=args.json_output, strict=args.strict))
