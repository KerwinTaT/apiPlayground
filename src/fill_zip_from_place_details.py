import os
import time
import json
import sqlite3
import requests
from datetime import datetime
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "restaurants_google_places.sqlite")

DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# ---- runtime knobs ----
SLEEP_SEC = 0.15         
BATCH_COMMIT = 200        
MAX_RETRIES = 6
TIMEOUT = 20

FIELDS = "address_component,formatted_address"

def extract_postal_code(address_components) -> Optional[str]:
    if not address_components:
        return None
    for comp in address_components:
        types = comp.get("types", [])
        if "postal_code" in types:
            return comp.get("long_name")
    return None

def fetch_details(api_key: str, place_id: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Returns: (postal_code, formatted_address, status)
    status from Google API: OK, OVER_QUERY_LIMIT, REQUEST_DENIED, INVALID_REQUEST, ZERO_RESULTS, etc.
    """
    params = {
        "place_id": place_id,
        "fields": FIELDS,
        "key": api_key
    }
    r = requests.get(DETAILS_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    status = data.get("status", "UNKNOWN")

    if status != "OK":
        return None, None, status

    result = data.get("result", {})
    formatted_address = result.get("formatted_address")
    postal_code = extract_postal_code(result.get("address_components"))
    return postal_code, formatted_address, status

def ensure_indexes(conn: sqlite3.Connection):
    conn.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_city_placeid ON restaurants(city, place_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_postal_code ON restaurants(postal_code);")
    conn.commit()

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY in environment (.env)")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Cannot find DB at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    ensure_indexes(conn)

    rows = conn.execute("""
        SELECT city, place_id
        FROM restaurants
        WHERE postal_code IS NULL
          AND place_id IS NOT NULL
        ORDER BY city
    """).fetchall()

    total = len(rows)
    print(f"[info] Need to fill postal_code for {total} places")

    updated = 0
    skipped = 0
    over_limit_hits = 0
    start = time.time()

    try:
        for i, (city, place_id) in enumerate(rows, start=1):
            time.sleep(SLEEP_SEC)

            retry = 0
            backoff = 1.0
            while True:
                try:
                    postal_code, formatted_address, status = fetch_details(api_key, place_id)

                    if status == "OK":
                        conn.execute("""
                            UPDATE restaurants
                            SET postal_code = ?,
                                formatted_address = ?,
                                details_fetched_at = ?
                            WHERE place_id = ? AND city = ?
                        """, (postal_code, formatted_address, datetime.utcnow().isoformat(timespec="seconds"), place_id, city))
                        updated += 1

                    elif status == "OVER_QUERY_LIMIT":
                        over_limit_hits += 1
                        wait = min(60, backoff)
                        print(f"[rate] OVER_QUERY_LIMIT at {i}/{total}. sleeping {wait:.1f}s (hit={over_limit_hits})")
                        time.sleep(wait)
                        backoff *= 2
                        retry += 1
                        if retry > MAX_RETRIES:
                            print("[rate] Too many retries. Stop now; rerun later to continue.")
                            raise SystemExit(2)
                        continue

                    else:
                        skipped += 1
                        if i % 200 == 0 or status not in ("ZERO_RESULTS",):
                            print(f"[skip] {status} city={city} place_id={place_id}")

                    break # exit retry loop on success or non-retryable status

                except requests.RequestException as e:
                    retry += 1
                    if retry > MAX_RETRIES:
                        print(f"[net] give up place_id={place_id} after {MAX_RETRIES} retries: {e}")
                        skipped += 1
                        break
                    wait = min(30, 2 ** retry)
                    print(f"[net] error {e}; retry in {wait}s (place_id={place_id})")
                    time.sleep(wait)

            if i % BATCH_COMMIT == 0:
                conn.commit()
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                print(f"[progress] {i}/{total} updated={updated} skipped={skipped} rate={rate:.2f} req/s")

        conn.commit()

    finally:
        conn.close()

    print(f"[done] updated={updated} skipped={skipped} total={total}")

if __name__ == "__main__":
    main()
