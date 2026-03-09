import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "restaurants_enriched.csv"

FIG_DIR = BASE_DIR / "data" / "figures" / "week10"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
df = df[["city", "types"]].dropna()
df["types"] = df["types"].str.replace("[", "", regex=False)
df["types"] = df["types"].str.replace("]", "", regex=False)
df["types"] = df["types"].str.replace("'", "", regex=False)
df["types"] = df["types"].str.replace('"', "", regex=False)

# Split types
df["types"] = df["types"].str.split(",")

df = df.explode("types")

df["types"] = df["types"].str.strip().str.lower()

# Remove generic types
REMOVE = [
    "restaurant",
    "food",
    "establishment",
    "point_of_interest",
]

df = df[~df["types"].isin(REMOVE)]

df["types"] = df["types"].str.replace("_", " ")

# Count per city + type
counts = (
    df.groupby(["city", "types"])
    .size()
    .reset_index(name="count")
)

# Top 5 per city
top_types = (
    counts.sort_values(["city", "count"], ascending=False)
    .groupby("city")
    .head(5)
)

# Plot
COLOR_MAP = {
    "bar": "#1f77b4",
    "store": "#ff7f0e",
    "meal takeaway": "#2ca02c",
    "cafe": "#d62728",
    "meal delivery": "#9467bd",
    "restaurant": "#8c564b",
    "bakery": "#e377c2",
}

cities = top_types["city"].unique()

plt.figure(figsize=(10, 8))

for i, city in enumerate(cities, 1):

    plt.subplot(len(cities), 1, i)

    subset = top_types[top_types["city"] == city]

    subset = subset.sort_values("count")

    colors = [
        COLOR_MAP.get(t, "#7f7f7f") 
        for t in subset["types"]
    ]

    plt.barh(
        subset["types"],
        subset["count"],
        color=colors,
    )

    plt.title(city)

    plt.xlabel("Count")

plt.tight_layout()

# Save figure
out_path = FIG_DIR / "cuisine_by_city_clean.png"
plt.savefig(out_path, dpi=150)
print("Saved:", out_path)
plt.show()