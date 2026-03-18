import streamlit as st
import altair as alt
from utils import load_data, filter_data, format_number

st.set_page_config(
    page_title="Rating vs Reviews",
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
    min_rating,
    max_rating,
    (min_rating, max_rating)
)

keyword = st.sidebar.text_input("Search name")

filtered = filter_data(
    df,
    city=selected_city,
    price_levels=selected_price,
    rating_range=rating_range,
    keyword=keyword
)

st.title("Rating vs Reviews Analysis")

# Scatter Plot

st.subheader("Rating vs Number of Reviews")

chart = (
    alt.Chart(filtered)
    .mark_circle(size=40, opacity=0.5)
    .encode(
        x=alt.X(
            "user_ratings_total:Q",
            title="Number of Reviews",
            scale=alt.Scale(type="log"),
        ),
        y=alt.Y(
            "rating:Q",
            title="Rating",
        ),
        color=alt.Color(
            "city:N",
            legend=alt.Legend(title="City"),
        ),
        tooltip=[
            "name",
            "city",
            "rating",
            "user_ratings_total",
            "price_level",
        ],
    )
    .interactive()
)

st.altair_chart(chart, width="stretch")


# Summary stats

st.subheader("Summary")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Restaurants",
    format_number(len(filtered))
)

col2.metric(
    "Avg Rating",
    f"{filtered['rating'].mean():.2f}"
)

col3.metric(
    "Avg Reviews",
    format_number(filtered["user_ratings_total"].mean())
)

st.divider()

# High review restaurants

st.subheader("Most Reviewed Restaurants")

top = (
    filtered[
        ["name", "city", "rating", "user_ratings_total", "price_level"]
    ]
    .sort_values("user_ratings_total", ascending=False)
    .head(8)
    .copy()
)

for _, row in top.iterrows():
    st.markdown(
        f"""
<div style="
    padding: 16px;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    margin-bottom: 12px;
    background-color: #111111;
">
    <div style="font-size: 18px; font-weight: 600; margin-bottom: 6px;">
        {row['name']}
    </div>
    <div style="font-size: 14px; color: #bbbbbb; margin-bottom: 8px;">
        {row['city']} · Price Level {int(row['price_level'])}
    </div>
    <div style="font-size: 14px;">
        ⭐ Rating: {row['rating']:.1f}
        &nbsp;&nbsp;|&nbsp;&nbsp;
        📝 Reviews: {int(row['user_ratings_total']):,}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )