"""
Add Photograph document to MA node top-level systems (AZ-MA-1, AZ-MA-2, AZ-MA-3).

The MICARRAY subsystems already have the photo, but the parent system doesn't.
The deployed-system card resolves the parent system SML, so it needs the photo there.
"""
import json
import requests

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = ("os4csapi", "ogc134mm")
PHOTO_DOC = {
    "role": "http://dbpedia.org/resource/Photograph",
    "name": "Microphone Array Photo",
    "description": "XMOS XVF3800 7-microphone circular MEMS array mounted on field tripod.",
    "link": {
        "href": "https://raw.githubusercontent.com/OS4CSAPI/ogc-csapi-explorer/refs/heads/demo/acoustic-cuas-targeting/demo/public/xmos-7mic-array.jpg",
        "type": "image/jpeg"
    }
}

MA_SYSTEMS = {
    "0420": "AZ-MA-1",
    "0490": "AZ-MA-2",
    "049g": "AZ-MA-3",
}


def add_photo(system_id: str, label: str):
    """Fetch current SML, prepend the photo document, PUT back."""
    url = f"{BASE}/systems/{system_id}"
    # Fetch current SML
    resp = requests.get(url, params={"f": "application/sml+json"},
                        headers={"Accept": "application/sml+json"},
                        auth=AUTH)
    resp.raise_for_status()
    sml = resp.json()
    
    # Check if photo already exists
    docs = sml.get("documents", [])
    for d in docs:
        link = d.get("link", {})
        if isinstance(link, dict) and link.get("type", "").startswith("image/"):
            print(f"  {label} ({system_id}): already has image doc — skipping")
            return
    
    # Prepend photo so it becomes first (thumbnail)
    sml["documents"] = [PHOTO_DOC] + docs
    
    # PUT back
    put_resp = requests.put(url, json=sml,
                            headers={"Content-Type": "application/sml+json",
                                     "Accept": "application/sml+json"},
                            auth=AUTH)
    if put_resp.status_code in (200, 204):
        print(f"  {label} ({system_id}): ✓ photo added")
    else:
        print(f"  {label} ({system_id}): ✗ HTTP {put_resp.status_code} — {put_resp.text[:200]}")


if __name__ == "__main__":
    print("Adding Photograph documents to MA node systems...")
    for sid, name in MA_SYSTEMS.items():
        add_photo(sid, name)
    print("Done.")
