import sqlite3
import pandas as pd
from src.config import DB_PATH

TABLE = "restaurants_enriched_zip"  # 先查这张

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(f"SELECT * FROM {TABLE};", conn)

print("Table:", TABLE)
print("Shape:", df.shape)
print("\nMissing values (top 20):")
print(df.isnull().sum().sort_values(ascending=False).head(20))

print("\nRating describe:")
print(df["rating"].describe())

print("\nPrice_level value counts (incl NaN):")
print(df["price_level"].value_counts(dropna=False).head(10))

print("\nuser_ratings_total describe:")
print(df["user_ratings_total"].describe())

conn.close()