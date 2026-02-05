import os
import time
import json
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

CITIES = {
    "San Francisco": "San Francisco, CA",
    "Los Angeles": "Los Angeles, CA",
    "Chicago": "Chicago, IL",
    "New York": "New York, NY",
}

def fetch_text_search(api_key: str, query: str, max_pages: int = 3):
    """
    Fetch up to max_pages pages for Google Places Text Search.
    Each page returns up to 20 results. next_page_token needs a short delay to activate.
    """
    all_results = []
    params = {"query": query, "key": api_key}

    next_page_token = None
    for page in range(max_pages):
        if next_page_token:
            # Google requires a short delay before next_page_token becomes valid
            time.sleep(2)
            params = {"pagetoken": next_page_token, "key": api_key}

        r = requests.get(TEXTSEARCH_URL, params=params, timeout=30)
        data = r.json()

        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Google API error: status={status}, error_message={data.get('error_message')}")

        results = data.get("results", [])
        all_results.extend(results)

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    return all_results

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

def upsert_restaurants(conn: sqlite3.Connection, city: str, places: list[dict]):
    cur = conn.cursor()

    rows = []
    for p in places:
        loc = (p.get("geometry") or {}).get("location") or {}
        rows.append((
            city,
            p.get("place_id"),
            p.get("name"),
            p.get("formatted_address") or p.get("vicinity"),
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

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in .env")

    db_path = "restaurants_google_places.sqlite"
    conn = init_db(db_path)

    for city_name, city_query in CITIES.items():
        query = f"restaurants in {city_query}"
        print(f"\n=== Fetching: {city_name} ({query}) ===")
        places = fetch_text_search(api_key, query=query, max_pages=3)
        print(f"Fetched {len(places)} places, writing to SQLite...")

        upsert_restaurants(conn, city_name, places)

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM restaurants WHERE city=?", (city_name,))
        count = cur.fetchone()[0]
        print(f"SQLite rows for {city_name}: {count}")

    conn.close()
    print("\n✅ Done.")
    print(f"SQLite file saved as: {db_path}")

if __name__ == "__main__":
    main()
