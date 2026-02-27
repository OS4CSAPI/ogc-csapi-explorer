"""Fix the 3 Tripod systems that are incorrectly registered at the top level.

They should only exist as subsystems under their respective AZ-MA-X nodes.
Strategy:
  1. Save each tripod's SensorML definition
  2. Check for nested resources (DS, CS, subsystems)
  3. Delete from server (cascade if needed)
  4. Recreate as subsystem ONLY (POST to /systems/{parentId}/subsystems)
  5. Verify they're gone from top-level but present as subsystems
"""
import requests
import json
import sys

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
SML_H = {"Accept": "application/sml+json"}
GEO_H = {"Accept": "application/geo+json"}
SML_CT = {"Content-Type": "application/sml+json", "Accept": "application/json"}

# The 3 tripods and their correct parents
TRIPODS = [
    {"id": "04p0", "parent_id": "04ng", "parent_name": "AZ-MA-1"},
    {"id": "04vg", "parent_id": "04o0", "parent_name": "AZ-MA-2"},
    {"id": "0560", "parent_id": "04og", "parent_name": "AZ-MA-3"},
]


def ordered_sml(d: dict) -> str:
    """Ensure 'type' is the first JSON key (OSH requirement)."""
    ordered = {}
    if "type" in d:
        ordered["type"] = d["type"]
    for k, v in d.items():
        if k != "type":
            ordered[k] = v
    return json.dumps(ordered)


def check_nested(system_id):
    """Check if a system has any nested resources."""
    results = {}
    for rel in ["subsystems", "datastreams", "controlstreams"]:
        r = requests.get(f"{BASE}/systems/{system_id}/{rel}?limit=1",
                         auth=AUTH, headers=GEO_H)
        if r.ok:
            items = r.json().get("items", r.json().get("features", []))
            results[rel] = len(items)
        else:
            results[rel] = 0
    return results


def main():
    print("=" * 60)
    print("  Fix Tripod Top-Level Registration")
    print("=" * 60)

    # Phase 1: Inspect
    print("\n── Phase 1: Inspect ──")
    saved = []
    for tripod in TRIPODS:
        tid = tripod["id"]
        pid = tripod["parent_id"]

        # Get SensorML
        r = requests.get(f"{BASE}/systems/{tid}?f=sml3", auth=AUTH, headers=SML_H)
        if not r.ok:
            print(f"  ✗ Cannot fetch SML for {tid}: HTTP {r.status_code}")
            sys.exit(1)
        sml = r.json()
        name = sml.get("label", tid)

        # Check nested
        nested = check_nested(tid)

        # Verify it IS a subsystem under the expected parent
        r2 = requests.get(f"{BASE}/systems/{pid}/subsystems?limit=100",
                          auth=AUTH, headers=GEO_H)
        sub_ids = [s.get("id") for s in r2.json().get("items", r2.json().get("features", []))]
        is_sub = tid in sub_ids

        print(f"  {tid} = {name}")
        print(f"    nested: {nested}")
        print(f"    is subsystem of {pid} ({tripod['parent_name']}): {is_sub}")

        saved.append({
            **tripod,
            "name": name,
            "sml": sml,
            "nested": nested,
            "is_sub": is_sub,
        })

    # Safety check
    for s in saved:
        if not s["is_sub"]:
            print(f"\n  ✗ ABORT: {s['id']} is NOT a subsystem of {s['parent_id']}!")
            print("    Cannot safely delete — it might not be recreatable.")
            sys.exit(1)
        if s["nested"]["subsystems"] > 0:
            print(f"\n  ⚠ {s['id']} has subsystems — will need cascade delete")

    # Phase 2: Delete from server
    print("\n── Phase 2: Delete ──")
    for s in saved:
        tid = s["id"]
        has_nested = any(v > 0 for v in s["nested"].values())
        params = {"cascade": "true"} if has_nested else {}

        r = requests.delete(f"{BASE}/systems/{tid}", auth=AUTH, params=params)
        print(f"  DELETE /systems/{tid} {'?cascade=true ' if has_nested else ''}: HTTP {r.status_code}")
        if r.status_code not in (200, 204):
            print(f"    ✗ Delete failed! Response: {r.text[:200]}")
            print("    ABORT — remaining tripods not deleted.")
            sys.exit(1)

    # Phase 3: Recreate as subsystem only
    print("\n── Phase 3: Recreate as subsystems ──")
    for s in saved:
        pid = s["parent_id"]
        sml = s["sml"]

        # Remove server-generated fields
        for key in ["id", "links", "@id"]:
            sml.pop(key, None)

        r = requests.post(
            f"{BASE}/systems/{pid}/subsystems",
            data=ordered_sml(sml),
            headers=SML_CT,
            auth=AUTH,
            allow_redirects=False,
        )
        loc = r.headers.get("Location", "")
        new_id = loc.rstrip("/").split("/")[-1] if "/" in loc else ""

        if r.status_code in (200, 201):
            print(f"  POST /systems/{pid}/subsystems: HTTP {r.status_code} → new ID: {new_id}")
        elif r.status_code == 302:
            # Redirect means the uniqueId already exists (it was re-registered)
            print(f"  POST /systems/{pid}/subsystems: HTTP 302 (already exists at {new_id})")
        else:
            print(f"  ✗ Recreate failed: HTTP {r.status_code}: {r.text[:200]}")
            continue

        s["new_id"] = new_id

    # Phase 4: Verify
    print("\n── Phase 4: Verify ──")

    # Check top-level systems
    r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=GEO_H)
    top_ids = set()
    for it in r.json().get("items", r.json().get("features", [])):
        top_ids.add(it.get("id"))

    all_good = True
    for s in saved:
        old_id = s["id"]
        new_id = s.get("new_id", "?")
        pid = s["parent_id"]
        name = s["name"]

        # Should NOT be in top-level
        old_in_top = old_id in top_ids
        new_in_top = new_id in top_ids

        # Should be in parent's subsystems
        r2 = requests.get(f"{BASE}/systems/{pid}/subsystems?limit=100",
                          auth=AUTH, headers=GEO_H)
        sub_ids = [it.get("id") for it in r2.json().get("items", r2.json().get("features", []))]
        is_sub = new_id in sub_ids

        status = "✅" if (not old_in_top and not new_in_top and is_sub) else "❌"
        if old_in_top or new_in_top or not is_sub:
            all_good = False

        print(f"  {status} {name} (was {old_id}, now {new_id})")
        print(f"      old ID in top-level: {old_in_top}")
        print(f"      new ID in top-level: {new_in_top}")
        print(f"      is subsystem of {pid}: {is_sub}")

    print()
    if all_good:
        print("  🎉 All 3 tripods fixed — removed from top-level, subsystem-only now.")
    else:
        print("  ⚠ Some issues remain — check above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
