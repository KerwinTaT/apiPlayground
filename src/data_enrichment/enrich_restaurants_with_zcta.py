import os
import sqlite3
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from src.config import DB_PATH, BASE_DIR

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")  # may be None; script still runs

ACS_SUBJECT_2022 = "https://api.census.gov/data/2022/acs/acs5/subject"
ACS_DETAILED_2022 = "https://api.census.gov/data/2022/acs/acs5"

# --- variables we will pull ---
# S0101 (Age and Sex - subject table)
S0101_VARS = [
    "NAME",
    "S0101_C01_001E",  # total population
    "S0101_C01_032E",  # median age
    "S0101_C02_022E",  # % under 18
    "S0101_C02_030E",  # % 65+
]

# B19013 (Median household income - detailed table)
B19013_VARS = [
    "NAME",
    "B19013_001E",     # median household income
]

GEO_FOR_ALL_ZCTA = "zip code tabulation area:*"  # pull all ZCTAs once, then filter locally


def get_json(url: str, params: dict, max_retries: int = 5, timeout: int = 60):
    """Robust GET with retries; returns JSON list-of-lists (header + rows)."""
    if CENSUS_API_KEY:
        params = dict(params)
        params["key"] = CENSUS_API_KEY

    backoff = 2
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == max_retries:
                raise
            print(f"[net] error: {e} | retry {attempt}/{max_retries} in {backoff}s")
            time.sleep(backoff)
            backoff = min(60, backoff * 2)


def to_int(x):
    try:
        # some values come as string floats; normalize
        return int(float(x))
    except Exception:
        return None


def to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Cannot find DB at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # Load distinct zip5 from restaurants
    zips = pd.read_sql(
        """
        SELECT DISTINCT zip5
        FROM restaurants
        WHERE zip5 IS NOT NULL
          AND LENGTH(zip5) = 5
        """,
        conn,
    )
    zip_set = set(zips["zip5"].astype(str).tolist())
    print(f"[info] distinct zip5 in DB: {len(zip_set)}")

    # Fetch ALL ZCTA demographic rows once (S0101)
    print("[fetch] ACS S0101 (population/age) for all ZCTAs ...")
    s0101_json = get_json(
        ACS_SUBJECT_2022,
        params={"get": ",".join(S0101_VARS), "for": GEO_FOR_ALL_ZCTA},
        timeout=120,
    )
    s0101_header = s0101_json[0]
    s0101_rows = s0101_json[1:]
    s0101_df = pd.DataFrame(s0101_rows, columns=s0101_header)

    # the API returns the geo id column named exactly "zip code tabulation area"
    GEO_COL = "zip code tabulation area"
    if GEO_COL not in s0101_df.columns:
        raise RuntimeError(f"Unexpected Census response: missing '{GEO_COL}' column")

    # Fetch ALL ZCTA income rows once (B19013)
    print("[fetch] ACS B19013 (median household income) for all ZCTAs ...")
    b19013_json = get_json(
        ACS_DETAILED_2022,
        params={"get": ",".join(B19013_VARS), "for": GEO_FOR_ALL_ZCTA},
        timeout=120,
    )
    b19013_header = b19013_json[0]
    b19013_rows = b19013_json[1:]
    b19013_df = pd.DataFrame(b19013_rows, columns=b19013_header)

    if GEO_COL not in b19013_df.columns:
        raise RuntimeError(f"Unexpected Census response: missing '{GEO_COL}' column in B19013 response")

    # Filter to only your 806 zips
    s0101_df = s0101_df[s0101_df[GEO_COL].isin(zip_set)].copy()
    b19013_df = b19013_df[b19013_df[GEO_COL].isin(zip_set)].copy()

    # Clean + merge into one zcta_demographics df
    # keep zip as TEXT to preserve leading zeros
    s0101_df["zip5"] = s0101_df[GEO_COL].astype(str)
    b19013_df["zip5"] = b19013_df[GEO_COL].astype(str)

    zcta = s0101_df[[
        "zip5",
        "NAME",
        "S0101_C01_001E",
        "S0101_C01_032E",
        "S0101_C02_022E",
        "S0101_C02_030E",
    ]].merge(
        b19013_df[["zip5", "B19013_001E"]],
        on="zip5",
        how="left",
    )

    zcta = zcta.rename(columns={
        "NAME": "census_name",
        "S0101_C01_001E": "population_total",
        "S0101_C01_032E": "median_age",
        "S0101_C02_022E": "pct_under_18",
        "S0101_C02_030E": "pct_65_plus",
        "B19013_001E": "median_household_income",
    })

    # type conversions
    zcta["population_total"] = zcta["population_total"].apply(to_int)
    zcta["median_age"] = zcta["median_age"].apply(to_float)
    zcta["pct_under_18"] = zcta["pct_under_18"].apply(to_float)
    zcta["pct_65_plus"] = zcta["pct_65_plus"].apply(to_float)
    zcta["median_household_income"] = zcta["median_household_income"].apply(to_int)

    print(f"[info] zcta_demographics rows after filtering: {len(zcta)}")

    # Write zcta_demographics table
    zcta.to_sql("zcta_demographics", conn, if_exists="replace", index=False)
    print("[write] table zcta_demographics (replace)")

    # Create restaurants_enriched_zip (replace) via SQL join
    conn.execute("DROP TABLE IF EXISTS restaurants_enriched_zip;")
    conn.execute("""
        CREATE TABLE restaurants_enriched_zip AS
        SELECT
            r.*,
            z.population_total,
            z.median_age,
            z.pct_under_18,
            z.pct_65_plus,
            z.median_household_income,
            z.census_name
        FROM restaurants r
        LEFT JOIN zcta_demographics z
          ON r.zip5 = z.zip5;
    """)
    print("[write] table restaurants_enriched_zip (replace)")

    # Create zip_analysis aggregation table (replace)
    conn.execute("DROP TABLE IF EXISTS zip_analysis;")
    conn.execute("""
        CREATE TABLE zip_analysis AS
        SELECT
            r.zip5,
            COUNT(*) AS restaurant_count,
            ROUND(AVG(r.rating), 3) AS avg_rating,
            ROUND(AVG(r.price_level), 3) AS avg_price_level,
            MAX(r.population_total) AS population_total,
            MAX(r.median_household_income) AS median_household_income,
            MAX(r.median_age) AS median_age,
            MAX(r.pct_under_18) AS pct_under_18,
            MAX(r.pct_65_plus) AS pct_65_plus,
            ROUND(CAST(COUNT(*) AS REAL) / NULLIF(MAX(r.population_total), 0) * 1000.0, 3) AS restaurants_per_1000_people
        FROM restaurants_enriched_zip r
        WHERE r.zip5 IS NOT NULL
        GROUP BY r.zip5;
    """)
    print("[write] table zip_analysis (replace)")

    conn.commit()
    conn.close()

    print("\n[done] ZIP-level Census enrichment complete.")
    print("Created tables: zcta_demographics, restaurants_enriched_zip, zip_analysis")


if __name__ == "__main__":
    main()
