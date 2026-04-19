#!/usr/bin/env python
"""One-shot: create the missing ISS deployment hierarchy on the Go CSAPI server.

OSH has a 4-level deployment tree under "Orbital Tracking Demo":
  Orbital Tracking Demo (root, exists on Go)
    └─ LEO Objects
       └─ ISS Tracking Role
          ├─ ISS Position Feed       (platform@link → ISS Position Publisher)
          └─ ISS Orbit Track Feed    (platform@link → ISS Orbit Track Publisher)

Go only had the root. Without the leaf deployments (which carry platform@link),
the Explorer cannot render the "ISS deployed system" marker on the map.

This script POSTs the 3 missing children. Idempotent — skips by UID.
"""
from __future__ import annotations
import json
import sys
import urllib.request
import urllib.error
import ssl

GO_BASE = "https://129-80-248-53.sslip.io/csapi-go"
ROOT_DEPLOYMENT_UID = "urn:os4csapi:deployment:orbital-tracking-demo:v1"
SYS_POS_UID = "urn:os4csapi:system:iss-position-publisher:v1"
SYS_TRACK_UID = "urn:os4csapi:system:iss-orbittrack-publisher:v1"
VALID_TIME = ["2026-01-01T00:00:00Z", ".."]

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def http(method: str, path: str, body: dict | None = None,
         content_type: str = "application/json") -> tuple[int, dict | None]:
    url = f"{GO_BASE}/{path.lstrip('/')}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            raw = r.read().decode() or "null"
            return r.status, json.loads(raw) if raw and raw != "null" else None
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None


def find_deployment_id_by_uid(uid: str, search_root: bool = True,
                              parent_id: str | None = None) -> str | None:
    """Find a deployment by uid — top-level or under a specific parent."""
    if parent_id is None:
        path = "deployments?limit=200"
    else:
        path = f"deployments/{parent_id}/subdeployments?limit=200"
    st, d = http("GET", path)
    if st != 200 or not d:
        return None
    for it in d.get("items", d.get("features", [])):
        u = it.get("properties", {}).get("uid") or it.get("uid")
        if u == uid:
            return it.get("id")
    return None


def find_system_id_by_uid(uid: str) -> str | None:
    st, d = http("GET", "systems?limit=200")
    if st != 200 or not d:
        return None
    for it in d.get("items", d.get("features", [])):
        u = it.get("properties", {}).get("uid") or it.get("uid")
        if u == uid:
            return it.get("id")
    return None


def make_deployment(uid: str, name: str, description: str,
                    platform_link: dict | None = None) -> dict:
    props = {
        "uid": uid,
        "featureType": "sosa:Deployment",
        "name": name,
        "description": description,
        "validTime": VALID_TIME,
        "definition": "sosa:Deployment",
    }
    if platform_link is not None:
        props["platform@link"] = platform_link
    return {
        "type": "Feature",
        "geometry": None,
        "properties": props,
    }


def create_subdeployment(parent_id: str, body: dict, label: str) -> str | None:
    uid = body["properties"]["uid"]
    existing = find_deployment_id_by_uid(uid, parent_id=parent_id)
    if existing:
        print(f"  SKIP {label} — already exists ({existing})")
        return existing
    st, d = http("POST", f"deployments/{parent_id}/subdeployments", body,
                 content_type="application/geo+json")
    if st in (200, 201):
        new_id = (d or {}).get("id") if isinstance(d, dict) else None
        if not new_id:
            # Go returns 201 with empty body + Location header; refetch by uid
            new_id = find_deployment_id_by_uid(uid, parent_id=parent_id)
        if new_id:
            print(f"  CREATED {label} → id={new_id}")
            return new_id
    print(f"  ERROR creating {label}: status={st} body={d}")
    return None


def main() -> int:
    print(f"Connecting to {GO_BASE}\n")

    root_id = find_deployment_id_by_uid(ROOT_DEPLOYMENT_UID)
    if not root_id:
        print(f"FATAL: root deployment {ROOT_DEPLOYMENT_UID} not found on Go")
        return 1
    print(f"Root  : Orbital Tracking Demo  id={root_id}")

    sys_pos_id = find_system_id_by_uid(SYS_POS_UID)
    sys_trk_id = find_system_id_by_uid(SYS_TRACK_UID)
    if not sys_pos_id or not sys_trk_id:
        print(f"FATAL: missing system(s).  pos={sys_pos_id}  track={sys_trk_id}")
        return 1
    print(f"System: ISS Position Publisher    id={sys_pos_id}")
    print(f"System: ISS Orbit Track Publisher id={sys_trk_id}\n")

    print("Creating LEO Objects under root...")
    leo_id = create_subdeployment(root_id, make_deployment(
        "urn:os4csapi:deployment:leo-objects:v1",
        "LEO Objects",
        "Grouping node for Low Earth Orbit tracked objects.",
    ), "LEO Objects")
    if not leo_id:
        return 2

    print("Creating ISS Tracking Role under LEO Objects...")
    role_id = create_subdeployment(leo_id, make_deployment(
        "urn:os4csapi:deployment:iss-tracking-role:v1",
        "ISS Tracking Role",
        "Operational role branch for ISS (NORAD 25544 / ZARYA) tracking products including position feeds and orbit-track predictions.",
    ), "ISS Tracking Role")
    if not role_id:
        return 3

    print("Creating ISS Position Feed leaf (platform@link → ISS Position Publisher)...")
    pos_feed_id = create_subdeployment(role_id, make_deployment(
        "urn:os4csapi:deployment:iss-position-feed:v1",
        "ISS Position Feed",
        "Leaf deployment linking the ISS Position Publisher system to the tracking hierarchy.",
        platform_link={
            "href": f"systems/{sys_pos_id}",
            "title": "ISS Position Publisher",
            "uid": SYS_POS_UID,
            "type": "application/sml+json",
        },
    ), "ISS Position Feed")

    print("Creating ISS Orbit Track Feed leaf (platform@link → ISS Orbit Track Publisher)...")
    trk_feed_id = create_subdeployment(role_id, make_deployment(
        "urn:os4csapi:deployment:iss-orbittrack-feed:v1",
        "ISS Orbit Track Feed",
        "Leaf deployment linking the ISS Orbit Track Publisher system to the tracking hierarchy.",
        platform_link={
            "href": f"systems/{sys_trk_id}",
            "title": "ISS Orbit Track Publisher",
            "uid": SYS_TRACK_UID,
            "type": "application/sml+json",
        },
    ), "ISS Orbit Track Feed")

    print("\nDone.")
    print(f"  LEO Objects        : {leo_id}")
    print(f"  ISS Tracking Role  : {role_id}")
    print(f"  ISS Position Feed  : {pos_feed_id}")
    print(f"  ISS Orbit Track Feed: {trk_feed_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
