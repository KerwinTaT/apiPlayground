import os
import time
import json
import math
import random
import sqlite3
import requests
from collections import deque
from dotenv import load_dotenv
from pathlib import Path


# ================== CONFIG ==================

load_dotenv()

GOOGLE_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
KEYWORD = "restaurant"

REQUEST_SLEEP = 0.8   

WINDOW = 50           
MIN_NEW_AVG = 0.5     
STABLE_WINDOWS = 5  

STEP_MULTIPLIER = 1.2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "restaurants_google_places.sqlite"


CITIES = {
    "San Francisco": {
        "bbox": {"lat_min": 37.66, "lat_max": 37.84, "lng_min": -122.55, "lng_max": -122.33},
        "radius_m": 1200,
    },
    "Los Angeles": {
        "bbox": {"lat_min": 33.70, "lat_max": 34.35, "lng_min": -118.70, "lng_max": -118.10},
        "radius_m": 3000,
    },
    "Chicago": {
        "bbox": {"lat_min": 41.65, "lat_max": 42.10, "lng_min": -88.05, "lng_max": -87.45},
        "radius_m": 1600,
    },
    "New York": {
        "bbox": {"lat_min": 40.50, "lat_max": 40.95, "lng_min": -74.30, "lng_max": -73.65},
        "radius_m": 1400,
    },
}

# ================== SAFE GET ==================

