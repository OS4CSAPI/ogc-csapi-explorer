"""Bulk-clear ALL observations from every datastream.

Uses requests.Session for HTTP keep-alive / connection pooling.
Short timeouts + per-request exception handling to survive flaky connection.
"""

import requests
import urllib3
import time
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = ("os4csapi", "ogc134mm")

# All datastream IDs on the server
ALL_DS_IDS = [
    "044g",  # SENREP
    "0430", "043g", "0420", "0440", "0410", "041g", "042g",  # MA-1
    "0450", "045g", "0460", "046g", "0470", "047g", "0480",  # MA-2
    "048g", "0490", "049g", "04a0", "04ag", "04b0", "04bg",  # MA-3
]


def make_session():
    s = requests.Session()
    s.auth = AUTH
    s.verify = False
    s.headers.update({"Accept": "application/json"})
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1, pool_maxsize=1,
        max_retries=urllib3.Retry(total=3, backoff_factor=1,
                                   status_forcelist=[502, 503, 504]),
    )
    s.mount("https://", adapter)
    return s


def clear_datastream(ds_id, session):
    """Clear all observations from a single datastream. Returns count deleted."""
    total = 0
    consecutive_errors = 0

    while consecutive_errors < 5:
        # Fetch a batch
        try:
            r = session.get(
                f"{BASE}/datastreams/{ds_id}/observations?limit=50",
                timeout=(5, 15),
            )
            items = r.json().get("items", [])
        except Exception as e:
            consecutive_errors += 1
            print(f"    ⚠ Fetch error ({consecutive_errors}): {type(e).__name__}")
            time.sleep(2)
            continue

        if not items:
            break  # All done

        consecutive_errors = 0
        batch = 0

        for obs in items:
            obs_id = obs.get("id")
            if not obs_id:
                continue
            try:
                r = session.delete(f"{BASE}/observations/{obs_id}", timeout=(5, 10))
                if r.status_code in (200, 204):
                    batch += 1
            except Exception:
                # Connection dropped — recreate session and continue
                try:
                    session.close()
                except Exception:
                    pass
                session = make_session()
                time.sleep(1)

        total += batch
        sys.stdout.write(f"\r    Deleted {total}...")
        sys.stdout.flush()

        if batch == 0 and items:
            # All deletes failed in this batch
            consecutive_errors += 1
            time.sleep(2)

    if total > 0:
        print(f"\r    ✓ Cleared {total} observations")
    else:
        print(f"\r    (empty)")

    return total, session


def main():
    session = make_session()

    print("Clearing observations from all datastreams...\n")
    grand_total = 0

    for ds_id in ALL_DS_IDS:
        # Get name
        try:
            meta = session.get(f"{BASE}/datastreams/{ds_id}", timeout=(5, 10)).json()
            name = meta.get("name", "?")
        except Exception:
            name = "?"

        print(f"  [{ds_id}] {name}")
        count, session = clear_datastream(ds_id, session)
        grand_total += count

    print(f"\n✓ Done. Total deleted: {grand_total}")
    session.close()


if __name__ == "__main__":
    main()
