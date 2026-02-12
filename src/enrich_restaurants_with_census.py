import os
import sqlite3
import requests
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "..", "data", "restaurants_google_places.sqlite")
OUT_CSV = os.path.join(BASE_DIR, "..", "data", "restaurants_enriched.csv")

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY") 

ACS_SUBJECT_2022 = "https://api.census.gov/data/2022/acs/acs5/subject"
ACS_DETAILED_2022 = "https://api.census.gov/data/2022/acs/acs5"

# Map city labels -> state/place FIPS
CITY_FIPS = {
    "San Francisco": {"state": "06", "place": "67000"},
    "Los Angeles": {"state": "06", "place": "44000"},
    "Chicago": {"state": "17", "place": "14000"},
    "New York": {"state": "36", "place": "51000"}, 
    "New York City": {"state": "36", "place": "51000"}, 
}

def census_get(url: str, params: dict) -> list:
    """Call Census API and return parsed JSON rows."""
    if CENSUS_API_KEY:
        params = dict(params)
        params["key"] = CENSUS_API_KEY

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_city_demographics(city: str, state: str, place: str) -> dict:
    """
    Pull a small set of city-level indicators:
      - total population
      - median age
      - % under 18
      - % 65+
      - median household income
    """
    # Subject table S0101 (Age and Sex)
    subj_vars = [
        "NAME",
        "S0101_C01_001E",  # total population
        "S0101_C01_032E",  # median age
        "S0101_C02_022E",  # % under 18
        "S0101_C02_030E",  # % 65+
    ]
    subj_params = {
        "get": ",".join(subj_vars),
        "for": f"place:{place}",
        "in": f"state:{state}",
    }
    subj = census_get(ACS_SUBJECT_2022, subj_params)
    header, row = subj[0], subj[1]
    subj_data = dict(zip(header, row))

    # Detailed table B19013 (Median household income)
    inc_vars = ["NAME", "B19013_001E"]
    inc_params = {
        "get": ",".join(inc_vars),
        "for": f"place:{place}",
        "in": f"state:{state}",
    }
    inc = census_get(ACS_DETAILED_2022, inc_params)
    header2, row2 = inc[0], inc[1]
    inc_data = dict(zip(header2, row2))

    def to_float(x):
        try:
            return float(x)
        except Exception:
            return None

    def to_int(x):
        try:
            return int(float(x))
        except Exception:
            return None

    return {
        "city": city,
        "census_name": subj_data.get("NAME"),
        "population_total": to_int(subj_data.get("S0101_C01_001E")),
        "median_age": to_float(subj_data.get("S0101_C01_032E")),
        "pct_under_18": to_float(subj_data.get("S0101_C02_022E")),
        "pct_65_plus": to_float(subj_data.get("S0101_C02_030E")),
        "median_household_income": to_int(inc_data.get("B19013_001E")),
        "census_state_fips": state,
        "census_place_fips": place,
    }

def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Cannot find DB at: {DB_PATH}")

    # 1) Load restaurants
    conn = sqlite3.connect(DB_PATH)
    restaurants = pd.read_sql(
        """
        SELECT
            place_id,
            city,
            name,
            rating,
            user_ratings_total,
            price_level,
            business_status,
            types
        FROM restaurants
        """,
        conn,
    )

    # 2) Fetch demographics for each city that exists in your DB
    cities_in_db = sorted(set(restaurants["city"].dropna().unique().tolist()))
    missing = [c for c in cities_in_db if c not in CITY_FIPS]

    if missing:
        print("\n[WARN] These cities are in your DB but not in CITY_FIPS mapping:")
        for c in missing:
            print(" -", c)
        print("They will get NULL demographic fields unless you add FIPS mapping.\n")

    demo_rows = []
    for city in cities_in_db:
        if city not in CITY_FIPS:
            continue
        f = CITY_FIPS[city]
        print(f"[fetch] {city} (state={f['state']}, place={f['place']})")
        demo_rows.append(fetch_city_demographics(city, f["state"], f["place"]))

    demographics = pd.DataFrame(demo_rows)

    # 3) Enrich (left join)
    enriched = restaurants.merge(demographics, on="city", how="left")

    # 4) Save results: (a) CSV in data/ (b) new sqlite table
    enriched.to_csv(OUT_CSV, index=False)
    print(f"\n[saved] {OUT_CSV}")

    demographics.to_sql("city_demographics", conn, if_exists="replace", index=False)
    enriched.to_sql("restaurants_enriched", conn, if_exists="replace", index=False)
    conn.close()

    # 5) Quick sanity print
    print("\n=== City demographics used ===")
    print(demographics.to_string(index=False))

    print("\n=== Enriched dataset preview ===")
    print(enriched.head(5).to_string(index=False))

if __name__ == "__main__":
    main()