def safe_get(url, params, max_tries=6):
    timeout = (10, 90)  # (connect_timeout, read_timeout)

    for i in range(max_tries):
        try:
            return requests.get(url, params=params, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            sleep_s = min(2 ** i, 30) + random.uniform(0, 1)
            print(f"⚠️ ReadTimeout, retry {i+1}/{max_tries} after {sleep_s:.1f}s")
            time.sleep(sleep_s)
        except requests.exceptions.RequestException as e:
            sleep_s = min(2 ** i, 30) + random.uniform(0, 1)
            print(f"⚠️ Network error: {e}, retry {i+1}/{max_tries} after {sleep_s:.1f}s")
            time.sleep(sleep_s)

    raise RuntimeError("❌ Failed after repeated network errors")

# ================== DB ==================

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")

    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        city TEXT,
        place_id TEXT,
        name TEXT,
        address TEXT,
        lat REAL,
        lng REAL,
        rating REAL,
        user_ratings_total INTEGER,
        price_level INTEGER,
        business_status TEXT,
        types TEXT,
        raw_json TEXT,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (city, place_id)
    )
    """)
    conn.commit()
    return conn

def load_existing_ids(conn, city):
    cur = conn.cursor()
    cur.execute("SELECT place_id FROM restaurants WHERE city=?", (city,))
    return {row[0] for row in cur.fetchall()}

INSERT_SQL = """
INSERT INTO restaurants (
  city, place_id, name, address, lat, lng, rating, user_ratings_total,
  price_level, business_status, types, raw_json, fetched_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(city, place_id) DO UPDATE SET
  name = excluded.name,
  address = excluded.address,
  lat = excluded.lat,
  lng = excluded.lng,
  rating = excluded.rating,
  user_ratings_total = excluded.user_ratings_total,
  price_level = excluded.price_level,
  business_status = excluded.business_status,
  types = excluded.types,
  raw_json = excluded.raw_json,
  fetched_at = CURRENT_TIMESTAMP;
"""

def insert_places(conn, city, places):
    if not places:
        return 0

    rows = []
    for p in places:
        loc = p.get("geometry", {}).get("location", {}) or {}
        rows.append((
            city,
            p.get("place_id"),
            p.get("name"),
            p.get("vicinity") or p.get("formatted_address"),
            loc.get("lat"),
            loc.get("lng"),
            p.get("rating"),
            p.get("user_ratings_total"),
            p.get("price_level"),
            p.get("business_status"),
            json.dumps(p.get("types", []), ensure_ascii=False, separators=(",", ":")),
            # raw_json 
            json.dumps(p, ensure_ascii=False, separators=(",", ":")),
        ))

    before = conn.total_changes
    with conn:
        conn.executemany(INSERT_SQL, rows)
    written = conn.total_changes - before
    return written

def count_city(conn, city):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM restaurants WHERE city=?", (city,))
    return cur.fetchone()[0]

# ================== GEO ==================

def meters_to_lat(m): return m / 111320
def meters_to_lng(m, lat): return m / (111320 * math.cos(math.radians(lat)) + 1e-9)

def grid_points(bbox, step_m):
    lat = bbox["lat_min"]
    while lat <= bbox["lat_max"]:
        lng = bbox["lng_min"]
        lng_step = meters_to_lng(step_m, lat)
        while lng <= bbox["lng_max"]:
            yield lat, lng
            lng += lng_step
        lat += meters_to_lat(step_m)

# ================== GOOGLE API ==================

def fetch_nearby(api_key, lat, lng, radius_m, keyword):
    all_results = []
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "keyword": keyword,
        "key": api_key,
    }

    next_token = None
    for _ in range(3):
        if next_token:
            time.sleep(2)
            params = {"pagetoken": next_token, "key": api_key}

        r = safe_get(GOOGLE_NEARBY_URL, params)
        data = r.json()

        status = data.get("status")
       
        # 1) next_page_token 
        if status == "INVALID_REQUEST" and next_token:
            time.sleep(2)
            r = safe_get(GOOGLE_NEARBY_URL, params)
            data = r.json()
            status = data.get("status")

        # 2) OK / ZERO_RESULTS
        if status == "OK":
            all_results.extend(data.get("results", []))
            next_token = data.get("next_page_token")
            if not next_token:
                break
            continue

        if status == "ZERO_RESULTS":
            # 正常：这个点附近确实没结果
            next_token = None
            break

        # 3) UNKNOWN_ERROR
        if status == "UNKNOWN_ERROR":
            print(f"⚠️ Google status=UNKNOWN_ERROR at ({lat:.4f},{lng:.4f}), sleeping 2s then retry")
            time.sleep(2)
            r = safe_get(GOOGLE_NEARBY_URL, params)
            data = r.json()
            status = data.get("status")

            if status == "OK":
                all_results.extend(data.get("results", []))
                next_token = data.get("next_page_token")
                if not next_token:
                    break
                continue
            if status == "ZERO_RESULTS":
                break

        # 4) otehr error
        print(
            f"❌ Google status={status} "
            f"at ({lat:.4f},{lng:.4f}) "
            f"msg={data.get('error_message')}"
        )
        return []

    return all_results

# ================== MAIN ==================

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY")

    conn = init_db()

    for city, cfg in CITIES.items():
        print(f"\n=== Fetching {city} ===")
        seen = load_existing_ids(conn, city)
        recent = deque(maxlen=WINDOW)
        stable_hits = 0
        points_done = 0
        MIN_POINTS_BEFORE_PLATEAU = 80 


        radius = cfg["radius_m"]
        step_m = int(radius * STEP_MULTIPLIER)

        for lat, lng in grid_points(cfg["bbox"], step_m):
            results = fetch_nearby(api_key, lat, lng, radius, KEYWORD)

            new_places = []
            for p in results:
                pid = p.get("place_id")
                if pid and pid not in seen:
                    seen.add(pid)
                    new_places.append(p)

            written = 0
            if new_places:
                written = insert_places(conn, city, new_places)

            points_done += 1

            if points_done == MIN_POINTS_BEFORE_PLATEAU:
                recent.clear()
                stable_hits = 0

            recent.append(len(new_places))
            avg_new = sum(recent) / len(recent)

            print(
                f"Point ({lat:.4f},{lng:.4f}) → "
                f"got {len(results)}, new {len(new_places)}, "
                f"total {len(seen)}, avg_new={avg_new:.2f}, "
                f"pt={points_done}"
            )

            if len(recent) == WINDOW:
                if points_done < MIN_POINTS_BEFORE_PLATEAU:
                    stable_hits = 0
                else:
                    if avg_new < MIN_NEW_AVG:
                        stable_hits += 1
                    else:
                        stable_hits = 0

                    if stable_hits >= STABLE_WINDOWS:
                        print(f"✅ Plateau reached for {city}")
                        break

            time.sleep(REQUEST_SLEEP)

        print(f"✅ Final rows for {city}: {count_city(conn, city)}")

    conn.close()
    print("\n✅ Done. SQLite saved as:", DB_PATH.resolve())

if __name__ == "__main__":
    main()
