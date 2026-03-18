import streamlit as st
from utils import load_data, filter_data, format_number

st.set_page_config(
    page_title="Business Insights",
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

st.title("Business Insights")
st.markdown(
    "Summary of key patterns discovered from restaurant data across cities and price segments."
)

if len(filtered) == 0:
    st.warning("No data available.")
    st.stop()

# Summary Metrics

col1, col2, col3 = st.columns(3)

col1.metric(
    "Restaurants",
    format_number(len(filtered))
)

col2.metric(
    "Average Rating",
    f"{filtered['rating'].mean():.2f}"
)

col3.metric(
    "Average Reviews",
    format_number(filtered["user_ratings_total"].mean())
)

st.divider()

# Compute stats

price_summary = (
    filtered.groupby("price_level")
    .agg(
        count=("place_id", "count"),
        rating=("rating", "mean"),
        reviews=("user_ratings_total", "mean"),
    )
)

top_price_count = price_summary["count"].idxmax()
top_price_rating = price_summary["rating"].idxmax()
top_price_reviews = price_summary["reviews"].idxmax()

city_summary = (
    filtered.groupby("city")
    .agg(
        count=("place_id", "count"),
        rating=("rating", "mean"),
    )
)

top_city = city_summary["count"].idxmax()

# Key Insights

st.subheader("Key Insights")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>Most common price level</b><br><br>
            Price Level {top_price_count} has the largest number of restaurants.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
            <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>Highest rated segment</b><br><br>
            Price Level {top_price_rating} has the highest average rating.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>Most reviewed segment</b><br><br>
            Price Level {top_price_reviews} has the highest review activity.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Recommendations

st.subheader("Business Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>Focus on mid-price market</b><br><br>
            Moderate price restaurants have the highest volume,
            making them the most competitive segment.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>Higher price → higher rating</b><br><br>
            Expensive restaurants tend to have higher ratings,
            suggesting quality perception matters.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div style="
            padding:16px;
            border:1px solid #2a2a2a;
            border-radius:12px;
            background:#111111;
        ">
            <b>City opportunity</b><br><br>
            {top_city} has the largest restaurant market.
            Expansion here may have the highest impact.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Final note

st.caption(
    "Insights are based on Google Places restaurant data across selected cities."
)