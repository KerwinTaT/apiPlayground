from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "restaurants_enriched.csv"
OUT_PATH = BASE_DIR / "data" / "figures" / "week10" / "rating_vs_reviews.png"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(DATA_PATH)

# clean data
df = df[
    ["rating", "user_ratings_total"]
].dropna()


df = df[df["user_ratings_total"] > 0]
df_sample = df.sample(2000, random_state=1)


# plot
plt.figure(figsize=(6,5))

plt.scatter(
    df_sample["user_ratings_total"],
    df_sample["rating"],
    alpha=0.15,
    s=10,
)

plt.xlabel("Number of Reviews")
plt.ylabel("Rating")

plt.title("Rating vs Review Count")

plt.xscale("log")

plt.ylim(3, 5)

plt.grid(True, alpha=0.3)

z = np.polyfit(
    np.log(df_sample["user_ratings_total"]),
    df_sample["rating"],
    1,
)

p = np.poly1d(z)

x = np.linspace(
    df_sample["user_ratings_total"].min(),
    df_sample["user_ratings_total"].max(),
    100,
)

plt.plot(
    x,
    p(np.log(x)),
    color="red",
    linewidth=2,
)

plt.savefig(OUT_PATH, dpi=150)
plt.show()

print("Saved:", OUT_PATH)