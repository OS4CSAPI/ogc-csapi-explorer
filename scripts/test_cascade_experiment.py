#!/usr/bin/env python3
"""
Full experiment: OSH SensorHub DELETE ?cascade behavior.

Creates an isolated hierarchy of disposable test resources, then systematically
tests every combination of DELETE with/without the cascade parameter.

SAFETY: All resources use a unique 'urn:test:cascade-exp-2026:*' namespace
and are cleaned up at the end. No existing demo data is touched.

Experiment matrix:
  T1 — DELETE leaf system (no children, no cascade param)        → expect 204
  T2 — DELETE parent with children (no cascade param)            → expect 400/409
  T3 — DELETE parent with children (?cascade=false)              → expect 400/409
  T4 — DELETE parent with children (?cascade=true)               → expect 204 if supported
  T5 — DELETE system with datastream (no cascade param)          → expect 400/409
  T6 — DELETE system with datastream (?cascade=true)             → expect 204 if supported
  T7 — DELETE system with DS+obs+CS+subsystem (?cascade=true)   → full tree test
"""
import json
import sys
import time
import requests
from datetime import datetime, timezone

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
SML_CT = {"Content-Type": "application/sml+json", "Accept": "application/json"}
GEO_CT = {"Content-Type": "application/json", "Accept": "application/json"}

NS = "urn:test:cascade-exp-2026"
CREATED_IDS = []  # track for cleanup

# ── Helpers ──────────────────────────────────────────────────────

def ordered_sml(d: dict) -> str:
    """Ensure 'type' is the first JSON key (OSH requirement)."""
    ordered = {}
    if "type" in d:
        ordered["type"] = d["type"]
    for k, v in d.items():
        if k != "type":
            ordered[k] = v
    return json.dumps(ordered)


def create_system(uid_suffix: str, label: str, parent_id: str | None = None) -> str | None:
    """Create a system, optionally as subsystem. Returns server ID or None."""
    sml = {
        "type": "PhysicalSystem",
        "uniqueId": f"{NS}:{uid_suffix}",
        "label": label,
        "definition": "http://www.w3.org/ns/ssn/System",
    }
    endpoint = f"{BASE}/systems"
    if parent_id:
        endpoint = f"{BASE}/systems/{parent_id}/subsystems"
    r = requests.post(endpoint, data=ordered_sml(sml), headers=SML_CT, auth=AUTH, allow_redirects=False)
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        sid = loc.rstrip("/").split("/")[-1] if "/" in loc else ""
        if sid:
            CREATED_IDS.append(("systems", sid))
            return sid
    print(f"    ⚠ Create system '{label}' → {r.status_code}: {r.text[:200]}")
    return None


def create_datastream(system_id: str, uid_suffix: str, label: str) -> str | None:
    """Create a minimal datastream. Returns server ID or None."""
    ds = {
        "name": label,
        "outputName": "test-output",
        "schema": {
            "obsFormat": "application/json",
            "recordSchema": {
                "type": "DataRecord",
                "label": label,
                "fields": [
                    {
                        "type": "Time",
                        "name": "timestamp",
                        "label": "Timestamp",
                        "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
                        "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC",
                        "uom": {"href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"},
                    },
                    {
                        "type": "Quantity",
                        "name": "value",
                        "label": "Value",
                        "definition": "http://qudt.org/vocab/quantitykind/Temperature",
                        "uom": {"code": "Cel"},
                    },
                ],
            },
        },
    }
    r = requests.post(
        f"{BASE}/systems/{system_id}/datastreams",
        json=ds,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        auth=AUTH,
    )
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        sid = loc.rstrip("/").split("/")[-1] if "/" in loc else ""
        if sid:
            CREATED_IDS.append(("datastreams", sid))
            return sid
    print(f"    ⚠ Create DS '{label}' → {r.status_code}: {r.text[:200]}")
    return None


def create_controlstream(system_id: str, label: str) -> str | None:
    """Create a minimal control stream. Returns server ID or None."""
    cs = {
        "name": label,
        "inputName": "test-command",
        "schema": {
            "commandFormat": "application/json",
            "recordSchema": {
                "type": "DataRecord",
                "label": label,
                "fields": [
                    {
                        "type": "Time",
                        "name": "timestamp",
                        "label": "Timestamp",
                        "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
                        "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC",
                        "uom": {"href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"},
                    },
                    {
                        "type": "Text",
                        "name": "mode",
                        "label": "Mode",
                        "definition": "http://www.opengis.net/def/property/OGC/0/OperationMode",
                    },
                ],
            },
        },
    }
    r = requests.post(
        f"{BASE}/systems/{system_id}/controlstreams",
        json=cs,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        auth=AUTH,
    )
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        sid = loc.rstrip("/").split("/")[-1] if "/" in loc else ""
        if sid:
            CREATED_IDS.append(("controlstreams", sid))
            return sid
    print(f"    ⚠ Create CS '{label}' → {r.status_code}: {r.text[:200]}")
    return None


