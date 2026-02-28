#!/usr/bin/env python3
"""
Reparent AZ-MA-1/2/3 under AZ-MA-NET as subsystems.

Strategy (discovered through testing):
  - DELETE datastream → cascades to observations (204)
  - DELETE system with subsystems → blocked (400)
  - DELETE leaf system (no children) → succeeds (204)

So we delete in order:
  1. Each subsystem's datastreams (cascades to obs) and control streams
  2. Each subsystem (now a leaf)
  3. Parent node's datastreams and control streams
  4. Parent node (now a leaf)
  5. Re-create parent as subsystem of MA-NET
  6. Re-create subsystems under new parent

Usage:
    python reparent_nodes.py [--dry-run]
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# ── Config ────────────────────────────────────────────────────────
BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")

SCRIPT_DIR = Path(__file__).resolve().parent
OSHCONNECT_DIR = SCRIPT_DIR.parent.parent / "OSHConnect-Python"
SCENARIO_DIR = OSHCONNECT_DIR / "scenarios" / "ft-huachuca-v2.3"
RESOURCES_DIR = SCENARIO_DIR / "examples" / "resources"

# AZ-MA-NET server ID
NET_ID = "04n0"

# Nodes to re-parent: (server_id, logical_id)
NODES = [
    ("04ng", "AZ-MA-1"),
    ("04o0", "AZ-MA-2"),
    ("04og", "AZ-MA-3"),
]

# Subsystem logical IDs (same pattern as bootstrap.py)
def get_subsystem_ids(node: str) -> List[str]:
    return [
        f"{node}-PLATFORM",
        f"{node}-MICARRAY",
        f"{node}-EDGE",
        f"{node}-COMMS",
        f"{node}-POWER",
        f"{node}-ACTUATOR",
    ] + [f"{node}-MIC{i}" for i in range(1, 8)]


def convert_valid_time(data: dict) -> dict:
    """Convert validTime from {begin, end} to [begin, '..'] array format."""
    props = data.get("properties", data)
    vt = props.get("validTime")
    if isinstance(vt, dict):
        begin = vt.get("begin", "2026-01-01T00:00:00Z")
        end = vt.get("end")
        props["validTime"] = [begin, ".."] if end is None else [begin, end]
    return data


class Migration:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.auth = AUTH
        self.id_map: Dict[str, str] = {}
        self.backup_dir = SCRIPT_DIR / "migration_backup"
        self.backup_dir.mkdir(exist_ok=True)
        self.stats = {"deleted": 0, "created": 0, "failed": 0, "skipped": 0}

    # ── HTTP helpers ─────────────────────────────────────────────

    def get_json(self, url: str, accept: str = "application/json") -> Optional[dict]:
        r = self.session.get(url, headers={"Accept": accept})
        return r.json() if r.ok else None

    def get_items(self, path: str, limit: int = 200) -> list:
        d = self.get_json(f"{BASE}/{path}?limit={limit}")
        return d.get("items", d.get("features", [])) if d else []

    def delete(self, path: str, label: str = "") -> bool:
        if self.dry_run:
            print(f"    [DRY] DELETE /{path} ({label})")
            self.stats["skipped"] += 1
            return True
        r = self.session.delete(f"{BASE}/{path}")
        if r.status_code in (200, 204):
            self.stats["deleted"] += 1
            return True
        print(f"    ✗ DELETE /{path} → {r.status_code} ({label})")
        self.stats["failed"] += 1
        return False

    def post_resource(self, endpoint: str, data: dict, label: str = "") -> Optional[str]:
        if self.dry_run:
            print(f"    [DRY] POST /{endpoint} ({label})")
            self.stats["skipped"] += 1
            return "dry-run"
        r = self.session.post(
            f"{BASE}/{endpoint}",
            json=data,
            headers={"Content-Type": "application/geo+json"},
        )
        if r.status_code in (200, 201):
            loc = r.headers.get("Location", "")
            server_id = loc.rstrip("/").split("/")[-1] if "/" in loc else ""
            if server_id:
                self.stats["created"] += 1
                return server_id
        elif r.status_code == 409:
            print(f"    ⚠ 409 conflict: {label} — looking up by UID")
            uid = data.get("properties", {}).get("uid", "")
            found = self._find_by_uid("systems", uid)
            if found:
                self.stats["skipped"] += 1
                return found
        print(f"    ✗ POST /{endpoint} → {r.status_code} ({label})")
        print(f"      {r.text[:200]}")
        self.stats["failed"] += 1
        return None

    def _find_by_uid(self, collection: str, uid: str) -> Optional[str]:
        d = self.get_json(f"{BASE}/{collection}?uid={uid}")
        if d:
            items = d.get("items", [])
            if items:
                return items[0].get("id")
        return None

    # ── Export (safety backup) ───────────────────────────────────

    def export_system(self, server_id: str, name: str):
        sml = self.get_json(f"{BASE}/systems/{server_id}?f=sml3", "application/sml+json")
        if sml:
            safe = name.replace(" ", "_").replace("/", "-")
            out = self.backup_dir / f"{safe}_sml.json"
            out.write_text(json.dumps(sml, indent=2), encoding="utf-8")

    # ── Delete a system tree (DS cascades to obs) ────────────────

    def delete_system_tree(self, server_id: str, name: str):
        """
        Delete a system and everything under it.
        Order: subsystem DS/CS → subsystems → own DS/CS → self.
        DS delete cascades to observations automatically.
        """
        print(f"\n  ── Deleting {name} ({server_id}) tree ──")

        # Get subsystems
        subs = self.get_items(f"systems/{server_id}/subsystems")
        if subs:
            print(f"    {len(subs)} subsystems to delete...")
            for sub in subs:
                sub_id = sub.get("id", "")
                sub_name = sub.get("properties", {}).get("name", sub_id)
                # Delete sub's datastreams (cascades to observations)
                sub_ds = self.get_items(f"systems/{sub_id}/datastreams")
                for ds in sub_ds:
                    self.delete(f"datastreams/{ds['id']}", f"DS:{ds.get('name','?')}")
                # Delete sub's control streams
                sub_cs = self.get_items(f"systems/{sub_id}/controlstreams")
                for cs in sub_cs:
                    self.delete(f"controlstreams/{cs['id']}", f"CS:{cs.get('name','?')}")
                # Delete the subsystem itself (now a leaf)
                self.delete(f"systems/{sub_id}", f"SUB:{sub_name}")

        # Delete own datastreams (cascades to observations)
        own_ds = self.get_items(f"systems/{server_id}/datastreams")
        if own_ds:
            print(f"    {len(own_ds)} own datastreams...")
            for ds in own_ds:
                self.delete(f"datastreams/{ds['id']}", f"DS:{ds.get('name','?')}")

        # Delete own control streams
        own_cs = self.get_items(f"systems/{server_id}/controlstreams")
        if own_cs:
            print(f"    {len(own_cs)} own control streams...")
            for cs in own_cs:
                self.delete(f"controlstreams/{cs['id']}", f"CS:{cs.get('name','?')}")

        # Delete the system itself (now a leaf)
        self.delete(f"systems/{server_id}", f"SYS:{name}")

    # ── Re-create under AZ-MA-NET ────────────────────────────────

    def recreate_node(self, logical_id: str) -> Optional[str]:
        f = RESOURCES_DIR / "systems" / f"{logical_id}.geojson"
        if not f.exists():
            print(f"    ✗ Source not found: {f}")
            return None
        data = json.loads(f.read_text(encoding="utf-8"))
        data = convert_valid_time(data)
        data.pop("id", None)
        server_id = self.post_resource(f"systems/{NET_ID}/subsystems", data, logical_id)
        if server_id:
            self.id_map[logical_id] = server_id
            print(f"    ✓ {logical_id} → {server_id}")
        return server_id

    def recreate_subsystems(self, parent_logical: str, parent_server: str):
        sub_ids = get_subsystem_ids(parent_logical)
        for sub_id in sub_ids:
            f = RESOURCES_DIR / "systems" / f"{sub_id}.geojson"
            if not f.exists():
                print(f"      ✗ Missing: {f.name}")
                self.stats["failed"] += 1
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            data = convert_valid_time(data)
            data.pop("id", None)
            server_id = self.post_resource(f"systems/{parent_server}/subsystems", data, sub_id)
            if server_id:
                self.id_map[sub_id] = server_id
                print(f"      ✓ {sub_id} → {server_id}")

    # ── Main ─────────────────────────────────────────────────────

    def run(self):
        print("=" * 60)
        print("ODAS Hierarchy Migration")
        print("Re-parent AZ-MA-1/2/3 → subsystems of AZ-MA-NET")
        print("=" * 60)
        if self.dry_run:
            print(">>> DRY RUN — no changes <<<\n")

        # Verify AZ-MA-NET
        net = self.get_json(f"{BASE}/systems/{NET_ID}", "application/geo+json")
        if not net:
            print(f"ABORT: AZ-MA-NET ({NET_ID}) not found!")
            return
        print(f"✓ AZ-MA-NET ({NET_ID}): {net.get('properties',{}).get('name','?')}\n")

        # ── Step 1: Backup SML ──
        print("Step 1: Exporting SML backups...")
        for server_id, name in NODES:
            self.export_system(server_id, name)
            subs = self.get_items(f"systems/{server_id}/subsystems")
            for sub in subs:
                sub_id = sub.get("id", "")
                sub_name = sub.get("properties", {}).get("name", sub_id)
                self.export_system(sub_id, sub_name.replace(" ", "_"))
        print(f"  Saved to: {self.backup_dir}")

        # ── Step 2: Delete trees ──
        print("\nStep 2: Delete system trees (DS→obs cascade)...")
        for server_id, name in NODES:
            self.delete_system_tree(server_id, name)

        # ── Step 3: Re-create under MA-NET ──
        print("\n\nStep 3: Re-create nodes under AZ-MA-NET...")
        for _, logical_id in NODES:
            self.recreate_node(logical_id)

        # ── Step 4: Re-create subsystems ──
        print("\nStep 4: Re-create subsystems...")
        for _, logical_id in NODES:
            parent_server = self.id_map.get(logical_id)
            if not parent_server:
                print(f"  ✗ Skipping {logical_id} subsystems — parent not created")
                continue
            print(f"\n  {logical_id} ({parent_server}):")
            self.recreate_subsystems(logical_id, parent_server)

        # ── Save ID map ──
        id_map_out = self.backup_dir / "new_id_map.json"
        with open(id_map_out, "w") as f:
            json.dump(self.id_map, f, indent=2)
        print(f"\n  ID map: {id_map_out}")

        # ── Verify ──
        if not self.dry_run:
            print("\nStep 5: Verification...")
            subs = self.get_items(f"systems/{NET_ID}/subsystems")
            sub_names = [s.get("properties", {}).get("name", "?") for s in subs]
            print(f"  AZ-MA-NET now has {len(subs)} subsystems: {sub_names}")
            for _, logical_id in NODES:
                sid = self.id_map.get(logical_id)
                if sid:
                    child_subs = self.get_items(f"systems/{sid}/subsystems")
                    print(f"  {logical_id} ({sid}): {len(child_subs)} subsystems")

        # ── Summary ──
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Deleted:  {self.stats['deleted']}")
        print(f"  Created:  {self.stats['created']}")
        print(f"  Failed:   {self.stats['failed']}")
        print(f"  Skipped:  {self.stats['skipped']}")

        if self.stats["failed"] == 0:
            print("\n✓ Migration successful!")
            print("\nNext steps:")
            print("  1. Run Phase 2 bootstrap (datastreams + control streams)")
            print("  2. Run enrich_systems.py (descriptions)")
            print("  3. Run enrich_sensorml.py (metadata)")
            print("  4. Run replay.py (observations)")
        else:
            print(f"\n⚠ {self.stats['failed']} failures — review above")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    Migration(dry_run=args.dry_run).run()
