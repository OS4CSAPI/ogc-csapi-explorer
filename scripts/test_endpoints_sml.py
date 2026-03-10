#!/usr/bin/env python3
"""Supplemental: fetch SML3 format for system & deployment to find richer link fields."""

import json
import urllib.request
import urllib.error
import ssl

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = "Basic b3M0Y3NhcGk6b2djMTM0bW0="
ctx = ssl.create_default_context()

def fetch(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={
        "Authorization": AUTH,
        "Accept": "application/json"
    })
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        body = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(body)
        except:
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return f"ERR:{e}", None

# Get system 0520 in SML3 format
print("=== System 0520 SML3 format ===")
s, data = fetch("/systems/0520?f=sml3")
print(f"Status: {s}")
if data:
    print(json.dumps(data, indent=2)[:3000])

print("\n\n=== Deployment 04ng SML3 format ===")
s, data = fetch("/deployments/04ng?f=sml3")
print(f"Status: {s}")
if data:
    print(json.dumps(data, indent=2)[:3000])

print("\n\n=== Procedure 049g SML3 format ===")
s, data = fetch("/procedures/049g?f=sml3")
print(f"Status: {s}")
if data:
    print(json.dumps(data, indent=2)[:3000])

# Also check deployment leaf detail for deployedSystems
print("\n\n=== Deployment 04ng JSON detail (all fields) ===")
s, data = fetch("/deployments/04ng")
print(f"Status: {s}")
if data:
    print(json.dumps(data, indent=2)[:3000])

# Check 400 error messages
print("\n\n=== Error details ===")
for path in ["/systems/0520/deployments?limit=5", "/systems/0520/procedures?limit=5",
             "/deployments/04mg/systems?limit=5", "/procedures/049g/systems?limit=5"]:
    s, data = fetch(path)
    err_msg = ""
    if isinstance(data, dict):
        err_msg = data.get("message", "") or data.get("error", "") or str(data)[:200]
    elif isinstance(data, str):
        err_msg = data[:200]
    print(f"  {s}  {path}  =>  {err_msg}")
