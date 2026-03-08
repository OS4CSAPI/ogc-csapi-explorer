#!/usr/bin/env python3
"""Verify all UAS pack templates were correctly transformed."""
import json
import os

d = os.path.join(os.path.dirname(__file__), "..", "docs", "uas-localizer-senrep-pack", "09_JSON_TEMPLATES")
d = os.path.abspath(d)

print("=== Verification: UAS Pack Template Transformation ===")
print(f"Dir: {d}")
print()

ok = 0
fail = 0

def check(label, condition, detail=""):
    global ok, fail
    if condition:
        print(f"  PASS  {label}")
        ok += 1
    else:
        print(f"  FAIL  {label}  {detail}")
        fail += 1

# U2: Datastream timestamp fields
for f in ["datastream_location_estimate.json", "datastream_senrep_v1_1.json"]:
    print(f"\n--- {f} ---")
    data = json.load(open(os.path.join(d, f)))
    ts = data["schema"]["resultSchema"]["fields"][0]
    check("timestamp.type == Time", ts["type"] == "Time")
    check("timestamp has definition", "definition" in ts, "CRITICAL: U2 not fixed!")
    check("definition is sensorml.com SamplingTime",
          ts.get("definition") == "http://sensorml.com/ont/swe/property/SamplingTime")
    check("timestamp has referenceTime", "referenceTime" in ts, "CRITICAL: U2 not fixed!")
    check("referenceTime is 1970 epoch", ts.get("referenceTime") == "1970-01-01T00:00:00Z")
    check("has obsFormat", "obsFormat" in data["schema"])
    fcount = len(data["schema"]["resultSchema"]["fields"])
    if "location" in f:
        check(f"field count == 10 (got {fcount})", fcount == 10)
    else:
        check(f"field count == 25 (got {fcount})", fcount == 25)

# U1: System templates
for f in ["system_localizer_enriched.json", "system_set_a_enriched.json",
          "system_monitoring_site_enriched.json", "system_relay_enriched.json"]:
    print(f"\n--- {f} ---")
    data = json.load(open(os.path.join(d, f)))
    check("has geojsonStub", "geojsonStub" in data)
    check("has sensorml", "sensorml" in data)
    stub = data.get("geojsonStub", {})
    sml = data.get("sensorml", {})
    check("stub type == Feature", stub.get("type") == "Feature")
    check("stub has uid", "uid" in stub.get("properties", {}))
    check("sml type == PhysicalSystem", sml.get("type") == "PhysicalSystem")
    check("sml has uniqueId", "uniqueId" in sml)
    check("sml has keywords", len(sml.get("keywords", [])) > 0)
    check("sml has identifiers", len(sml.get("identifiers", [])) > 0)
    check("sml has classifiers", len(sml.get("classifiers", [])) > 0)

# U1: Procedure templates
for f in ["procedure_lob_wls_triangulation_v1.json", "procedure_senrep_sop_v1.json"]:
    print(f"\n--- {f} ---")
    data = json.load(open(os.path.join(d, f)))
    check("type == Feature", data.get("type") == "Feature")
    check("has geometry", "geometry" in data)
    props = data.get("properties", {})
    check("has uid", "uid" in props)
    check("has featureType", "featureType" in props)
    check("featureType == sosa:ObservingProcedure",
          props.get("featureType") == "sosa:ObservingProcedure")
    check("_originalMetadata preserved", "_originalMetadata" in props)
    om = props.get("_originalMetadata", {})
    check("inputs preserved", len(om.get("inputs", [])) > 0)
    check("outputs preserved", len(om.get("outputs", [])) > 0)
    check("assumptions preserved", len(om.get("assumptions", [])) > 0)
    check("documents preserved", len(om.get("documents", [])) > 0)

# U1: Deployment templates
for f in ["deployment_localizer_feed_leaf.json", "deployment_relay_emplacement_enriched.json"]:
    print(f"\n--- {f} ---")
    data = json.load(open(os.path.join(d, f)))
    check("type == Feature", data.get("type") == "Feature")
    check("has uid", "uid" in data.get("properties", {}))
    check("has platform@link", "platform@link" in data.get("properties", {}))
    href = data["properties"]["platform@link"]["href"]
    check("platform@link has RUNTIME_RESOLVE prefix", href.startswith("RUNTIME_RESOLVE:"))
    check("_originalMetadata preserved", "_originalMetadata" in data.get("properties", {}))

# U6: SVG paths
print(f"\n--- SVG URL check (U6) ---")
for f in ["system_localizer_enriched.json", "system_set_a_enriched.json"]:
    content = open(os.path.join(d, f)).read()
    has_relative = "../14_DIAGRAMS" in content
    has_absolute = "raw.githubusercontent.com" in content
    check(f"{f}: no relative SVG paths", not has_relative, "Still has ../14_DIAGRAMS!")
    check(f"{f}: has absolute GitHub URL", has_absolute)

for f in ["procedure_lob_wls_triangulation_v1.json", "procedure_senrep_sop_v1.json"]:
    content = open(os.path.join(d, f)).read()
    has_relative = "../14_DIAGRAMS" in content
    has_absolute = "raw.githubusercontent.com" in content
    check(f"{f}: no relative SVG paths", not has_relative)
    check(f"{f}: has absolute GitHub URL", has_absolute)

# U4: Relay templates exist
print(f"\n--- U4: Relay templates ---")
relay_sys = os.path.join(d, "system_relay_enriched.json")
relay_dep = os.path.join(d, "deployment_relay_emplacement_enriched.json")
check("system_relay_enriched.json exists", os.path.exists(relay_sys))
check("deployment_relay_emplacement_enriched.json exists", os.path.exists(relay_dep))
# Verify relay system uses correct UID from Relay Patch Pack
data = json.load(open(relay_sys))
check("relay UID = urn:os4csapi:system:relay:ft-huachuca:001",
      data["sensorml"]["uniqueId"] == "urn:os4csapi:system:relay:ft-huachuca:001")
# Verify relay has capabilities (from patch pack)
check("relay sensorml has capabilities", len(data["sensorml"].get("capabilities", [])) > 0)
# Verify relay has manufacturer/model/assetTag identifiers
ids = [i["label"] for i in data["sensorml"].get("identifiers", [])]
check("relay has Manufacturer identifier", "Manufacturer" in ids)
check("relay has Model identifier", "Model" in ids)
check("relay has Asset Tag identifier", "Asset Tag" in ids)

# File count
print(f"\n--- File inventory ---")
files = sorted(os.listdir(d))
print(f"  Total: {len(files)} files (was 12, now 15 with relay system + relay deployment)")
for f in files:
    sz = os.path.getsize(os.path.join(d, f))
    print(f"  {f:50s} {sz:6d} bytes")

# Summary
print(f"\n{'=' * 60}")
print(f"Results: {ok} passed, {fail} failed")
if fail == 0:
    print("ALL CHECKS PASSED — templates are server-ready.")
else:
    print(f"WARNING: {fail} checks failed — review above!")
