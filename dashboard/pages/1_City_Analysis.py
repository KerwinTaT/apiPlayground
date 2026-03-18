import streamlit as st
import altair as alt
from utils import load_data, filter_data, format_number

st.set_page_config(
    page_title="City Analysis",
    layout="wide"
)

df = load_data()

# Sidebar 
st.sidebar.title("Filters")

city_options = ["All"] + sorted(df["city"].unique())
selected_city = st.sidebar.selectbox("City", city_options)

price_options = sorted(df["price_level"].unique())
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

st.title("City Analysis")

# ALL CITIES VIEW
if selected_city == "All":
    st.subheader("City Comparison")

    city_summary = (
        filtered.groupby("city")
        .agg(
            restaurant_count=("place_id", "count"),
            avg_rating=("rating", "mean"),
            avg_reviews=("user_ratings_total", "mean"),
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        chart1 = (
            alt.Chart(city_summary)
            .mark_bar()
            .encode(
                x=alt.X("city:N", title="City", axis=alt.Axis(labelAngle=-35)),
                y=alt.Y("restaurant_count:Q", title="Restaurant Count"),
                tooltip=[
                    alt.Tooltip("city:N", title="City"),
                    alt.Tooltip("restaurant_count:Q", title="Restaurant Count", format=",")
                ],
            )
            .properties(height=300)
            .interactive()
        )
        st.altair_chart(chart1, width="stretch")

    with col2:
        chart2 = (
            alt.Chart(city_summary)
            .mark_bar()
            .encode(
                x=alt.X("city:N", title="City", axis=alt.Axis(labelAngle=-35)),
                y=alt.Y("avg_rating:Q", title="Average Rating"),
                tooltip=[
                    alt.Tooltip("city:N", title="City"),
                    alt.Tooltip("avg_rating:Q", title="Average Rating", format=".2f")
                ],
            )
            .properties(height=300)
            .interactive()
        )
        st.altair_chart(chart2, width="stretch")

    st.subheader("City Summary")

    card_col1, card_col2 = st.columns(2)

    for i, (_, row) in enumerate(city_summary.iterrows()):
        target_col = card_col1 if i % 2 == 0 else card_col2

        with target_col:
            st.markdown(
                f"""
                <div style="
                    padding: 16px;
                    border: 1px solid #2a2a2a;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    background-color: #111111;
                ">
                    <div style="font-size: 20px; font-weight: 700; margin-bottom: 8px;">
                        {row['city']}
                    </div>
                    <div style="font-size: 14px; margin-bottom: 6px;">
                        🍽️ Restaurants: {int(row['restaurant_count']):,}
                    </div>
                    <div style="font-size: 14px; margin-bottom: 6px;">
                        ⭐ Average Rating: {row['avg_rating']:.2f}
                    </div>
                    <div style="font-size: 14px;">
                        📝 Average Reviews: {row['avg_reviews']:.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# SINGLE CITY VIEW
else:
    city_df = filtered[filtered["city"] == selected_city]

    st.subheader(f"{selected_city} Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Restaurants", format_number(len(city_df)))
    col2.metric("Avg Rating", f"{city_df['rating'].mean():.2f}" if len(city_df) else "N/A")
    col3.metric(
        "Avg Reviews",
        format_number(city_df["user_ratings_total"].mean()) if len(city_df) else "N/A"
    )

    st.divider()

    st.subheader("Rating Distribution")

    rating_dist = (
        city_df["rating"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    rating_dist.columns = ["rating", "count"]
    rating_dist["rating"] = rating_dist["rating"].astype(str)

    chart3 = (
        alt.Chart(rating_dist)
        .mark_bar()
        .encode(
            x=alt.X("rating:N", title="Rating", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("count:Q", title="Restaurant Count"),
            tooltip=[
                alt.Tooltip("rating:N", title="Rating"),
                alt.Tooltip("count:Q", title="Restaurant Count", format=",")
            ],
        )
        .properties(height=300)
        .interactive()
    )
    st.altair_chart(chart3, width="stretch")

    st.subheader("Price Level Distribution")

    price_dist = (
        city_df["price_level"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    price_dist.columns = ["price_level", "count"]
    price_dist["price_level"] = price_dist["price_level"].astype(str)

    chart4 = (
        alt.Chart(price_dist)
        .mark_bar()
        .encode(
            x=alt.X("price_level:N", title="Price Level"),
            y=alt.Y("count:Q", title="Restaurant Count"),
            tooltip=[
                alt.Tooltip("price_level:N", title="Price Level"),
                alt.Tooltip("count:Q", title="Restaurant Count", format=",")
            ],
        )
        .properties(height=300)
        .interactive()
    )
    st.altair_chart(chart4, width="stretch")

    st.subheader("Top Restaurants")

    top_restaurants = (
        city_df[
            ["name", "rating", "user_ratings_total", "price_level"]
        ]
        .sort_values(
            ["rating", "user_ratings_total"],
            ascending=[False, False],
        )
        .head(8)
        .copy()
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
                    {selected_city} · Price Level {int(row['price_level'])}
                </div>
                <div style="font-size: 14px;">
                    ⭐ Rating: {row['rating']:.1f} &nbsp;&nbsp; | &nbsp;&nbsp; 📝 Reviews: {int(row['user_ratings_total']):,}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )