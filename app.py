import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="Books Scraper", page_icon="📚", layout="wide")

st.title("📚 Books to Scrape — Web Scraper")
st.markdown("Scrapes live data from [books.toscrape.com](https://books.toscrape.com)")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Settings")
num_pages = st.sidebar.slider("Number of pages to scrape", min_value=1, max_value=50, value=1)
rating_filter = st.sidebar.multiselect(
    "Filter by Rating",
    options=["One", "Two", "Three", "Four", "Five"],
    default=["One", "Two", "Three", "Four", "Five"]
)

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def scrape_page(page_num):
    url = f"https://books.toscrape.com/catalogue/page-{page_num}.html"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.product_pod")
    items = []
    for article in articles:
        title = article.find("h3").find("a")["title"]
        price_text = article.select_one("p.price_color").text.strip()
        # Fix encoding issue — extract numeric value
        price = float(''.join(c for c in price_text if c.isdigit() or c == '.'))
        rating_class = article.select_one("p.star-rating")["class"][1]
        items.append({"Book": title, "Price (£)": price, "Rating": rating_class})
    return items

# --- Scrape button ---
if st.button("🚀 Start Scraping", use_container_width=True):
    all_items = []
    progress = st.progress(0, text="Starting...")
    for i in range(1, num_pages + 1):
        progress.progress(i / num_pages, text=f"Scraping page {i} of {num_pages}...")
        all_items.extend(scrape_page(i))
    progress.empty()

    if all_items:
        df = pd.DataFrame(all_items)
        df["Rating Stars"] = df["Rating"].map(RATING_MAP)

        # Apply filter
        df_filtered = df[df["Rating"].isin(rating_filter)].reset_index(drop=True)

        st.success(f"✅ Scraped **{len(df_filtered)}** books from **{num_pages}** page(s).")

        # --- Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Books", len(df_filtered))
        col2.metric("Avg Price (£)", f"£{df_filtered['Price (£)'].mean():.2f}")
        col3.metric("Cheapest (£)", f"£{df_filtered['Price (£)'].min():.2f}")
        col4.metric("Most Expensive (£)", f"£{df_filtered['Price (£)'].max():.2f}")

        st.markdown("---")

        # --- Charts ---
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📊 Books per Rating")
            rating_counts = df_filtered["Rating"].value_counts().reindex(
                ["One", "Two", "Three", "Four", "Five"]
            ).fillna(0)
            st.bar_chart(rating_counts)

        with col_b:
            st.subheader("💰 Avg Price by Rating")
            avg_price = df_filtered.groupby("Rating")["Price (£)"].mean().reindex(
                ["One", "Two", "Three", "Four", "Five"]
            ).fillna(0)
            st.bar_chart(avg_price)

        st.markdown("---")

        # --- Table ---
        st.subheader("📋 Scraped Data")
        sort_col = st.selectbox("Sort by", ["Book", "Price (£)", "Rating Stars"])
        sort_asc = st.radio("Order", ["Ascending", "Descending"], horizontal=True) == "Ascending"
        df_sorted = df_filtered.sort_values(sort_col, ascending=sort_asc).reset_index(drop=True)
        st.dataframe(df_sorted[["Book", "Price (£)", "Rating"]], use_container_width=True)

        # --- Download ---
        csv_buf = io.StringIO()
        df_sorted[["Book", "Price (£)", "Rating"]].to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_buf.getvalue(),
            file_name="scraped_books.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.error("No data scraped. Check your connection.")
else:
    st.info("👈 Set your preferences in the sidebar and click **Start Scraping** to begin.")
