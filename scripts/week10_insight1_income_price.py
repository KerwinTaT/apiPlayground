import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "restaurants_enriched.csv"
FIG_DIR = BASE_DIR / "data" / "figures" / "week10"

FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

# Keep needed columns only
df = df[
    [
        "median_household_income",
        "price_level",
    ]
].dropna()

# Remove invalid price levels (0 or negative)
df = df[df["price_level"] > 0]

# Create income groups
df["income_group"] = pd.qcut(
    df["median_household_income"],
    4,
    duplicates="drop",
)

df["income_group"] = df["income_group"].astype(str)

# Aggregate price level by income group
grouped = (
    df.groupby("income_group", as_index=False)["price_level"]
    .mean()
    .reset_index()
)

print(grouped)

# Plot
plt.figure(figsize=(8, 5))

plt.bar(
    grouped["income_group"],
    grouped["price_level"],
)

plt.xlabel("Income Group")
plt.ylabel("Average Price Level")
plt.title("Average Restaurant Price Level by Income Group")

plt.grid(axis="y")

# Save figure
out_path = FIG_DIR / "income_vs_price.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print("Saved:", out_path)
plt.show()