import streamlit as st
import pandas as pd
import altair as alt
from utils import load_data, filter_data, format_number

st.set_page_config(
    page_title="Overview",
    layout="wide"
)

df = load_data()

# Sidebar 
st.sidebar.title("Filters")

city_options = ["All"] + sorted(df["city"].unique().tolist())
selected_city = st.sidebar.selectbox("City", city_options)

price_options = sorted(df["price_level"].unique().tolist())
selected_price = st.sidebar.multiselect(
    "Price Level",
    price_options,
    default=price_options
)

min_rating = float(df["rating"].min())
max_rating = float(df["rating"].max())

rating_range = st.sidebar.slider(
    "Rating",
    min_value=min_rating,
    max_value=max_rating,
    value=(min_rating, max_rating)
)

keyword = st.sidebar.text_input("Search name")

filtered = filter_data(
    df,
    city=selected_city,
    price_levels=selected_price,
    rating_range=rating_range,
    keyword=keyword
)

# Header 
st.title("Restaurant Intelligence Dashboard")
st.markdown(
    "Explore restaurant patterns across major U.S. cities through ratings, reviews, and price levels."
)

# KPI Row 
col1, col2, col3, col4 = st.columns(4)

col1.metric("Restaurants", format_number(len(filtered)))
col2.metric("Avg Rating", f"{filtered['rating'].mean():.2f}" if len(filtered) else "N/A")
col3.metric(
    "Avg Reviews",
    format_number(filtered["user_ratings_total"].mean()) if len(filtered) else "N/A"
)
col4.metric("Cities", filtered["city"].nunique() if len(filtered) else 0)

st.divider()

# Main Chart 
st.subheader("Rating Distribution")

rating_dist = (
    filtered["rating"]
    .value_counts()
    .sort_index()
    .reset_index()
)
rating_dist.columns = ["rating", "count"]
rating_dist["rating"] = rating_dist["rating"].astype(str)

rating_chart = (
    alt.Chart(rating_dist)
    .mark_bar()
    .encode(
        x=alt.X("rating:N", title="Rating", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("count:Q", title="Restaurant Count"),
        tooltip=["rating", "count"]
    )
    .properties(height=350)
    .interactive()
)

st.altair_chart(rating_chart, width="stretch")

st.divider()

# Bottom Section 
st.subheader("Overview Details")
left_col, right_col = st.columns([1.25, 1])

with left_col:
    st.markdown("### Top Restaurants")

    top_restaurants = (
        filtered[
            ["name", "city", "rating", "user_ratings_total", "price_level"]
        ]
        .sort_values(["rating", "user_ratings_total"], ascending=[False, False])
        .head(5)
    )

    for _, row in top_restaurants.iterrows():
        st.markdown(
            f"""
            <div style="
                padding: 16px;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
                margin-bottom: 12px;
                background-color: #111111;
            ">
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 4px;">
                    {row['name']}
                </div>
                <div style="font-size: 14px; color: #bbbbbb; margin-bottom: 8px;">
                    {row['city']} · Price Level {row['price_level']}
                </div>
                <div style="font-size: 14px;">
                    ⭐ Rating: {row['rating']} &nbsp;&nbsp; | &nbsp;&nbsp; 📝 Reviews: {int(row['user_ratings_total'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

with right_col:
    st.markdown("### Restaurant Count by City")
    city_counts = (
        filtered["city"]
        .value_counts()
        .reset_index()
    )
    city_counts.columns = ["city", "count"]

    city_chart = (
        alt.Chart(city_counts)
        .mark_bar()
        .encode(
            x=alt.X("city:N", title="City", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("count:Q", title="Restaurant Count"),
            tooltip=["city", "count"]
        )
        .properties(height=250)
        .interactive()
    )

    st.altair_chart(city_chart, width="stretch")

    st.markdown("### Price Level Distribution")
    price_dist = (
        filtered["price_level"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    price_dist.columns = ["price_level", "count"]
    price_dist["price_level"] = price_dist["price_level"].astype(str)

    price_chart = (
        alt.Chart(price_dist)
        .mark_bar()
        .encode(
            x=alt.X("price_level:N", title="Price Level", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("count:Q", title="Restaurant Count"),
            tooltip=["price_level", "count"]
        )
        .properties(height=250)
        .interactive()
    )

    st.altair_chart(price_chart, width="stretch")