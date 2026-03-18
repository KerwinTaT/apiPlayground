import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "processed" / "restaurants_enriched.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    df["city"] = df["city"].astype(str)

    if "price_level" in df.columns:
        df["price_level"] = df["price_level"].fillna(0).astype(int)

    if "rating" in df.columns:
        df = df[df["rating"].notna()]

    if "user_ratings_total" in df.columns:
        df["user_ratings_total"] = df["user_ratings_total"].fillna(0)

    return df


def filter_data(df, city="All", price_levels=None, rating_range=None, keyword=""):
    filtered = df.copy()

    if city != "All":
        filtered = filtered[filtered["city"] == city]

    if price_levels:
        filtered = filtered[filtered["price_level"].isin(price_levels)]

    if rating_range:
        filtered = filtered[
            (filtered["rating"] >= rating_range[0]) &
            (filtered["rating"] <= rating_range[1])
        ]

    if keyword:
        filtered = filtered[
            filtered["name"].str.contains(keyword, case=False, na=False)
        ]

    return filtered


def format_number(n):
    return f"{int(n):,}"