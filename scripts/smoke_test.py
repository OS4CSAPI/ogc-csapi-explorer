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
BASE = "https://129-80-248-53.sslip.io/sensorhub/api"
AUTH = b64encode(b"os4csapi:ogc134mm").decode()
HEADERS = {
    "Authorization": f"Basic {AUTH}",
    "Accept": "application/json",
}

# ── Expected resources ───────────────────────────────────────────────
EXPECTED_SYSTEMS = {
    "04dg": "SET Ft Huachuca",
    "04e0": "Monitoring Site Node",
    "04eg": "VHF Relay/Repeater",
    "04f0": "ODAS AZ-MA-1",
    "04fg": "ODAS AZ-MA-2",
    "04g0": "ODAS AZ-MA-3",
    "0540": "Localizer",
    "054g": "ISS Position Publisher",
    "0550": "ISS Orbit Track Publisher",
    "040g": "NWS KTUS",
    "0410": "NWS KDMA",
    "041g": "NWS KFHU",
    "0420": "NWS KLUF",
    "042g": "NWS KPHX",
    "0430": "NWS KDCA",
    "043g": "NWS KIAD",
    "0440": "NWS KNYG",
    "044g": "NWS KDAY",
    "0450": "NWS KFFO",
    # ── NDBC buoys ──
    "045g": "NDBC 44025 Long Island",
    "0460": "NDBC 41009 Canaveral",
    "046g": "NDBC 42036 W Tampa",
    "0470": "NDBC 46025 Santa Monica",
    "047g": "NDBC 46013 Bodega Bay",
    # ── CO-OPS tide stations ──
    "0480": "CO-OPS 8518750 The Battery",
    "048g": "CO-OPS 8723214 Virginia Key",
    "0490": "CO-OPS 8726520 St. Petersburg",
    "049g": "CO-OPS 9414290 San Francisco",
    "04a0": "CO-OPS 8443970 Boston",
    # ── AviationWeather METAR stations ──
    "04ag": "AWX KTUS Tucson Intl",
    "04b0": "AWX KDMA Davis-Monthan",
    "04bg": "AWX KFHU Fort Huachuca",
    "04c0": "AWX KLUF Luke AFB",
    "04cg": "AWX KPHX Sky Harbor",
    # ── OpenSky ADS-B feed ──
    "04d0": "OpenSky ADS-B Feed",
    # ── USGS Water monitoring stations ──
    "055g": "USGS 09380000 Colorado River Lees Ferry",
    "0560": "USGS 09019850 Willow Creek Granby",
    "056g": "USGS 11313433 Dutch Slough",
    "0570": "USGS 08171000 Blanco River Wimberley",
    "057g": "USGS 01650800 Sligo Creek Takoma Park",
    "0580": "USGS 05051300 Bois De Sioux Doran",
    "058g": "USGS 12439500 Okanogan River Oroville",
    "0590": "USGS 02135000 Little Pee Dee Galivants Ferry",
    # ── USGS Earthquake feed ──
    "059g": "USGS Earthquake Feed",
}

EXPECTED_DEPLOYMENTS = {
    "04i0": "Intelligence Collection Operation",
    "04o0": "Orbital Tracking Demo",
    "040g": "NWS Weather Demo",
    "046g": "NDBC Buoy Demo",
    "04a0": "CO-OPS Coastal Demo",
    "04dg": "AWX METAR Demo",
    "04h0": "Airspace Tracking Demo",
    "04hg": "OpenSky ADS-B Feed",           # sub-deployment of 04h0
    "04qg": "USGS Water Monitoring Demo",
    "055g": "USGS NIMS Imagery Demo",
    "05ag": "Seismic Monitoring Demo",
    "05b0": "USGS Earthquake Feed",          # sub-deployment of 05ag
}

