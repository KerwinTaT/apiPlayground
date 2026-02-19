import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

    sns.set_theme(style="whitegrid")

    # 1. Income vs Avg Price
    plt.figure(figsize=(6,5))
    sns.scatterplot(data=df, x="median_household_income", y="avg_price_level")
    plt.title("Income vs Average Price Level")
    plt.tight_layout()
    plt.show()

    # 2. Income vs Avg Rating
    plt.figure(figsize=(6,5))
    sns.scatterplot(data=df, x="median_household_income", y="avg_rating")
    plt.title("Income vs Average Rating")
    plt.tight_layout()
    plt.show()

    # 3. Income vs Restaurant Density
    plt.figure(figsize=(6,5))
    sns.scatterplot(data=df, x="median_household_income", y="restaurants_per_1000_people")
    plt.title("Income vs Restaurant Density")
    plt.tight_layout()
    plt.show()

    # 4. Median Age vs Density
    plt.figure(figsize=(6,5))
    sns.scatterplot(data=df, x="median_age", y="restaurants_per_1000_people")
    plt.title("Median Age vs Restaurant Density")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
