import streamlit as st
import altair as alt
from utils import load_data, filter_data, format_number

st.set_page_config(
    page_title="Price Level Analysis",
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

st.title("Price Level Analysis")
st.markdown(
    "Compare restaurant volume, average rating, and review activity across price segments."
)

if len(filtered) == 0:
    st.warning("No data available for the selected filters.")
else:
    summary = (
        filtered.groupby("price_level")
        .agg(
            restaurant_count=("place_id", "count"),
            avg_rating=("rating", "mean"),
            avg_reviews=("user_ratings_total", "mean")
        )
        .reset_index()
        .sort_values("price_level")
    )

    summary["price_level_str"] = summary["price_level"].astype(str)

    # Price Level Explanation
    st.caption(
    "Price level scale: "
    )
    st.caption( 
    "0 = Unknown, 1 = Cheap, 2 = Moderate, 3 = Expensive, 4 = Very Expensive"
    )

    # KPI 
    col1, col2, col3 = st.columns(3)
    col1.metric("Restaurants", format_number(len(filtered)))
    col2.metric("Price Levels Shown", summary["price_level"].nunique())
    col3.metric("Overall Avg Rating", f"{filtered['rating'].mean():.2f}")

    st.divider()

    # Charts 
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Restaurant Count by Price Level")

        chart_count = (
            alt.Chart(summary)
            .mark_bar()
            .encode(
                x=alt.X("price_level_str:N", title="Price Level", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("restaurant_count:Q", title="Restaurant Count"),
                tooltip=[
                    alt.Tooltip("price_level_str:N", title="Price Level"),
                    alt.Tooltip("restaurant_count:Q", title="Restaurant Count", format=",")
                ],
            )
            .properties(height=300)
            .interactive()
        )

        st.altair_chart(chart_count, width="stretch")

    with col_b:
        st.subheader("Average Rating by Price Level")

        chart_rating = (
            alt.Chart(summary)
            .mark_bar()
            .encode(
                x=alt.X("price_level_str:N", title="Price Level", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("avg_rating:Q", title="Average Rating"),
                tooltip=[
                    alt.Tooltip("price_level_str:N", title="Price Level"),
                    alt.Tooltip("avg_rating:Q", title="Average Rating", format=".2f")
                ],
            )
            .properties(height=300)
            .interactive()
        )

        st.altair_chart(chart_rating, width="stretch")

    st.subheader("Average Reviews by Price Level")

    chart_reviews = (
        alt.Chart(summary)
        .mark_bar()
        .encode(
            x=alt.X("price_level_str:N", title="Price Level", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("avg_reviews:Q", title="Average Reviews"),
            tooltip=[
                alt.Tooltip("price_level_str:N", title="Price Level"),
                alt.Tooltip("avg_reviews:Q", title="Average Reviews", format=".0f")
            ],
        )
        .properties(height=300)
        .interactive()
    )

    st.altair_chart(chart_reviews, width="stretch")

    st.divider()

    # Summary Cards 
    st.subheader("Price Segment Summary")

    card_col1, card_col2 = st.columns(2)

    for i, (_, row) in enumerate(summary.iterrows()):
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
                        Price Level {int(row['price_level'])}
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

    st.divider()

    #  Interpretation 
    st.subheader("Key Takeaways")

    top_rating_level = int(summary.loc[summary["avg_rating"].idxmax(), "price_level"])
    top_review_level = int(summary.loc[summary["avg_reviews"].idxmax(), "price_level"])
    top_count_level = int(summary.loc[summary["restaurant_count"].idxmax(), "price_level"])

    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            margin-bottom: 12px;
            background-color: #111111;
        ">
            <div style="font-size: 16px; margin-bottom: 8px;">
                <strong>Most common segment:</strong> Price Level {top_count_level} has the largest number of restaurants.
            </div>
            <div style="font-size: 16px; margin-bottom: 8px;">
                <strong>Highest average rating:</strong> Price Level {top_rating_level} performs best on average rating.
            </div>
            <div style="font-size: 16px;">
                <strong>Most visible segment:</strong> Price Level {top_review_level} has the highest average review volume.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )