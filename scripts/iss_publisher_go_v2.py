#!/usr/bin/env python3
"""
iss_publisher.py — ISS dual-product publisher (Position + Orbit Track).

Publishes TWO products from ISS NORAD TLE data:
  1. Position fixes (11 fields, every 30s) → ISS Position Publisher system
  2. Orbit ground-track predictions (~100 points, every 5min) → ISS Orbit Track system

Migrated from csapi-explorer/scripts/iss_publisher_v3.py to use the common
publisher framework. Publishes to Go CSAPI server via REST.

Configure via environment variables:
    OSH_ADDRESS        Server hostname            (required)
    OSH_PORT           Server port                (default: 443)
    OSH_USER           Auth username              (required)
    OSH_PASS           Auth password              (required)
    OSH_BASE_URL       REST base URL              (required for Go server)
    POS_SYSTEM_UID     Position system URN        (default: urn:os4csapi:system:iss-position-publisher:v1)
    POS_DS_NAME        Position datastream name   (default: ISS Position (SGP4))
    TRACK_SYSTEM_UID   Orbit track system URN     (default: urn:os4csapi:system:iss-orbittrack-publisher:v1)
    TRACK_DS_NAME      Orbit track DS name        (default: ISS Orbit Ground Track)
    NORAD_ID           NORAD catalog number       (default: 25544)

Usage:
    python -m publishers.iss.iss_publisher                   # run forever (30s cadence)
    python -m publishers.iss.iss_publisher --dry-run         # print only
    python -m publishers.iss.iss_publisher --once            # single observation
    python -m publishers.iss.iss_publisher --interval 10     # 10s cadence
    python -m publishers.iss.iss_publisher --tle-refresh 7200
    python -m publishers.iss.iss_publisher --track-interval 600  # orbit track every 10min
    python -m publishers.iss.iss_publisher --no-track        # disable orbit track
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.request import Request, urlopen

try:
    from sgp4.api import Satrec, WGS72
except ImportError:
    print("ERROR: sgp4 package not found. Install it with: pip install sgp4")
    sys.exit(1)

# Add parent dir to path so `publishers.base` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from publishers.base import PublisherBase


# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

NORAD_ID   = os.environ.get("NORAD_ID", "25544")
ASSET_NAME = os.environ.get("ASSET_NAME", "ISS (ZARYA)")
CELESTRAK_URL = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={NORAD_ID}&FORMAT=JSON"
FALLBACK_TLE_URL = f"https://tle.ivanstanojevic.me/api/tle/{NORAD_ID}"

# Orbit track generation parameters
TRACK_SYSTEM_UID  = os.environ.get("TRACK_SYSTEM_UID",
                                    "urn:os4csapi:system:iss-orbittrack-publisher:v1")
TRACK_DS_NAME     = os.environ.get("TRACK_DS_NAME", "ISS Orbit Ground Track")
TRACK_DURATION_MIN    = 100   # ~1 full orbit
TRACK_POINT_INTERVAL  = 60    # seconds between track points


# ═══════════════════════════════════════════════════════════════════════════
#  CelesTrak TLE + SGP4
# ═══════════════════════════════════════════════════════════════════════════

_cached_satrec = None
_tle_fetched_at = 0.0
_tle_epoch_str = ""
_tle_epoch_dt = None
_tle_refresh_interval = 3600.0


def _fetch_tle_celestrak():
    """Primary source: CelesTrak OMM JSON."""
    req = Request(CELESTRAK_URL, headers={
        "Accept": "application/json",
        "User-Agent": "OSHConnect-Python/1.0",
    })
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    if isinstance(data, list) and len(data) > 0:
        omm = data[0]
    else:
        raise RuntimeError(f"Unexpected CelesTrak response: {str(data)[:200]}")

    sat = Satrec()
    sat.sgp4init(
        WGS72, 'i',
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
    epoch_str = omm.get("EPOCH", "unknown")
    return sat, epoch_str


def _fetch_tle_fallback():
    """Fallback source: tle.ivanstanojevic.me (TLE two-line format)."""
    req = Request(FALLBACK_TLE_URL, headers={
        "Accept": "application/json",
        "User-Agent": "OSHConnect-Python/1.0",
    })
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    line1 = data["line1"]
    line2 = data["line2"]
    sat = Satrec.twoline2rv(line1, line2, WGS72)
    epoch_str = data.get("date", "unknown")
    # Normalize to CelesTrak-style epoch format
    if epoch_str != "unknown":
        try:
            dt = datetime.fromisoformat(epoch_str)
            epoch_str = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}"
        except (ValueError, TypeError):
            pass
    return sat, epoch_str


def fetch_tle_from_celestrak():
    global _cached_satrec, _tle_fetched_at, _tle_epoch_str, _tle_epoch_dt

    # Try CelesTrak first, fall back to alternative API
    last_err = None
    for label, fetcher in [("CelesTrak", _fetch_tle_celestrak),
                           ("tle.ivanstanojevic.me", _fetch_tle_fallback)]:
        try:
            sat, epoch_str = fetcher()
            _cached_satrec = sat
            _tle_fetched_at = time.time()
            _tle_epoch_str = epoch_str
            try:
                _tle_epoch_dt = datetime.strptime(
                    _tle_epoch_str, "%Y-%m-%dT%H:%M:%S.%f"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                _tle_epoch_dt = None
            if label != "CelesTrak":
                print(f"  TLE fetched via fallback: {label}")
            return sat
        except Exception as e:
            last_err = e
            print(f"  TLE fetch failed ({label}): {e}")
            continue

    raise RuntimeError(f"All TLE sources failed. Last error: {last_err}")


def _epoch_to_jdsatepoch(epoch_str):
    dt = datetime.strptime(epoch_str, "%Y-%m-%dT%H:%M:%S.%f").replace(
        tzinfo=timezone.utc
    )
    jd, fr = _datetime_to_jd(dt)
    return (jd + fr) - 2433281.5


def get_satrec():
    global _cached_satrec, _tle_fetched_at
    if _cached_satrec is None or (time.time() - _tle_fetched_at) > _tle_refresh_interval:
        fetch_tle_from_celestrak()
    return _cached_satrec


def propagate_to_geodetic(sat, dt):
    jd, fr = _datetime_to_jd(dt)
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        raise RuntimeError(f"SGP4 propagation error code {e}")
    x, y, z = r
    vx, vy, vz = v
    lat, lon, alt = eci_to_geodetic(x, y, z, dt)
    velocity_km_s = math.sqrt(vx**2 + vy**2 + vz**2)
    return lat, lon, alt, velocity_km_s


def _datetime_to_jd(dt):
    y, m = dt.year, dt.month
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


def eci_to_geodetic(x_km, y_km, z_km, dt):
    a_e = 6378.135
    f = 1.0 / 298.26
    gmst = _gmst_rad(dt)
    cos_g, sin_g = math.cos(gmst), math.sin(gmst)
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


def _gmst_rad(dt):
    jd, fr = _datetime_to_jd(dt)
    T = (jd + fr - 2451545.0) / 36525.0
    gmst_sec = (67310.54841 +
                (876600.0 * 3600 + 8640184.812866) * T +
                0.093104 * T**2 - 6.2e-6 * T**3)
    gmst_rad = (gmst_sec % 86400) / 86400.0 * 2 * math.pi
    if gmst_rad < 0:
        gmst_rad += 2 * math.pi
    return gmst_rad


def estimate_position_error_m(tle_age_sec):
    age_days = abs(tle_age_sec) / 86400.0
    return round((1.0 + 1.5 * age_days) * 1000.0, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  Orbit track observation builder
# ═══════════════════════════════════════════════════════════════════════════

def build_orbit_track_observation(sat, now):
    """Build a predicted ground-track observation (~100 points, ~100 min ahead)."""
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
            "computedAt": str(now.timestamp()),
            "noradId": int(NORAD_ID),
            "assetName": ASSET_NAME,
            "durationMin": TRACK_DURATION_MIN,
            "numPoints": len(points),
            "method": "SGP4",
            "trackPointsJson": json.dumps(points, separators=(",", ":")),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  ISS Publisher (extends PublisherBase)
# ═══════════════════════════════════════════════════════════════════════════

class ISSPublisher(PublisherBase):
    name = "ISS Satellite Publisher (Position + Orbit Track)"
    system_uid = os.environ.get(
        "POS_SYSTEM_UID",
        "urn:os4csapi:system:iss-position-publisher:v1",
    )
    ds_name = os.environ.get("POS_DS_NAME", "ISS Position (SGP4)")

    def __init__(self):
        # REST-only mode: bypass OSHConnect SDK when OSH_BASE_URL is set
        self._rest_mode = bool(os.environ.get("OSH_BASE_URL"))
        if self._rest_mode:
            import base64
            self.osh_address = os.environ.get("OSH_ADDRESS", "")
            self.osh_user = os.environ.get("OSH_USER", "")
            self.osh_pass = os.environ.get("OSH_PASS", "")
            self._base_url = os.environ["OSH_BASE_URL"]
            self._is_go_server = "csapi-go" in self._base_url
            self._auth = "Basic " + base64.b64encode(
                f"{self.osh_user}:{self.osh_pass}".encode()
            ).decode()
            self._ds_id = None
            self._track_ds_id = None
            self.stats = {
                "published": 0,
                "track_published": 0,
                "errors": 0,
                "reconnects": 0,
            }
        else:
            super().__init__()
            self._is_go_server = False
            self._track_ds_id = None

        self._enable_track = True
        self._track_interval = 300.0
        self._last_track_time = 0.0  # force track publish on first tick

    def configure_cli(self, parser):
        parser.add_argument(
            "--tle-refresh", type=float, default=3600.0,
            help="Seconds between TLE refreshes (default: 3600)",
        )
        parser.add_argument(
            "--track-interval", type=float, default=300.0,
            help="Seconds between orbit track publications (default: 300)",
        )
        parser.add_argument(
            "--no-track", action="store_true",
            help="Disable orbit track publishing",
        )
        parser.set_defaults(interval=30.0)  # ISS default is 30s, not 60s

    def on_startup(self, args):
        global _tle_refresh_interval
        if hasattr(args, "tle_refresh"):
            _tle_refresh_interval = args.tle_refresh
        if hasattr(args, "track_interval"):
            self._track_interval = args.track_interval
        if hasattr(args, "no_track") and args.no_track:
            self._enable_track = False
        print("  Fetching TLE from CelesTrak...")
        try:
            fetch_tle_from_celestrak()
            print(f"  TLE epoch: {_tle_epoch_str}")
        except Exception as e:
            print(f"  FATAL: Could not fetch TLE: {e}")
            sys.exit(1)

    def connect(self):
        """Connect to server. Uses REST mode when OSH_BASE_URL is set."""
        if self._rest_mode:
            from publishers.bootstrap_helpers import api_get, find_by_uid

            # Position system + datastream
            sys_id = find_by_uid(
                self._base_url, self._auth, "systems", self.system_uid
            )
            if not sys_id:
                raise RuntimeError(
                    f"System '{self.system_uid}' not found on server"
                )

            ds_list = api_get(
                self._base_url,
                f"systems/{sys_id}/datastreams",
                self._auth,
            )
            if ds_list:
                for item in ds_list.get("items", []):
                    if item.get("outputName") == "issPosition":
                        self._ds_id = item.get("id")
                        break
            if not self._ds_id:
                raise RuntimeError(
                    f"Datastream 'issPosition' not found under system {sys_id}"
                )
            print(f"  Connected (REST): pos_sys={sys_id} pos_ds={self._ds_id}")

            # Orbit track system + datastream (optional)
            if self._enable_track:
                track_sys_id = find_by_uid(
                    self._base_url, self._auth, "systems", TRACK_SYSTEM_UID
                )
                if track_sys_id:
                    track_ds_list = api_get(
                        self._base_url,
                        f"systems/{track_sys_id}/datastreams",
                        self._auth,
                    )
                    if track_ds_list:
                        for item in track_ds_list.get("items", []):
                            if item.get("outputName") == "issOrbitTrack":
                                self._track_ds_id = item.get("id")
                                break
                    if self._track_ds_id:
                        print(
                            f"  Connected (REST): track_sys={track_sys_id} "
                            f"track_ds={self._track_ds_id}"
                        )
                    else:
                        print(
                            f"  [WARN] Orbit track datastream 'issOrbitTrack' "
                            f"not found — track disabled"
                        )
                else:
                    print(
                        f"  [WARN] Orbit track system '{TRACK_SYSTEM_UID}' "
                        f"not found — track disabled"
                    )
        else:
            return super().connect()

    def _post_observation(self, ds_id, obs):
        """POST an observation to a specific datastream via REST."""
        import ssl
        url = f"{self._base_url}/datastreams/{ds_id}/observations"

        # Go server workarounds
        if self._is_go_server:
            r = obs.get("result", {})
            # Go server requires all declared schema fields as strings
            for key in ("timestamp", "computedAt"):
                if key in r and not isinstance(r[key], str):
                    r[key] = str(r[key])

        body = json.dumps(obs).encode()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self._auth,
        })
        with urlopen(req, timeout=30, context=ctx) as resp:
            if resp.status not in (200, 201, 204):
                raise RuntimeError(f"HTTP {resp.status}")
        return True

    def publish_obs(self, obs):
        """POST position observation."""
        if self._rest_mode:
            try:
                self._post_observation(self._ds_id, obs)
                self.stats["published"] += 1
                return True
            except Exception:
                self.stats["errors"] += 1
                raise
        else:
            return super().publish_obs(obs)

    def publish_track_obs(self, obs):
        """POST orbit track observation."""
        if self._rest_mode:
            try:
                self._post_observation(self._track_ds_id, obs)
                self.stats["track_published"] += 1
                return True
            except Exception:
                self.stats["errors"] += 1
                raise
        else:
            raise NotImplementedError(
                "Track publishing not supported in SDK mode"
            )

    def fetch(self):
        sat = get_satrec()
        now = datetime.now(timezone.utc)
        lat, lon, alt_km, vel = propagate_to_geodetic(sat, now)
        return {
            "lat": lat,
            "lon": lon,
            "alt_km": alt_km,
            "vel": vel,
            "now": now,
        }

    def build_obs(self, data):
        now = data["now"]
        iso = now.strftime("%Y-%m-%dT%H:%M:%S.") + \
            f"{now.microsecond // 1000:03d}Z"

        tle_age_sec = 0.0
        source_epoch_iso = _tle_epoch_str
        if _tle_epoch_dt is not None:
            tle_age_sec = (now - _tle_epoch_dt).total_seconds()
            source_epoch_iso = _tle_epoch_dt.strftime(
                "%Y-%m-%dT%H:%M:%S."
            ) + f"{_tle_epoch_dt.microsecond // 1000:03d}Z"

        return {
            "phenomenonTime": iso,
            "resultTime": iso,
            "result": {
                "timestamp": str(now.timestamp()),
                "lat_deg": round(data["lat"], 6),
                "lon_deg": round(data["lon"], 6),
                "alt_km": round(data["alt_km"], 3),
                "velocity_km_s": round(data["vel"], 3),
                "noradId": int(NORAD_ID),
                "assetName": ASSET_NAME,
                "sourceEpoch": source_epoch_iso,
                "sourceAgeSec": round(tle_age_sec, 1),
                "posErrorM": estimate_position_error_m(tle_age_sec),
                "method": "SGP4",
            },
        }

    def run(self, *, interval=30.0, dry_run=False, once=False):
        """Main loop: position fixes + orbit tracks on separate cadences."""
        print("=" * 70)
        print(f"  {self.name}")
        print("=" * 70)
        if self._rest_mode:
            print(f"  Server:         {self._base_url}")
        else:
            print(
                f"  Server:         https://{self.osh_address}:"
                f"{self.osh_port}/{self.osh_root}/api"
            )
        print(f"  Position UID:   {self.system_uid}")
        print(f"  Position DS:    {self.ds_name}  (every {interval}s)")
        if self._enable_track:
            print(f"  Track UID:      {TRACK_SYSTEM_UID}")
            print(
                f"  Track DS:       {TRACK_DS_NAME}  "
                f"(every {self._track_interval}s)"
            )
        else:
            print(f"  Track:          DISABLED")
        print(f"  NORAD ID:       {NORAD_ID}")
        print(f"  TLE refresh:    {_tle_refresh_interval}s")
        print(f"  Dry run:        {dry_run}")
        print()

        # Connect
        if not dry_run:
            print("  Connecting to server...")
            if self._rest_mode:
                self.connect()
            else:
                self.connect_with_retry()

        # Startup hook
        self.on_startup(argparse.Namespace(
            interval=interval,
            dry_run=dry_run,
            once=once,
            tle_refresh=_tle_refresh_interval,
            track_interval=self._track_interval,
            no_track=not self._enable_track,
        ))

        tick = 0
        consecutive_errors = 0
        start_time = time.time()

        print()
        try:
            while True:
                now = datetime.now(timezone.utc)
                tick += 1

                # Refresh TLE if stale
                try:
                    sat = get_satrec()
                except Exception as e:
                    print(f"  [WARN] TLE refresh failed (using cached): {e}")
                    sat = _cached_satrec

                # ── Position observation ──────────────────────────────
                try:
                    lat, lon, alt_km, vel = propagate_to_geodetic(sat, now)
                except Exception as e:
                    print(f"  [ERR] Propagation failed: {e}")
                    consecutive_errors += 1
                    if not once:
                        time.sleep(interval)
                    continue

                ts = now.strftime("%H:%M:%S")
                obs = self.build_obs({
                    "lat": lat,
                    "lon": lon,
                    "alt_km": alt_km,
                    "vel": vel,
                    "now": now,
                })

                if dry_run:
                    r = obs["result"]
                    print(
                        f"  [{ts}] #{tick:5d} OK  "
                        f"timestamp={r['timestamp']}, "
                        f"lat_deg={r['lat_deg']}, "
                        f"lon_deg={r['lon_deg']}, "
                        f"alt_km={r['alt_km']}"
                    )
                else:
                    try:
                        self.publish_obs(obs)
                        consecutive_errors = 0
                        r = obs["result"]
                        print(
                            f"  [{ts}] #{tick:5d} OK  "
                            f"timestamp={r['timestamp']}, "
                            f"lat_deg={r['lat_deg']}, "
                            f"lon_deg={r['lon_deg']}, "
                            f"alt_km={r['alt_km']}"
                        )
                    except Exception as e:
                        consecutive_errors += 1
                        print(f"  [{ts}] #{tick:5d} ERR {e}")

                # ── Orbit track observation (less frequent) ───────────
                time_since_track = time.time() - self._last_track_time
                if (
                    self._enable_track
                    and self._track_ds_id
                    and time_since_track >= self._track_interval
                ):
                    n_expect = TRACK_DURATION_MIN * 60 // TRACK_POINT_INTERVAL
                    print(
                        f"           Generating orbit track "
                        f"({TRACK_DURATION_MIN}min, {n_expect} points)..."
                    )
                    track_obs = build_orbit_track_observation(sat, now)
                    n_pts = track_obs["result"]["numPoints"]

                    if dry_run:
                        print(
                            f"           [DRY-TRACK] {n_pts} points, "
                            f"{TRACK_DURATION_MIN}min horizon"
                        )
                    else:
                        try:
                            self.publish_track_obs(track_obs)
                            print(
                                f"           [TRACK] Published "
                                f"{n_pts}-point orbit track"
                            )
                        except Exception as e:
                            print(
                                f"           [ERR] Track publish failed: {e}"
                            )
                    self._last_track_time = time.time()

                # Reconnect if too many errors
                if (
                    consecutive_errors >= self.reconnect_threshold
                    and not dry_run
                ):
                    print(
                        f"  [WARN] {self.reconnect_threshold} consecutive "
                        f"errors, reconnecting..."
                    )
                    try:
                        self.connect()
                        self.stats["reconnects"] += 1
                        consecutive_errors = 0
                    except Exception as re_err:
                        print(f"  [ERR] Reconnect failed: {re_err}")

                if once:
                    break

                # Drift-compensated sleep
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
        print(f"  Position obs:   {self.stats['published']}")
        print(f"  Track obs:      {self.stats.get('track_published', 0)}")
        print(f"  Errors:         {self.stats['errors']}")
        print(f"  Reconnects:     {self.stats['reconnects']}")
        print("=" * 70)

    @classmethod
    def cli(cls):
        """Build CLI parser and run."""
        instance = cls()
        parser = argparse.ArgumentParser(description=instance.name)
        parser.add_argument(
            "--interval", type=float, default=30.0,
            help="Seconds between position observations (default: 30)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Print observations but don't POST them",
        )
        parser.add_argument(
            "--once", action="store_true",
            help="Publish a single cycle then exit",
        )

        # Let subclass add its own args
        instance.configure_cli(parser)

        args = parser.parse_args()

        # Apply track settings before run()
        if hasattr(args, "track_interval"):
            instance._track_interval = args.track_interval
        if hasattr(args, "no_track") and args.no_track:
            instance._enable_track = False

        instance.run(
            interval=args.interval,
            dry_run=args.dry_run,
            once=args.once,
        )


if __name__ == "__main__":
    ISSPublisher.cli()
