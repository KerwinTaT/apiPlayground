import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "restaurants_enriched.csv"

FIG_DIR = BASE_DIR / "data" / "figures" / "week10"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
df = df[
    [
        "census_name",
        "population_total",
        "median_household_income",
    ]
].dropna()

# restaurant count per area
counts = (
    df.groupby("census_name")
    .size()
    .reset_index(name="restaurant_count")
)

# population per area
pop = (
    df.groupby("census_name")["population_total"]
    .mean()
    .reset_index()
)

# income per area
income = (
    df.groupby("census_name")["median_household_income"]
    .mean()
    .reset_index()
)

# merge
merged = counts.merge(pop, on="census_name")

merged = merged.merge(income, on="census_name")

# density
merged["density_per_1000"] = (
    merged["restaurant_count"]
    / merged["population_total"]
    * 1000
)

print(merged.head())

# Plot
colors = {
    "Chicago": "red",
    "Los Angeles": "green",
    "New York": "orange",
    "San Francisco": "purple",
}

plt.figure(figsize=(6, 6))

for _, row in merged.iterrows():

    name = row["census_name"].split(",")[0]

    for city in colors:
        if city in name:
            c = colors[city]

    x = row["median_household_income"]
    y = row["density_per_1000"]

    plt.scatter(
        x,
        y,
        s=250,
        color=c,
        edgecolor="black"
    )

    # label offset
    dx = 1000
    dy = 0.02

    if "Los Angeles" in name:
        dx = -4000
        dy = 0.02

    if "New York" in name:
        dx = 1000
        dy = -0.03

    plt.text(x + dx, y + dy, name)

plt.xlabel("Income")
plt.ylabel("Restaurants per 1000")
plt.title("Restaurant Density vs Income (by City)")
plt.grid(True)

out_path = FIG_DIR / "density_vs_income.png"

plt.savefig(out_path, dpi=150)

print("Saved:", out_path)

plt.show()