# Datastreams grouped by feed for clearer reporting
# IDs verified against production server 2026-03-12 (post DB rebuild)
DATASTREAMS = {
    # ── UAS / MA infrastructure ──
    "SENREP":                         {"id": "04g0", "system": "04dg"},
    # AZ-MA-1 (system 04f0)
    "AZ-MA-1 LOB":                    {"id": "04hg", "system": "04f0"},
    "AZ-MA-1 Classification":         {"id": "04gg", "system": "04f0"},
    "AZ-MA-1 Detection Capabilities": {"id": "04k0", "system": "04f0"},
    "AZ-MA-1 Health":                 {"id": "04h0", "system": "04f0"},
    "AZ-MA-1 Scene Summary":          {"id": "04i0", "system": "04f0"},
    "AZ-MA-1 SSL Potential Sources":   {"id": "04ig", "system": "04f0"},
    "AZ-MA-1 SST Tracked Sources":     {"id": "04j0", "system": "04f0"},
    "AZ-MA-1 Track Updates":          {"id": "04jg", "system": "04f0"},
    # AZ-MA-2 (system 04fg)
    "AZ-MA-2 LOB":                    {"id": "04lg", "system": "04fg"},
    "AZ-MA-2 Classification":         {"id": "04kg", "system": "04fg"},
    "AZ-MA-2 Detection Capabilities": {"id": "04o0", "system": "04fg"},
    "AZ-MA-2 Health":                 {"id": "04l0", "system": "04fg"},
    "AZ-MA-2 Scene Summary":          {"id": "04m0", "system": "04fg"},
    "AZ-MA-2 SSL Potential Sources":   {"id": "04mg", "system": "04fg"},
    "AZ-MA-2 SST Tracked Sources":     {"id": "04n0", "system": "04fg"},
    "AZ-MA-2 Track Updates":          {"id": "04ng", "system": "04fg"},
    # AZ-MA-3 (system 04g0)
    "AZ-MA-3 LOB":                    {"id": "04pg", "system": "04g0"},
    "AZ-MA-3 Classification":         {"id": "04og", "system": "04g0"},
    "AZ-MA-3 Detection Capabilities": {"id": "04s0", "system": "04g0"},
    "AZ-MA-3 Health":                 {"id": "04p0", "system": "04g0"},
    "AZ-MA-3 Scene Summary":          {"id": "04q0", "system": "04g0"},
    "AZ-MA-3 SSL Potential Sources":   {"id": "04qg", "system": "04g0"},
    "AZ-MA-3 SST Tracked Sources":     {"id": "04r0", "system": "04g0"},
    "AZ-MA-3 Track Updates":          {"id": "04rg", "system": "04g0"},
    # ── Localizer ──
    "UAS Location Estimate":          {"id": "04t0", "system": "0540"},
    # ── ISS ──
    "ISS Position SGP4":              {"id": "04tg", "system": "054g"},
    "ISS Orbit Ground Track":         {"id": "04u0", "system": "0550"},
    # ── NWS ──
    "NWS KTUS Surface Obs":           {"id": "040g", "system": "040g"},
    "NWS KDMA Surface Obs":           {"id": "0410", "system": "0410"},
    "NWS KFHU Surface Obs":           {"id": "041g", "system": "041g"},
    "NWS KLUF Surface Obs":           {"id": "0420", "system": "0420"},
    "NWS KPHX Surface Obs":           {"id": "042g", "system": "042g"},
    "NWS KDCA Surface Obs":           {"id": "0430", "system": "0430"},
    "NWS KIAD Surface Obs":           {"id": "043g", "system": "043g"},
    "NWS KNYG Surface Obs":           {"id": "0440", "system": "0440"},
    "NWS KDAY Surface Obs":           {"id": "044g", "system": "044g"},
    "NWS KFFO Surface Obs":           {"id": "0450", "system": "0450"},
    # ── NDBC buoys (met obs) ──
    "NDBC 44025 Met Obs":              {"id": "045g", "system": "045g"},
    "NDBC 41009 Met Obs":              {"id": "046g", "system": "0460"},
    "NDBC 42036 Met Obs":              {"id": "047g", "system": "046g"},
    "NDBC 46025 Met Obs":              {"id": "048g", "system": "0470"},
    "NDBC 46013 Met Obs":              {"id": "049g", "system": "047g"},
    # ── NDBC buoys (BuoyCAM) ──
    "NDBC 44025 BuoyCAM":              {"id": "0460", "system": "045g"},
    "NDBC 41009 BuoyCAM":              {"id": "0470", "system": "0460"},
    "NDBC 42036 BuoyCAM":              {"id": "0480", "system": "046g"},
    "NDBC 46025 BuoyCAM":              {"id": "0490", "system": "0470"},
    "NDBC 46013 BuoyCAM":              {"id": "04a0", "system": "047g"},
    # ── CO-OPS tide stations ──
    "CO-OPS 8518750 Coastal Obs":       {"id": "04ag", "system": "0480"},
    "CO-OPS 8723214 Coastal Obs":       {"id": "04b0", "system": "048g"},
    "CO-OPS 8726520 Coastal Obs":       {"id": "04bg", "system": "0490"},
    "CO-OPS 9414290 Coastal Obs":       {"id": "04c0", "system": "049g"},
    "CO-OPS 8443970 Coastal Obs":       {"id": "04cg", "system": "04a0"},
    # ── AviationWeather METAR stations ──
    "AWX KTUS METAR Obs":              {"id": "04d0", "system": "04ag"},
    "AWX KDMA METAR Obs":              {"id": "04dg", "system": "04b0"},
    "AWX KFHU METAR Obs":              {"id": "04e0", "system": "04bg"},
    "AWX KLUF METAR Obs":              {"id": "04eg", "system": "04c0"},
    "AWX KPHX METAR Obs":              {"id": "04f0", "system": "04cg"},
    # ── OpenSky ADS-B feed ──
    "OpenSky ADS-B States":              {"id": "05fg", "system": "04d0"},
    # ── USGS Water monitoring (discharge) ──
    "USGS 09380000 Discharge":            {"id": "04ug", "system": "055g"},
    "USGS 09019850 Discharge":            {"id": "04vg", "system": "0560"},
    "USGS 11313433 Discharge":            {"id": "050g", "system": "056g"},
    "USGS 08171000 Discharge":            {"id": "051g", "system": "0570"},
    "USGS 01650800 Discharge":            {"id": "052g", "system": "057g"},
    "USGS 05051300 Discharge":            {"id": "053g", "system": "0580"},
    "USGS 12439500 Discharge":            {"id": "054g", "system": "058g"},
    "USGS 02135000 Discharge":            {"id": "055g", "system": "0590"},
    # ── USGS Water monitoring (gage height) ──
    "USGS 09380000 Gage Height":          {"id": "04v0", "system": "055g"},
    "USGS 09019850 Gage Height":          {"id": "0500", "system": "0560"},
    "USGS 11313433 Gage Height":          {"id": "0510", "system": "056g"},
    "USGS 08171000 Gage Height":          {"id": "0520", "system": "0570"},
    "USGS 01650800 Gage Height":          {"id": "0530", "system": "057g"},
    "USGS 05051300 Gage Height":          {"id": "0540", "system": "0580"},
    "USGS 12439500 Gage Height":          {"id": "0550", "system": "058g"},
    "USGS 02135000 Gage Height":          {"id": "0560", "system": "0590"},
    # ── USGS NIMS Imagery ──
    "NIMS 09380000 Imagery":              {"id": "05b0", "system": "055g"},
    "NIMS 09019850 Imagery":              {"id": "05bg", "system": "0560"},
    "NIMS 11313433 Imagery":              {"id": "05c0", "system": "056g"},
    "NIMS 08171000 Imagery":              {"id": "05cg", "system": "0570"},
    "NIMS 01650800 Imagery":              {"id": "05d0", "system": "057g"},
    "NIMS 05051300 Imagery":              {"id": "05dg", "system": "0580"},
    "NIMS 12439500 Imagery":              {"id": "05e0", "system": "058g"},
    "NIMS 02135000 Imagery":              {"id": "05eg", "system": "0590"},
    # ── USGS Earthquake feed ──
    "USGS Earthquake Events":             {"id": "05f0", "system": "059g"},
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
    "NDBC 44025 Met Obs",
    "NDBC 41009 Met Obs",
    "NDBC 42036 Met Obs",
    "NDBC 46025 Met Obs",
    "NDBC 46013 Met Obs",
    "NDBC 44025 BuoyCAM",
    "NDBC 41009 BuoyCAM",
    "NDBC 42036 BuoyCAM",
    "NDBC 46025 BuoyCAM",
    "NDBC 46013 BuoyCAM",
    "CO-OPS 8518750 Coastal Obs",
    "CO-OPS 8723214 Coastal Obs",
    "CO-OPS 8726520 Coastal Obs",
    "CO-OPS 9414290 Coastal Obs",
    "CO-OPS 8443970 Coastal Obs",
    "AWX KTUS METAR Obs",
    "AWX KDMA METAR Obs",
    "AWX KFHU METAR Obs",
    "AWX KLUF METAR Obs",
    "AWX KPHX METAR Obs",
    "OpenSky ADS-B States",
    # ── USGS Water (discharge) ──
    "USGS 09380000 Discharge",
    "USGS 09019850 Discharge",
    "USGS 11313433 Discharge",
    "USGS 08171000 Discharge",
    "USGS 01650800 Discharge",
    "USGS 05051300 Discharge",
    "USGS 12439500 Discharge",
    "USGS 02135000 Discharge",
    # ── USGS Water (gage height) ──
    "USGS 09380000 Gage Height",
    "USGS 09019850 Gage Height",
    "USGS 11313433 Gage Height",
    "USGS 08171000 Gage Height",
    "USGS 01650800 Gage Height",
    "USGS 05051300 Gage Height",
    "USGS 12439500 Gage Height",
    "USGS 02135000 Gage Height",
    # ── USGS NIMS Imagery ──
    "NIMS 09380000 Imagery",
    "NIMS 09019850 Imagery",
    "NIMS 11313433 Imagery",
    "NIMS 08171000 Imagery",
    "NIMS 01650800 Imagery",
    "NIMS 05051300 Imagery",
    "NIMS 12439500 Imagery",
    "NIMS 02135000 Imagery",
    # ── USGS Earthquake feed ──
    "USGS Earthquake Events",
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
    if count < 71:
        c.fail(f"Only {count} datastreams (expected >= 71)")
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
    if count < 39:
        c.fail(f"Only {count} systems (expected >= 39)")
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
    if count < 10:
        c.fail(f"Only {count} deployments (expected >= 10)")
    else:
        c.ok(f"{count} top-level deployments")
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

    elif "USGS" in ds_name or "NIMS" in ds_name:
        max_age = 120 if strict else 480
        if age_min > max_age:
            c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
        else:
            result = obs.get("result", {})
            if "Discharge" in ds_name:
                val = result.get("discharge_cfs")
                val_str = f"{val} ft³/s" if val is not None else "—"
            elif "Gage" in ds_name:
                val = result.get("gage_height_ft")
                val_str = f"{val} ft" if val is not None else "—"
            elif "NIMS" in ds_name:
                fn = result.get("filename", "—")
                val_str = fn
            elif "Earthquake" in ds_name:
                mag = result.get("magnitude")
                place = result.get("place", "—")
                val_str = f"M{mag} {place}" if mag is not None else place
            else:
                val_str = "ok"
            c.ok(f"fresh — {age_min:.0f} min old, {val_str}")

    elif "NWS" in ds_name or "NDBC" in ds_name or "CO-OPS" in ds_name or "AWX" in ds_name:
        max_age = 120 if strict else 480
        if age_min > max_age:
            c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
        else:
            # Also check result has lat/lon/temp
            result = obs.get("result", {})
            lat = result.get("lat_deg")
            lon = result.get("lon_deg")
            # NWS uses temperature_c, NDBC uses air_temp_c, CO-OPS uses air_temp_c
            if "NWS" in ds_name:
                temp = result.get("temperature_c")
            else:
                temp = result.get("air_temp_c")
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
                if "CO-OPS" in ds_name:
                    wl = result.get("water_level_m")
                    wl_str = f", wl={wl}m" if wl is not None else ""
                    c.ok(f"fresh — {age_min:.0f} min old, {temp_str}{wl_str}")
                else:
                    c.ok(f"fresh — {age_min:.0f} min old, {temp_str}")

    # OpenSky ADS-B feed (aircraft state vectors)
    elif "OpenSky" in ds_name:
        max_age = 120 if strict else 480
        if age_min > max_age:
            c.fail(f"Stale — {age_min:.0f} min old (max {max_age} min)")
        else:
            result = obs.get("result", {})
            callsign = result.get("callsign", "?").strip()
            alt = result.get("baro_altitude_m")
            alt_str = f"{alt}m" if alt is not None and alt != "NaN" else "—"
            c.ok(f"fresh — {age_min:.0f} min old, {callsign} alt={alt_str}")

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
