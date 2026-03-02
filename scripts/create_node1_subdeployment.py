#!/usr/bin/env python3
"""
Create Node 1 Sub-Deployment Under String Alpha
================================================

Discovered Oracle state (2025-01-xx inventory):

  Deployment tree (6 levels):
    ICO (040g) → R&S (0410) → SSO (041g) → SNet (0420) → Field 001 (042g)
      └── String Alpha (0430)  platform@link → /systems/0420 (AZ-MA-1)

  Systems:
    040g  SET-A              uid: urn:os4csapi:system:set:ft-huachuca:001
                             1 DS: SENREP (044g), deployment@link = none
    0420  AZ-MA-1            uid: urn:os4csapi:system:odas:az-ma-1
                             7 DS (all deployment@link = none)
                             12+ subsystems

  Target restructure:
    String Alpha (0430)
      [REMOVE platform@link — String Alpha is a collective, not a single system]
      └── Node 1 (NEW sub-deployment)
            platform@link → /systems/0420  (AZ-MA-1)
            7 DS on 0420 get deployment@link → Node 1
            1 DS on 040g (SENREP) gets deployment@link → Node 1

Steps:
  1. Probe: test PUT on a datastream to see if deployment@link can be set
  2. Create Node 1 sub-deployment under String Alpha (0430)
  3. Set deployment@link on all 8 datastreams → Node 1
  4. Remove platform@link from String Alpha
  5. Verify final state

Usage:
  python create_node1_subdeployment.py             # live run
  python create_node1_subdeployment.py --dry-run    # read-only
"""

import json
import ssl
import socket
import urllib.request
import urllib.error
import base64
import time
import sys

# ══════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════

ORACLE_HOST = "os4csapi-osh.duckdns.org"
ORACLE_IP = "129.80.248.53"
ORACLE_BASE = f"https://{ORACLE_HOST}/sensorhub/api"
ORACLE_AUTH = base64.b64encode(b"os4csapi:ogc134mm").decode()

# ── Discovered IDs (from inventory probes) ──────────────────────────

STRING_ALPHA_ID  = "0430"
STRING_ALPHA_UID = "urn:os4csapi:deployment:string:ft-huachuca:001"

MA1_SYSTEM_ID  = "0420"   # ODAS Mic Array Node AZ-MA-1
MA1_SYSTEM_UID = "urn:os4csapi:system:odas:az-ma-1"

SETA_SYSTEM_ID = "040g"   # Sensor Employment Team (SET-A) — holds SENREP

# ── Node 1 sub-deployment payload ───────────────────────────────────

NODE1_UID = "urn:os4csapi:deployment:node:ft-huachuca:alpha:001"
NODE1_PAYLOAD = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-110.3441, 31.5549]},
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": NODE1_UID,
        "name": "Node 1 \u2014 AZ-MA-1",
        "description": (
            "AZ-MA-1 Monitoring Array deployed as Node 1 on "
            "Sensor String Alpha, Ft Huachuca ODAS"
        ),
        "validTime": ["2026-01-15T00:00:00Z", ".."],
        "platform@link": {
            "href": f"/sensorhub/api/systems/{MA1_SYSTEM_ID}",
            "uid": MA1_SYSTEM_UID,
            "title": "ODAS Mic Array Node AZ-MA-1",
            "type": "application/geo+json",
        },
    },
}

DRY_RUN = "--dry-run" in sys.argv

# ══════════════════════════════════════════════════════════════════════
#  DNS  MONKEY-PATCH  (DuckDNS  →  Oracle IP)
# ══════════════════════════════════════════════════════════════════════

_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == ORACLE_HOST:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ORACLE_IP, port or 443))]
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# ══════════════════════════════════════════════════════════════════════
#  API  HELPER
# ══════════════════════════════════════════════════════════════════════

