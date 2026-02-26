import sqlite3
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from src.config import DB_PATH, FIG_DIR

conn = sqlite3.connect(str(DB_PATH))

df = pd.read_sql_query("""
SELECT
  city,
  rating,
  price_level,
  median_household_income,
  population_total
FROM restaurants_enriched_zip
WHERE rating IS NOT NULL
  AND price_level IS NOT NULL
  AND median_household_income IS NOT NULL
  AND population_total IS NOT NULL
  AND median_household_income > 0
  AND population_total > 1000
""", conn)

conn.close()

print("Rows:", len(df))

X = df[["rating", "price_level", "median_household_income", "population_total"]].astype(float)

X_scaled = StandardScaler().fit_transform(X)

k = 4
kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
df["cluster"] = kmeans.fit_predict(X_scaled)

print(df["cluster"].value_counts().sort_index())
print(df.groupby("cluster")[["rating", "price_level", "median_household_income", "population_total"]].mean())

plt.figure()
plt.scatter(df["rating"], df["price_level"], c=df["cluster"])
plt.xlabel("Rating")
plt.ylabel("Price Level")
plt.title("Restaurant Clusters (Enriched)")

output_path = FIG_DIR / "restaurant_clusters_enriched.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")

print(f"Figure saved to: {output_path}")

plt.close()