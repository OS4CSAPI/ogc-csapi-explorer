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
    "0430", "043g", "04c0", "0440", "0410", "041g", "042g",  # MA-1 (04c0 = LOB, was 0420)
    "0450", "045g", "04cg", "046g", "0470", "047g", "0480",  # MA-2 (04cg = LOB, was 0460)
    "048g", "0490", "04d0", "04a0", "04ag", "04b0", "04bg",  # MA-3 (04d0 = LOB, was 049g)
    "04dg", "04e0", "04eg",  # Detection capabilities (MA-1, MA-2, MA-3)
]


def make_session():
    s = requests.Session()
    s.auth = AUTH
    s.verify = False
    s.headers.update({"Accept": "application/json"})
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1, pool_maxsize=1,
        max_retries=urllib3.Retry(total=5, backoff_factor=2,
                                   status_forcelist=[502, 503, 504]),
    )
    s.mount("https://", adapter)
    return s


def _retry(fn, label="request", max_retries=8, base_delay=3):
    """Run fn() with retries on transient DNS / connection errors."""
    for attempt in range(max_retries):
        try:
            return fn()
        except (requests.ConnectionError, requests.Timeout, OSError) as e:
            wait = base_delay * (attempt + 1)
            print(f"    ↻ Retry {label} in {wait}s ({type(e).__name__})")
            time.sleep(wait)
    raise RuntimeError(f"Failed after {max_retries} retries: {label}")


def clear_datastream(ds_id, session):
    """Clear all observations from a single datastream. Returns count deleted."""
    total = 0
    consecutive_errors = 0

    while consecutive_errors < 10:
        # Fetch a batch with DNS-resilient retry
        try:
            r = _retry(
                lambda: session.get(
                    f"{BASE}/datastreams/{ds_id}/observations?limit=50",
                    timeout=(10, 30),
                ),
                label=f"GET obs {ds_id}",
            )
            items = r.json().get("items", [])
        except Exception as e:
            consecutive_errors += 1
            print(f"    ⚠ Fetch error ({consecutive_errors}): {type(e).__name__}")
            try:
                session.close()
            except Exception:
                pass
            session = make_session()
            time.sleep(3)
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
                r = _retry(
                    lambda oid=obs_id: session.delete(
                        f"{BASE}/observations/{oid}", timeout=(10, 20)
                    ),
                    label=f"DEL {obs_id}",
                )
                if r.status_code in (200, 204):
                    batch += 1
            except Exception:
                # Connection dropped — recreate session and continue
                try:
                    session.close()
                except Exception:
                    pass
                session = make_session()
                time.sleep(2)

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
        # Get name (with retry)
        try:
            meta = _retry(
                lambda did=ds_id: session.get(f"{BASE}/datastreams/{did}", timeout=(10, 20)).json(),
                label=f"meta {ds_id}",
            )
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
