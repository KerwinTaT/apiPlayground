import os
import time
import json
import math
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

CITIES = {
    "San Francisco": {
        "bbox": {"lat_min": 37.70, "lat_max": 37.82, "lng_min": -122.52, "lng_max": -122.35},
        "radius_m": 1200,
    },
    "Los Angeles": {
        "bbox": {"lat_min": 33.90, "lat_max": 34.12, "lng_min": -118.52, "lng_max": -118.15},
        "radius_m": 1800,
    },
    "Chicago": {
        "bbox": {"lat_min": 41.78, "lat_max": 42.05, "lng_min": -87.85, "lng_max": -87.55},
        "radius_m": 1600,
    },
    "New York": {
        "bbox": {"lat_min": 40.65, "lat_max": 40.85, "lng_min": -74.05, "lng_max": -73.85},
        "radius_m": 1400,
    },
}

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        city TEXT NOT NULL,
        place_id TEXT NOT NULL,
        name TEXT,
        formatted_address TEXT,
        lat REAL,
        lng REAL,
        rating REAL,
        user_ratings_total INTEGER,
        price_level INTEGER,
        business_status TEXT,
        types TEXT,
        raw_json TEXT,
        fetched_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (city, place_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city);")
    conn.commit()
    return conn

def upsert_places(conn, city: str, places: list[dict]):
    cur = conn.cursor()
    rows = []
    for p in places:
        loc = (p.get("geometry") or {}).get("location") or {}
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
            json.dumps(p.get("types", []), ensure_ascii=False),
            json.dumps(p, ensure_ascii=False),
        ))

    cur.executemany("""
    INSERT INTO restaurants (
        city, place_id, name, formatted_address, lat, lng,
        rating, user_ratings_total, price_level, business_status,
        types, raw_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(city, place_id) DO UPDATE SET
        name=excluded.name,
        formatted_address=excluded.formatted_address,
        lat=excluded.lat,
        lng=excluded.lng,
        rating=excluded.rating,
        user_ratings_total=excluded.user_ratings_total,
        price_level=excluded.price_level,
        business_status=excluded.business_status,
        types=excluded.types,
        raw_json=excluded.raw_json,
        fetched_at=datetime('now');
    """, rows)

    conn.commit()

def meters_to_lat_deg(m: float) -> float:
    return m / 111_320.0  

def meters_to_lng_deg(m: float, lat_deg: float) -> float:
    return m / (111_320.0 * math.cos(math.radians(lat_deg)) + 1e-9)

def generate_grid_points(bbox: dict, step_m: int):
    """
    Generate grid points across bbox using ~step_m spacing.
    """
    lat_min, lat_max = bbox["lat_min"], bbox["lat_max"]
    lng_min, lng_max = bbox["lng_min"], bbox["lng_max"]

    lat_step = meters_to_lat_deg(step_m)
    lat = lat_min
    while lat <= lat_max:
        lng_step = meters_to_lng_deg(step_m, lat)
        lng = lng_min
        while lng <= lng_max:
            yield (lat, lng)
            lng += lng_step
        lat += lat_step

def fetch_nearby(api_key: str, lat: float, lng: float, radius_m: int, keyword: str = "restaurant", max_pages: int = 3):
    """
    Google Nearby Search: up to 20 results per page, typically up to 3 pages (~60).
    """
    all_results = []
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "keyword": keyword,
        "key": api_key,
    }

    next_token = None
    for _ in range(max_pages):
        if next_token:
            time.sleep(2) 
            params = {"pagetoken": next_token, "key": api_key}

        r = requests.get(NEARBY_URL, params=params, timeout=30)
        data = r.json()
        status = data.get("status")

        if status == "INVALID_REQUEST" and next_token:
            time.sleep(2)
            r = requests.get(NEARBY_URL, params=params, timeout=30)
            data = r.json()
            status = data.get("status")

        if status not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Google Nearby error: status={status}, error_message={data.get('error_message')}")

        all_results.extend(data.get("results", []))
        next_token = data.get("next_page_token")
        if not next_token:
            break

    return all_results

def count_city(conn, city: str) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM restaurants WHERE city=?", (city,))
    return cur.fetchone()[0]

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in .env")

    db_path = "restaurants_google_places.sqlite"
    conn = init_db(db_path)

    TARGET_PER_CITY = 1000
    STEP_MULTIPLIER = 1.2  

    for city, cfg in CITIES.items():
        bbox = cfg["bbox"]
        radius = int(cfg["radius_m"])
        step_m = int(radius * STEP_MULTIPLIER)

        print(f"\n=== City: {city} | target={TARGET_PER_CITY} | radius={radius}m | step≈{step_m}m ===")

        current = count_city(conn, city)
        print(f"Current SQLite rows for {city}: {current}")

        seen_place_ids = set()
        cur = conn.cursor()
        cur.execute("SELECT place_id FROM restaurants WHERE city=?", (city,))
        for (pid,) in cur.fetchall():
            seen_place_ids.add(pid)

        for (lat, lng) in generate_grid_points(bbox, step_m=step_m):
            if len(seen_place_ids) >= TARGET_PER_CITY:
                break

            try:
                results = fetch_nearby(api_key, lat, lng, radius_m=radius, keyword="restaurant", max_pages=3)
            except RuntimeError as e:
                msg = str(e)
                print(f"⚠️ API error at ({lat:.5f},{lng:.5f}): {msg}")
                time.sleep(2)
                continue

            new_places = []
            for p in results:
                pid = p.get("place_id")
                if not pid:
                    continue
                if pid in seen_place_ids:
                    continue
                seen_place_ids.add(pid)
                new_places.append(p)

                if len(seen_place_ids) >= TARGET_PER_CITY:
                    break

            if new_places:
                upsert_places(conn, city, new_places)

            if len(seen_place_ids) % 100 == 0 or new_places:
                print(f"Point ({lat:.4f},{lng:.4f}) -> got {len(results)} results, new {len(new_places)}, total {len(seen_place_ids)}")

            time.sleep(0.2)

        final_count = count_city(conn, city)
        print(f"✅ Final SQLite rows for {city}: {final_count}")

        if final_count < TARGET_PER_CITY:
            print(f"⚠️ Only got {final_count} (<{TARGET_PER_CITY}). Consider expanding bbox or decreasing step size.")

    conn.close()
    print("\n✅ Done.")
    print("SQLite file saved as: restaurants_google_places.sqlite")

if __name__ == "__main__":
    main()
