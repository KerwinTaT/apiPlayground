import sqlite3
import pandas as pd
from src.config import DB_PATH

def main():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
        SELECT *
        FROM zip_analysis
        WHERE population_total IS NOT NULL
          AND median_household_income IS NOT NULL
    """, conn)
    
    df = df[df["median_household_income"] > 0]

    conn.close()

    print("\nNumber of ZIPs used in analysis:", len(df))

    cols = [
        "median_household_income",
        "avg_price_level",
        "avg_rating",
        "restaurants_per_1000_people",
        "median_age"
    ]

    corr_matrix = df[cols].corr()

    print("\n=== Correlation Matrix ===\n")
    print(corr_matrix)

if __name__ == "__main__":
    main()
