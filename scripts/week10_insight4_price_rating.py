from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "restaurants_enriched.csv"
OUT_PATH = BASE_DIR / "data" / "figures" / "week10" / "price_vs_rating.png"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(DATA_PATH)

# clean data
df = df[
    ["price_level", "rating"]
].dropna()

df["price_level"] = df["price_level"].astype(int)


# group by price level and calculate average rating
grouped = (
    df.groupby("price_level")["rating"]
    .mean()
    .reset_index()
)

print(grouped)

# plot
plt.figure(figsize=(6,4))

plt.bar(
    grouped["price_level"],
    grouped["rating"],
    color=["green", "blue", "orange", "red"],
)

plt.xlabel("Price Level")
plt.ylabel("Average Rating")
plt.title("Average Rating by Price Level")

plt.ylim(3.5, 5)

plt.savefig(OUT_PATH, dpi=150)
plt.show()

print("Saved:", OUT_PATH)