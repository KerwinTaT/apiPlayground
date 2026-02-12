import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "restaurants_google_places.sqlite")
OUT_DIR = os.path.join(BASE_DIR, "..", "data", "figures")

sns.set_theme(style="whitegrid")

def savefig(name: str):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    print(f"[saved] {path}")

def main():
    # ---------- setup ----------
    sns.set_theme(style="whitegrid")
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Cannot find DB at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    # ---------- load data ----------
    df = pd.read_sql("""
        SELECT
            city,
            name,
            rating,
            user_ratings_total,
            price_level,
            business_status,
            types
        FROM restaurants
    """, conn)

    conn.close()

    df_rating = df[df["rating"].notna()].copy()

    # 1) Average rating by city
    avg_rating_city = (
        df_rating.groupby("city")["rating"]
        .mean()
        .reset_index()
        .sort_values("rating", ascending=False)
    )

    plt.figure(figsize=(8, 5))
    sns.barplot(data=avg_rating_city, x="city", y="rating")
    plt.title("Average Restaurant Rating by City")
    plt.ylabel("Average Rating")
    plt.xlabel("City")
    plt.ylim(3.5, 5.0) 
    savefig("01_avg_rating_by_city.png")
    plt.show()

    print("\n=== Average Rating by City ===")
    print(avg_rating_city.to_string(index=False))

    # 2) Price level distribution per city
    price_df = df[df["price_level"].notna()].copy()

    plt.figure(figsize=(10, 6))
    sns.countplot(data=price_df, x="price_level", hue="city")
    plt.title("Price Level Distribution by City")
    plt.xlabel("Price Level (0=cheapest, 4=most expensive)")
    plt.ylabel("Number of Restaurants")
    savefig("02_price_level_distribution_by_city.png")
    plt.show()

    print("\n=== Price Level Distribution by City ===")

    # 3) Top restaurant types/cuisines (overall)
    types_df = df[["city", "types"]].dropna().copy()

    def safe_json_load(s):
        try:
            return json.loads(s)
        except Exception:
            return []

    types_df["types_list"] = types_df["types"].apply(safe_json_load)
    types_exploded = types_df.explode("types_list").rename(columns={"types_list": "type"})
    types_exploded = types_exploded[types_exploded["type"].notna()]

    exclude = {"restaurant", "food", "point_of_interest", "establishment", "store"}
    types_clean = types_exploded[~types_exploded["type"].isin(exclude)].copy()

    top_types = (
        types_clean.groupby("type")
        .size()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name="count")
    )

    plt.figure(figsize=(10, 6))
    sns.barplot(data=top_types, y="type", x="count")
    plt.title("Top 10 Restaurant Types Across All Cities")
    plt.xlabel("Number of Restaurants")
    plt.ylabel("Restaurant Type")
    savefig("03_top10_types_overall.png")
    plt.show()

    print("\n=== Top 10 Types Overall ===")
    print(top_types.to_string(index=False))

    # 4) Top 5 types per city (comparison)
    top_types_city = (
        types_clean.groupby(["city", "type"])
        .size()
        .reset_index(name="count")
        .sort_values(["city", "count"], ascending=[True, False])
        .groupby("city")
        .head(5)
    )

    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_types_city, x="count", y="type", hue="city")
    plt.title("Top 5 Restaurant Types by City")
    plt.xlabel("Number of Restaurants")
    plt.ylabel("Restaurant Type")
    savefig("04_top5_types_by_city.png")
    plt.show()

    print("\n=== Top 5 Types by City ===")
    for city in sorted(top_types_city["city"].unique()):
        print(f"\n-- {city} --")
        print(top_types_city[top_types_city["city"] == city][["type", "count"]].to_string(index=False))

if __name__ == "__main__":
    main()
