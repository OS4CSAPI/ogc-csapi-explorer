#!/usr/bin/env python3
"""Quick verification of the 3 new deployment nodes."""
import json, base64, socket, ssl
from urllib.request import Request, urlopen

ORACLE_IP = "129.80.248.53"
_real = socket.getaddrinfo
socket.getaddrinfo = lambda h, p, *a, **k: _real(ORACLE_IP, p, *a, **k) if h == "os4csapi-osh.duckdns.org" else _real(h, p, *a, **k)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cred = base64.b64encode(b"os4csapi:ogc134mm").decode()
BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"

def get(path):
    req = Request(f"{BASE}/{path}", headers={"Authorization": f"Basic {cred}", "Accept": "application/json"})
    with urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read().decode())

uids = [
    "urn:os4csapi:deployment:set:ft-huachuca:001",
    "urn:os4csapi:deployment:monsite:ft-huachuca:001",
    "urn:os4csapi:deployment:relay:ft-huachuca:001",
]

for uid in uids:
    result = get(f"deployments?uid={uid}")
    items = result.get("items", [])
    if items:
        d = items[0]
        props = d.get("properties", {})
        plat = props.get("platform@link", {})
        name = props.get("name", "?")
        did = d.get("id", "?")
        ptitle = plat.get("title", "NONE")
        puid = plat.get("uid", "")
        print(f"OK  {name} (id={did}) -> platform@link: {ptitle} ({puid})")
    else:
        print(f"NOT FOUND: {uid}")
