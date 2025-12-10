import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy
from src.config import Config
import logging

# Setup Page
st.set_page_config(page_title="ASOS Analytics Dashboard", layout="wide")
st.title("👗 ASOS Product Analytics Dashboard")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    engine = sqlalchemy.create_engine(Config().DATABASE_URL)
    
    # Query: Join Products with Features and Dimensions
    query = """
    SELECT 
        p.product_id, p.name, p.sku, p.base_price, p.description_clean,
        b.brand_name, c.category_name, col.color_name,
        f.price_zscore, f.cluster_id
    FROM dim_product p
    JOIN dim_brand b ON p.brand_id = b.brand_id
    JOIN dim_category c ON p.category_id = c.category_id
    LEFT JOIN dim_color col ON p.color_id = col.color_id
    LEFT JOIN fact_product_features f ON p.product_id = f.product_id
    WHERE p.base_price IS NOT NULL
    """
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Ensure ETL has run successfully.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")

# Category Filter
categories = ['All'] + sorted(df['category_name'].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

# Brand Filter
brands = ['All'] + sorted(df['brand_name'].dropna().unique().tolist())
selected_brand = st.sidebar.selectbox("Brand", brands)

# Filter Logic
df_filtered = df.copy()
if selected_category != 'All':
    df_filtered = df_filtered[df_filtered['category_name'] == selected_category]
if selected_brand != 'All':
    df_filtered = df_filtered[df_filtered['brand_name'] == selected_brand]

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Products", f"{len(df_filtered):,}")
col2.metric("Avg Price", f"£{df_filtered['base_price'].mean():.2f}")
col3.metric("Unique Brands", f"{df_filtered['brand_name'].nunique()}")
col4.metric("Unique Categories", f"{df_filtered['category_name'].nunique()}")

st.markdown("---")

# --- VISUALIZATIONS ---

# Row 1: Price Dist + Scatter
c1, c2 = st.columns(2)

with c1:
    st.subheader("Price Distribution")
    fig_hist = px.histogram(df_filtered, x="base_price", nbins=50, title="Price Distribution", color_discrete_sequence=['#2ecc71'])
    st.plotly_chart(fig_hist, use_container_width=True)

with c2:
    st.subheader("Price vs. Category (Z-Score)")
    # Scatter plot of Z-Score vs Price, colored by Cluster
    if 'cluster_id' in df_filtered.columns:
        df_filtered['cluster_label'] = df_filtered['cluster_id'].astype(str)
        fig_scatter = px.scatter(
            df_filtered, x="base_price", y="price_zscore", color="cluster_label",
            hover_data=['name', 'brand_name'],
            title="Price vs. Standardized Price (coloured by Cluster)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Cluster data not available.")

# Row 2: Top Brands
st.subheader("Top 10 Brands in Selection")
top_brands = df_filtered['brand_name'].value_counts().head(10).reset_index()
top_brands.columns = ['Brand', 'Count']
fig_bar = px.bar(top_brands, x='Count', y='Brand', orientation='h', title="Top Brands", color='Count', color_continuous_scale='Blues')
st.plotly_chart(fig_bar, use_container_width=True)

# --- DATA TABLE ---
st.subheader("Product Details")
st.dataframe(df_filtered[['name', 'brand_name', 'category_name', 'base_price', 'color_name', 'cluster_id', 'description_clean']].head(100))