def post_observation(ds_id: str) -> bool:
    """Post a single observation to a datastream."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    obs = {
        "timestamp": now,
        "value": 22.5,
    }
    r = requests.post(
        f"{BASE}/datastreams/{ds_id}/observations",
        json=obs,
        headers={"Content-Type": "application/json"},
        auth=AUTH,
    )
    return r.status_code in (200, 201, 204)


def exists(resource_type: str, resource_id: str) -> bool:
    """Check if a resource still exists."""
    r = requests.get(f"{BASE}/{resource_type}/{resource_id}", auth=AUTH, headers={"Accept": "application/json"})
    return r.status_code == 200


def count_items(path: str) -> int:
    """Count items at a collection endpoint."""
    r = requests.get(f"{BASE}/{path}?limit=100", auth=AUTH, headers={"Accept": "application/json"})
    if r.status_code != 200:
        return -1
    data = r.json()
    items = data.get("items", data.get("features", []))
    return len(items)


def do_delete(resource_type: str, resource_id: str, cascade: str | None = None) -> int:
    """DELETE a resource with optional cascade parameter. Returns HTTP status."""
    url = f"{BASE}/{resource_type}/{resource_id}"
    params = {}
    if cascade is not None:
        params["cascade"] = cascade
    r = requests.delete(url, auth=AUTH, params=params)
    return r.status_code


def cleanup():
    """Best-effort cleanup of all created resources (reverse order)."""
    print("\n🧹 Cleanup...")
    # Delete in reverse order (children before parents)
    for rtype, rid in reversed(CREATED_IDS):
        try:
            # Try cascade first, then plain
            r = requests.delete(f"{BASE}/{rtype}/{rid}", auth=AUTH, params={"cascade": "true"})
            if r.status_code not in (200, 204, 404):
                requests.delete(f"{BASE}/{rtype}/{rid}", auth=AUTH)
        except Exception:
            pass
    print("  Done.")


# ── Test Functions ───────────────────────────────────────────────

def test_1_delete_leaf():
    """T1: DELETE a leaf system with no children, no cascade param."""
    print("\n━━━ T1: DELETE leaf system (no children, no cascade param) ━━━")
    sid = create_system("t1-leaf", "CASCADE-TEST-T1-LEAF")
    if not sid:
        return {"test": "T1", "status": "SETUP_FAIL"}
    assert exists("systems", sid), "System should exist after creation"
    status = do_delete("systems", sid, cascade=None)
    still_exists = exists("systems", sid)
    result = {
        "test": "T1",
        "description": "DELETE leaf system (no children, no cascade param)",
        "http_status": status,
        "resource_deleted": not still_exists,
        "expected_status": "200 or 204",
        "pass": status in (200, 204) and not still_exists,
    }
    print(f"  → HTTP {status}, deleted={not still_exists}  {'✅ PASS' if result['pass'] else '❌ FAIL'}")
    return result


def test_2_delete_parent_no_param():
    """T2: DELETE parent with children, no cascade param."""
    print("\n━━━ T2: DELETE parent+child (no cascade param) ━━━")
    parent = create_system("t2-parent", "CASCADE-TEST-T2-PARENT")
    if not parent:
        return {"test": "T2", "status": "SETUP_FAIL"}
    child = create_system("t2-child", "CASCADE-TEST-T2-CHILD", parent_id=parent)
    if not child:
        return {"test": "T2", "status": "SETUP_FAIL"}
    status = do_delete("systems", parent, cascade=None)
    parent_alive = exists("systems", parent)
    child_alive = exists("systems", child)
    result = {
        "test": "T2",
        "description": "DELETE parent with child (no cascade param)",
        "http_status": status,
        "parent_survived": parent_alive,
        "child_survived": child_alive,
        "expected_status": "400 or 409 (rejected)",
        "pass": status in (400, 409) and parent_alive and child_alive,
    }
    print(f"  → HTTP {status}, parent_alive={parent_alive}, child_alive={child_alive}  {'✅ PASS' if result['pass'] else '⚠️ UNEXPECTED'}")
    # Cleanup for next test
    do_delete("systems", child, cascade=None)
    do_delete("systems", parent, cascade=None)
    return result


def test_3_delete_parent_cascade_false():
    """T3: DELETE parent with children, ?cascade=false."""
    print("\n━━━ T3: DELETE parent+child (?cascade=false) ━━━")
    parent = create_system("t3-parent", "CASCADE-TEST-T3-PARENT")
    if not parent:
        return {"test": "T3", "status": "SETUP_FAIL"}
    child = create_system("t3-child", "CASCADE-TEST-T3-CHILD", parent_id=parent)
    if not child:
        return {"test": "T3", "status": "SETUP_FAIL"}
    status = do_delete("systems", parent, cascade="false")
    parent_alive = exists("systems", parent)
    child_alive = exists("systems", child)
    result = {
        "test": "T3",
        "description": "DELETE parent with child (?cascade=false)",
        "http_status": status,
        "parent_survived": parent_alive,
        "child_survived": child_alive,
        "expected_status": "400 or 409 (rejected)",
        "pass": status in (400, 409) and parent_alive and child_alive,
    }
    print(f"  → HTTP {status}, parent_alive={parent_alive}, child_alive={child_alive}  {'✅ PASS' if result['pass'] else '⚠️ UNEXPECTED'}")
    do_delete("systems", child, cascade=None)
    do_delete("systems", parent, cascade=None)
    return result


def test_4_delete_parent_cascade_true():
    """T4: DELETE parent with children, ?cascade=true (THE KEY TEST)."""
    print("\n━━━ T4: DELETE parent+child (?cascade=true) — KEY TEST ━━━")
    parent = create_system("t4-parent", "CASCADE-TEST-T4-PARENT")
    if not parent:
        return {"test": "T4", "status": "SETUP_FAIL"}
    child = create_system("t4-child", "CASCADE-TEST-T4-CHILD", parent_id=parent)
    if not child:
        return {"test": "T4", "status": "SETUP_FAIL"}
    status = do_delete("systems", parent, cascade="true")
    parent_alive = exists("systems", parent)
    child_alive = exists("systems", child)
    cascade_worked = status in (200, 204) and not parent_alive and not child_alive
    result = {
        "test": "T4",
        "description": "DELETE parent with child (?cascade=true)",
        "http_status": status,
        "parent_deleted": not parent_alive,
        "child_deleted": not child_alive,
        "cascade_supported": cascade_worked,
        "expected_status": "200 or 204 if cascade supported; 400/409 if not",
        "pass": cascade_worked,
    }
    emoji = "✅ CASCADE WORKS" if cascade_worked else "❌ CASCADE NOT SUPPORTED"
    print(f"  → HTTP {status}, parent_deleted={not parent_alive}, child_deleted={not child_alive}  {emoji}")
    # Cleanup in case cascade didn't work
    if child_alive:
        do_delete("systems", child, cascade=None)
    if parent_alive:
        do_delete("systems", parent, cascade=None)
    return result


def test_5_delete_system_with_ds_no_param():
    """T5: DELETE system that has a datastream (no cascade param)."""
    print("\n━━━ T5: DELETE system with datastream (no cascade param) ━━━")
    sys_id = create_system("t5-sys", "CASCADE-TEST-T5-SYS")
    if not sys_id:
        return {"test": "T5", "status": "SETUP_FAIL"}
    ds_id = create_datastream(sys_id, "t5-ds", "CASCADE-TEST-T5-DS")
    if not ds_id:
        return {"test": "T5", "status": "SETUP_FAIL"}
    status = do_delete("systems", sys_id, cascade=None)
    sys_alive = exists("systems", sys_id)
    ds_alive = exists("datastreams", ds_id)
    result = {
        "test": "T5",
        "description": "DELETE system with datastream (no cascade param)",
        "http_status": status,
        "system_survived": sys_alive,
        "datastream_survived": ds_alive,
        "expected_status": "400 or 409 (rejected — system has nested resources)",
        "pass": status in (400, 409) and sys_alive and ds_alive,
    }
    print(f"  → HTTP {status}, sys_alive={sys_alive}, ds_alive={ds_alive}  {'✅ PASS' if result['pass'] else '⚠️ UNEXPECTED'}")
    if ds_alive:
        do_delete("datastreams", ds_id, cascade=None)
    if sys_alive:
        do_delete("systems", sys_id, cascade=None)
    return result


def test_6_delete_system_with_ds_cascade_true():
    """T6: DELETE system with datastream, ?cascade=true."""
    print("\n━━━ T6: DELETE system+datastream (?cascade=true) ━━━")
    sys_id = create_system("t6-sys", "CASCADE-TEST-T6-SYS")
    if not sys_id:
        return {"test": "T6", "status": "SETUP_FAIL"}
    ds_id = create_datastream(sys_id, "t6-ds", "CASCADE-TEST-T6-DS")
    if not ds_id:
        return {"test": "T6", "status": "SETUP_FAIL"}
    status = do_delete("systems", sys_id, cascade="true")
    sys_alive = exists("systems", sys_id)
    ds_alive = exists("datastreams", ds_id)
    cascade_worked = status in (200, 204) and not sys_alive and not ds_alive
    result = {
        "test": "T6",
        "description": "DELETE system with datastream (?cascade=true)",
        "http_status": status,
        "system_deleted": not sys_alive,
        "datastream_deleted": not ds_alive,
        "cascade_supported": cascade_worked,
        "pass": cascade_worked,
    }
    emoji = "✅ CASCADE WORKS" if cascade_worked else "❌ CASCADE NOT SUPPORTED"
    print(f"  → HTTP {status}, sys_deleted={not sys_alive}, ds_deleted={not ds_alive}  {emoji}")
    if ds_alive:
        do_delete("datastreams", ds_id, cascade=None)
    if sys_alive:
        do_delete("systems", sys_id, cascade=None)
    return result


def test_7_full_tree_cascade():
    """T7: Full tree — parent + subsystem + DS + observation + CS, ?cascade=true."""
    print("\n━━━ T7: Full tree cascade (?cascade=true) — COMPREHENSIVE ━━━")
    parent = create_system("t7-parent", "CASCADE-TEST-T7-PARENT")
    if not parent:
        return {"test": "T7", "status": "SETUP_FAIL"}

    child = create_system("t7-child", "CASCADE-TEST-T7-CHILD", parent_id=parent)
    if not child:
        return {"test": "T7", "status": "SETUP_FAIL"}

    grandchild = create_system("t7-grandchild", "CASCADE-TEST-T7-GRANDCHILD", parent_id=child)

    ds_parent = create_datastream(parent, "t7-ds-p", "CASCADE-TEST-T7-DS-PARENT")
    ds_child = create_datastream(child, "t7-ds-c", "CASCADE-TEST-T7-DS-CHILD")

    cs_parent = create_controlstream(parent, "CASCADE-TEST-T7-CS-PARENT")

    # Post a couple observations
    obs_posted = 0
    if ds_child:
        for _ in range(3):
            if post_observation(ds_child):
                obs_posted += 1
            time.sleep(0.1)

    print(f"  Setup: parent={parent}, child={child}, grandchild={grandchild}")
    print(f"         ds_parent={ds_parent}, ds_child={ds_child}, cs_parent={cs_parent}")
    print(f"         observations posted: {obs_posted}")

    # Count observations before delete
    obs_before = count_items(f"datastreams/{ds_child}/observations") if ds_child else 0
    print(f"         observations in DS before delete: {obs_before}")

    # THE BIG DELETE
    status = do_delete("systems", parent, cascade="true")
    time.sleep(0.5)  # give server a moment

    # Verify everything
    checks = {
        "parent": exists("systems", parent),
        "child": exists("systems", child),
    }
    if grandchild:
        checks["grandchild"] = exists("systems", grandchild)
    if ds_parent:
        checks["ds_parent"] = exists("datastreams", ds_parent)
    if ds_child:
        checks["ds_child"] = exists("datastreams", ds_child)
    if cs_parent:
        checks["cs_parent"] = exists("controlstreams", cs_parent)

    all_gone = all(alive == False for alive in checks.values())
    cascade_worked = status in (200, 204) and all_gone

    result = {
        "test": "T7",
        "description": "Full tree: parent + child + grandchild + 2DS + obs + CS (?cascade=true)",
        "http_status": status,
        "resources_after_delete": {k: "ALIVE" if v else "DELETED" for k, v in checks.items()},
        "all_deleted": all_gone,
        "cascade_supported": cascade_worked,
        "obs_posted_before": obs_posted,
        "pass": cascade_worked,
    }

    if cascade_worked:
        print(f"  → HTTP {status}  ✅ FULL CASCADE WORKS — all {len(checks)} resources deleted!")
    else:
        print(f"  → HTTP {status}")
        for k, v in checks.items():
            print(f"    {k}: {'ALIVE ⚠️' if v else 'DELETED ✅'}")
        if not all_gone:
            print("  ❌ CASCADE DID NOT FULLY DELETE THE TREE")

    # Cleanup survivors
    for rtype_id in [(grandchild, "systems"), (ds_child, "datastreams"),
                      (ds_parent, "datastreams"), (cs_parent, "controlstreams"),
                      (child, "systems"), (parent, "systems")]:
        rid, rtype = rtype_id
        if rid and exists(rtype, rid):
            do_delete(rtype, rid, cascade=None)

    return result


def test_8_delete_parent_cascade_true_param_variations():
    """T8: Test different parameter forms for cascade."""
    print("\n━━━ T8: Parameter format variations ━━━")
    results = []
    
    for i, (param_value, desc) in enumerate([
        ("true", "cascade=true (string)"),
        ("TRUE", "cascade=TRUE (uppercase)"),
        ("1", "cascade=1 (numeric)"),
    ]):
        suffix = f"t8-{i}"
        parent = create_system(f"{suffix}-parent", f"CASCADE-TEST-T8-{i}-PARENT")
        if not parent:
            results.append({"variant": desc, "status": "SETUP_FAIL"})
            continue
        child = create_system(f"{suffix}-child", f"CASCADE-TEST-T8-{i}-CHILD", parent_id=parent)
        if not child:
            results.append({"variant": desc, "status": "SETUP_FAIL"})
            do_delete("systems", parent)
            continue

        status = do_delete("systems", parent, cascade=param_value)
        p_alive = exists("systems", parent)
        c_alive = exists("systems", child)
        worked = status in (200, 204) and not p_alive and not c_alive

        results.append({"variant": desc, "http_status": status, "cascade_worked": worked})
        print(f"  {desc}: HTTP {status}, worked={worked}  {'✅' if worked else '❌'}")

        if c_alive:
            do_delete("systems", child)
        if p_alive:
            do_delete("systems", parent)

    return {"test": "T8", "description": "Parameter format variations", "variants": results}


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  OSH SensorHub — CASCADE DELETE Experiment")
    print(f"  Server: {BASE}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Namespace: {NS}")
    print("=" * 70)

    # Sanity check: verify server is reachable
    try:
        r = requests.get(f"{BASE}/systems?limit=1", auth=AUTH, headers={"Accept": "application/json"}, timeout=10)
        print(f"\n✓ Server reachable (HTTP {r.status_code})")
    except Exception as e:
        print(f"\n✗ Server unreachable: {e}")
        sys.exit(1)

    all_results = []

    try:
        all_results.append(test_1_delete_leaf())
        all_results.append(test_2_delete_parent_no_param())
        all_results.append(test_3_delete_parent_cascade_false())
        all_results.append(test_4_delete_parent_cascade_true())
        all_results.append(test_5_delete_system_with_ds_no_param())
        all_results.append(test_6_delete_system_with_ds_cascade_true())
        all_results.append(test_7_full_tree_cascade())
        all_results.append(test_8_delete_parent_cascade_true_param_variations())
    except Exception as e:
        print(f"\n💥 Experiment error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  EXPERIMENT SUMMARY")
    print("=" * 70)

    cascade_supported = None
    for r in all_results:
        if r.get("test") in ("T4", "T6", "T7"):
            if r.get("cascade_supported") is True:
                cascade_supported = True
            elif r.get("cascade_supported") is False and cascade_supported is None:
                cascade_supported = False

    for r in all_results:
        test_id = r.get("test", "?")
        desc = r.get("description", "")
        passed = r.get("pass", r.get("status") == "SETUP_FAIL")
        status = r.get("http_status", r.get("status", "?"))
        icon = "✅" if passed else ("⚠️" if r.get("status") == "SETUP_FAIL" else "❌")
        print(f"  {icon} {test_id}: {desc}  [HTTP {status}]")

    print()
    if cascade_supported is True:
        print("  🎉 CONCLUSION: ?cascade=true IS SUPPORTED by this OSH server!")
        print("     Future migrations can use a single DELETE ?cascade=true instead")
        print("     of manual bottom-up deletion.")
    elif cascade_supported is False:
        print("  ❌ CONCLUSION: ?cascade=true is NOT SUPPORTED by this OSH server.")
        print("     The manual bottom-up deletion strategy remains necessary.")
    else:
        print("  ⚠️  CONCLUSION: Could not determine cascade support (setup failures).")

    # Write JSON results
    out_file = "scripts/cascade_experiment_results.json"
    with open(out_file, "w") as f:
        json.dump({"timestamp": datetime.now(timezone.utc).isoformat(), "server": BASE, "results": all_results, "cascade_supported": cascade_supported}, f, indent=2)
    print(f"\n  Results written to: {out_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