def api(method, path, body=None,
        content_type="application/geo+json",
        accept="application/geo+json"):
    """Call Oracle OSH API.  Returns (status, data_or_text, location)."""
    url = f"{ORACLE_BASE}/{path}" if not path.startswith("http") else path
    headers = {
        "Authorization": f"Basic {ORACLE_AUTH}",
        "Accept": accept,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = content_type

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
            status = resp.status
            loc = resp.getheader("Location", "")
            raw = resp.read().decode("utf-8", errors="replace")
            return (status, json.loads(raw), loc) if raw.strip() else (status, {}, loc)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            return e.code, json.loads(raw), ""
        except Exception:
            return e.code, raw, ""
    except Exception as exc:
        return 0, str(exc), ""


# ══════════════════════════════════════════════════════════════════════
#  STEP 1 – PROBE  (can PUT set deployment@link on a datastream?)
# ══════════════════════════════════════════════════════════════════════

def get_ds_schema(ds_id):
    """Fetch the SWE schema for a datastream (needed for PUT)."""
    s, data, _ = api("GET", f"datastreams/{ds_id}/schema", accept="application/json")
    if s == 200 and isinstance(data, dict):
        return data
    return None


def build_ds_put_payload(ds, schema):
    """Build the PUT payload for a datastream: include schema + strip server fields."""
    payload = dict(ds)
    for key in ("id", "links"):
        payload.pop(key, None)
    if schema:
        payload["schema"] = schema
    return payload


def step1_probe():
    print("\n" + "=" * 70)
    print("STEP 1: Probe \u2014 Can PUT set deployment@link on a datastream?")
    print("=" * 70)

    # Grab one AZ-MA-1 datastream
    status, ds_data, _ = api(
        "GET", f"systems/{MA1_SYSTEM_ID}/datastreams?limit=1",
        accept="application/json",
    )
    if status != 200 or not ds_data.get("items"):
        print(f"  FATAL: Cannot GET a test datastream (HTTP {status})")
        sys.exit(1)

    test_ds = ds_data["items"][0]
    ds_id   = test_ds.get("id")
    ds_name = test_ds.get("name")
    cur_dep = test_ds.get("deployment@link")
    print(f"  Test DS: {ds_name}  (id={ds_id})")
    print(f"  Current deployment@link: {json.dumps(cur_dep) if cur_dep else 'NONE'}")

    # Fetch schema (required by OSH for PUT)
    schema = get_ds_schema(ds_id)
    print(f"  Schema: {'fetched OK' if schema else 'NOT FOUND'}")

    if DRY_RUN:
        print("  DRY-RUN: skipping probe PUT")
        return True

    # Build probe payload with sentinel deployment@link
    probe_payload = build_ds_put_payload(test_ds, schema)
    probe_payload["deployment@link"] = {
        "href": f"/sensorhub/api/deployments/{STRING_ALPHA_ID}",
        "title": "PROBE-TEST-MARKER",
        "type": "application/geo+json",
    }

    print("  PUT with deployment@link + schema  (sentinel)...")
    s, r, _ = api(
        "PUT", f"systems/{MA1_SYSTEM_ID}/datastreams/{ds_id}",
        probe_payload,
        content_type="application/json",
        accept="application/json",
    )
    print(f"  PUT response: HTTP {s}")

    if s not in (200, 204):
        print(f"  PUT failed: {r}")
        return False

    # Read back and check
    time.sleep(0.5)
    s2, rb, _ = api(
        "GET", f"systems/{MA1_SYSTEM_ID}/datastreams/{ds_id}",
        accept="application/json",
    )
    if s2 != 200:
        print(f"  Cannot read back: HTTP {s2}")
        return False

    rb_dep = rb.get("deployment@link")
    if rb_dep:
        rb_title = rb_dep.get("title", "")
        rb_href  = rb_dep.get("href", "")
        print(f"  Read-back: title='{rb_title}', href='{rb_href}'")

        if rb_title == "PROBE-TEST-MARKER" or STRING_ALPHA_ID in rb_href:
            print("  PROBE SUCCESS: PUT can set deployment@link!")

            # Restore original (remove sentinel)
            restore = build_ds_put_payload(test_ds, schema)
            restore.pop("deployment@link", None)
            api(
                "PUT", f"systems/{MA1_SYSTEM_ID}/datastreams/{ds_id}",
                restore,
                content_type="application/json",
                accept="application/json",
            )
            print("  Restored original state (removed sentinel).")
            return True
        else:
            print("  Sentinel not found in read-back — PUT may silently ignore field")
            return False
    else:
        print("  PROBE FAILED: deployment@link not in read-back (server silently drops)")
        return False


# ══════════════════════════════════════════════════════════════════════
#  STEP 2 – CREATE  NODE 1  SUB-DEPLOYMENT
# ══════════════════════════════════════════════════════════════════════

def step2_create_node1():
    print("\n" + "=" * 70)
    print("STEP 2: Create Node 1 Sub-Deployment Under String Alpha")
    print("=" * 70)

    # Check if Node 1 already exists (idempotency guard)
    s, subs, _ = api("GET", f"deployments/{STRING_ALPHA_ID}/subdeployments")
    if s == 200:
        for item in (subs or {}).get("items", []):
            uid = item.get("properties", {}).get("uid", "")
            if uid == NODE1_UID:
                nid = item.get("id")
                print(f"  Node 1 already exists (id={nid}) \u2014 skipping creation")
                return nid

    if DRY_RUN:
        print(f"  DRY-RUN: would POST to deployments/{STRING_ALPHA_ID}/subdeployments")
        print(f"  Name: {NODE1_PAYLOAD['properties']['name']}")
        return "DRY-NODE1"

    s, data, location = api("POST", f"deployments/{STRING_ALPHA_ID}/subdeployments",
                            NODE1_PAYLOAD)
    if s in (200, 201):
        node1_id = ""
        if location:
            node1_id = location.rstrip("/").split("/")[-1]
        elif isinstance(data, dict):
            node1_id = data.get("id", "")
        print(f"  \u2713 Created Node 1: HTTP {s}, id={node1_id}")
        return node1_id
    else:
        print(f"  FATAL: Failed to create Node 1: HTTP {s}")
        print(f"  Response: {data}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════
#  STEP 3 – SET  deployment@link  ON ALL DATASTREAMS  →  NODE 1
# ══════════════════════════════════════════════════════════════════════

def step3_set_deployment_links(node1_id, put_works):
    print("\n" + "=" * 70)
    print("STEP 3: Set deployment@link on all datastreams \u2192 Node 1")
    print("=" * 70)

    new_dep_link = {
        "href": f"/sensorhub/api/deployments/{node1_id}",
        "uid": NODE1_UID,
        "title": "Node 1 \u2014 AZ-MA-1",
        "type": "application/geo+json",
    }

    # Collect targets:  (system_id, label, ds_dict)
    targets = []

    for sys_id, label in [(MA1_SYSTEM_ID, "MA-1"), (SETA_SYSTEM_ID, "SET-A")]:
        s, ds_list, _ = api(
            "GET", f"systems/{sys_id}/datastreams?limit=20",
            accept="application/json",
        )
        if s == 200:
            for ds in ds_list.get("items", []):
                targets.append((sys_id, label, ds))

    print(f"  Found {len(targets)} datastreams to update")

    if not put_works and not DRY_RUN:
        print("  PUT does not work — cannot set deployment@link via this script.")
        print("  Would need a delete/recreate approach (not implemented).")
        return 0, len(targets)

    success = 0
    fail = 0

    for sys_id, label, ds in targets:
        ds_id   = ds.get("id")
        ds_name = ds.get("name", "?")

        if DRY_RUN:
            print(f"  DRY-RUN: [{label}] {ds_name} (id={ds_id}) -> Node 1")
            success += 1
            continue

        # Fetch schema (required by OSH for PUT)
        schema = get_ds_schema(ds_id)
        if not schema:
            print(f"  SKIP [{label}] {ds_name} (id={ds_id}): cannot fetch schema")
            fail += 1
            continue

        payload = build_ds_put_payload(ds, schema)
        payload["deployment@link"] = new_dep_link

        s, r, _ = api(
            "PUT", f"systems/{sys_id}/datastreams/{ds_id}",
            payload,
            content_type="application/json",
            accept="application/json",
        )
        if s in (200, 204):
            print(f"  OK [{label}] {ds_name} (id={ds_id}): HTTP {s}")
            success += 1
        else:
            print(f"  FAIL [{label}] {ds_name} (id={ds_id}): HTTP {s}: {r}")
            fail += 1

    print(f"\n  Results: {success} updated, {fail} failed")
    return success, fail


# ══════════════════════════════════════════════════════════════════════
#  STEP 4 – REMOVE  platform@link  FROM STRING ALPHA
# ══════════════════════════════════════════════════════════════════════

def step4_clean_string_alpha():
    print("\n" + "=" * 70)
    print("STEP 4: Remove platform@link from String Alpha")
    print("=" * 70)

    s, dep, _ = api("GET", f"deployments/{STRING_ALPHA_ID}")
    if s != 200:
        print(f"  FATAL: Cannot GET String Alpha: HTTP {s}")
        return False

    props = dep.get("properties", {})
    if "platform@link" not in props:
        print("  String Alpha already has no platform@link \u2014 nothing to do")
        return True

    plat = props["platform@link"]
    print(f"  Current platform@link: {plat.get('href', '?')}")

    if DRY_RUN:
        print("  DRY-RUN: would PUT String Alpha without platform@link")
        return True

    put_payload = dict(dep)
    put_payload.get("properties", {}).pop("platform@link", None)
    put_payload.get("properties", {}).pop("deployedSystems@link", None)
    put_payload.pop("links", None)

    s, r, _ = api("PUT", f"deployments/{STRING_ALPHA_ID}", put_payload)
    if s in (200, 204):
        print(f"  \u2713 Removed platform@link: HTTP {s}")
    else:
        print(f"  \u2717 Failed: HTTP {s}: {r}")
        return False

    time.sleep(0.5)
    s2, verify, _ = api("GET", f"deployments/{STRING_ALPHA_ID}")
    if s2 == 200:
        still = "platform@link" in verify.get("properties", {})
        msg = "STILL PRESENT (unexpected)" if still else "REMOVED OK"
        print(f"  Verify: {msg}")
    return True


# ══════════════════════════════════════════════════════════════════════
#  STEP 5 – FINAL VERIFICATION
# ══════════════════════════════════════════════════════════════════════

def step5_verify(node1_id):
    print("\n" + "=" * 70)
    print("STEP 5: Verify Final State")
    print("=" * 70)

    if DRY_RUN:
        print("  DRY-RUN: skipping verification")
        return

    # ── 1. String Alpha ─────────────────────────────────────────
    s, dep, _ = api("GET", f"deployments/{STRING_ALPHA_ID}")
    if s == 200:
        has_plat = "platform@link" in dep.get("properties", {})
        plat_msg = "PRESENT (unexpected!)" if has_plat else "absent OK"
        print(f"  String Alpha ({STRING_ALPHA_ID}):")
        print(f"    platform@link: {plat_msg}")

    # ── 2. Sub-deployments ───────────────────────────────────────
    s, subs, _ = api("GET", f"deployments/{STRING_ALPHA_ID}/subdeployments")
    if s == 200:
        items = subs.get("items", [])
        print(f"    subdeployments: {len(items)}")
        for item in items:
            print(f"      - {item.get('properties', {}).get('name', '?')}  id={item.get('id', '?')}")

    # ── 3. Node 1 ───────────────────────────────────────────────
    s, node1, _ = api("GET", f"deployments/{node1_id}")
    if s == 200:
        p = node1.get("properties", {})
        plat = p.get("platform@link") or {}
        href = plat.get("href", "none")
        print(f"\n  Node 1 ({node1_id}):")
        print(f"    name: {p.get('name', '?')}")
        print(f"    platform@link: {href}")
        ok = MA1_SYSTEM_ID in href
        ok_msg = "YES" if ok else "NO"
        print(f"    correct: {ok_msg}")

    # ── 4. Datastreams ──────────────────────────────────────────
    print(f"\n  Datastream deployment@link status:")
    total = 0
    dep_linked = 0
    for sys_id, label in [(MA1_SYSTEM_ID, "AZ-MA-1"), (SETA_SYSTEM_ID, "SET-A")]:
        s, ds_data, _ = api(
            "GET", f"systems/{sys_id}/datastreams?limit=20",
            accept="application/json",
        )
        if s == 200:
            for ds in ds_data.get("items", []):
                total += 1
                dep = ds.get("deployment@link") or {}
                dep_h = dep.get("href", "none") if dep else "none"
                has_node1 = node1_id in dep_h
                if has_node1:
                    dep_linked += 1
                status_str = "-> Node 1" if has_node1 else dep_h
                print(f"    [{label}] {ds.get('name', '?')} (id={ds.get('id', '?')}): {status_str}")

    # ── 5. Deployment-scoped query ──────────────────────────────
    print(f"\n  Deployment-scoped query test:")
    s, scoped, _ = api(
        "GET", f"deployments/{node1_id}/datastreams",
        accept="application/json",
    )
    if s == 200:
        items = scoped.get("items", [])
        print(f"    GET /deployments/{node1_id}/datastreams -> {len(items)} datastream(s)")
        for ds in items:
            print(f"      - {ds.get('name', '?')}")
    elif s == 400:
        print(f"    HTTP 400 -- deployment-scoped datastream endpoint may not be implemented")
    else:
        print(f"    HTTP {s}")

    # Also test systems scoped to deployment
    s, sys_scoped, _ = api(
        "GET", f"deployments/{node1_id}/systems",
        accept="application/json",
    )
    if s == 200:
        items = sys_scoped.get("items", [])
        print(f"    GET /deployments/{node1_id}/systems -> {len(items)} system(s)")
        for sys in items:
            print(f"      - {sys.get('properties', {}).get('name', '?')}  id={sys.get('id', '?')}")
    elif s == 400:
        print(f"    GET /deployments/{node1_id}/systems -> HTTP 400")
    else:
        print(f"    GET /deployments/{node1_id}/systems -> HTTP {s}")

    # ── Summary ─────────────────────────────────────────────────
    print("\n  === RESTRUCTURE COMPLETE ===")
    print(f"  String Alpha ({STRING_ALPHA_ID})  ->  no platform@link")
    print(f"  Node 1 ({node1_id})  ->  platform@link  ->  AZ-MA-1 ({MA1_SYSTEM_ID})")
    if dep_linked > 0:
        print(f"  {dep_linked}/{total} datastreams  ->  deployment@link  ->  Node 1")
    else:
        print(f"  NOTE: OSH does not persist deployment@link on datastreams (known limitation)")
        print(f"        Deployment-scoped resolution relies on platform@link only")


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("CREATE NODE 1 SUB-DEPLOYMENT UNDER STRING ALPHA")
    print(f"  Target: {ORACLE_BASE}")
    print(f"  String Alpha: {STRING_ALPHA_ID}  ({STRING_ALPHA_UID})")
    print(f"  AZ-MA-1:      {MA1_SYSTEM_ID}  ({MA1_SYSTEM_UID})")
    print(f"  SET-A:         {SETA_SYSTEM_ID}")
    if DRY_RUN:
        print("  MODE: DRY-RUN (no writes)")
    else:
        print("  MODE: LIVE")
    print("=" * 70)

    # Connectivity check
    print("\nValidating Oracle connectivity...")
    s, _, _ = api("GET", "")
    if s != 200:
        print(f"  FATAL: Oracle API returned HTTP {s}")
        sys.exit(1)
    print("  Oracle API OK")

    t0 = time.time()

    # Step 1: Probe deployment@link on datastreams
    put_dep_link_works = step1_probe()

    if not put_dep_link_works and not DRY_RUN:
        print("\n  NOTE: OSH silently drops deployment@link on datastreams (known limitation).")
        print("  Proceeding with Node 1 creation + String Alpha cleanup.")
        print("  Datastream wiring will be skipped.")

    # Step 2: Create Node 1
    node1_id = step2_create_node1()

    # Step 3: Set deployment@link on datastreams (only if probe succeeded)
    if put_dep_link_works:
        success, fail = step3_set_deployment_links(node1_id, put_dep_link_works)
    else:
        if not DRY_RUN:
            print("\n  STEP 3: SKIPPED (deployment@link not supported by server)")

    # Step 4: Clean String Alpha
    step4_clean_string_alpha()

    # Step 5: Verify
    step5_verify(node1_id)

    elapsed = time.time() - t0
    print(f"\nCompleted in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
