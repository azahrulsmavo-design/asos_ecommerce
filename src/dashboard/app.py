import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlalchemy
import sys
import os
from datetime import datetime, timedelta

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config

# --- CONFIGURATION ---
st.set_page_config(
    page_title="ASOS Retail Intelligence", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #2d3436; }
    .metric-label { font-size: 14px; color: #636e72; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #2d3436; }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    engine = sqlalchemy.create_engine(Config().DATABASE_URL)
    
    # 1. Sales Data (Fact + Dims)
    q_sales = """
    SELECT 
        s.date, s.time, s.quantity, s.unit_price, s.total_amount, s.profit, s.payment_method, s.channel,
        st.store_name, st.region,
        p.name as product_name, p.sku, p.base_price, c.category_name, b.brand_name,
        cus.gender, cus.age, cus.region as customer_region
    FROM fact_sales s
    JOIN dim_store st ON s.store_id = st.store_id
    JOIN dim_product p ON s.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    LEFT JOIN dim_brand b ON p.brand_id = b.brand_id
    LEFT JOIN dim_customer cus ON s.customer_id = cus.customer_id
    """
    
    # 2. Inventory Data
    q_inv = """
    SELECT i.stock_on_hand, i.reorder_point, i.last_restock_date,
           p.name as product_name, p.sku, st.store_name
    FROM fact_inventory i
    JOIN dim_product p ON i.product_id = p.product_id
    JOIN dim_store st ON i.store_id = st.store_id
    """
    
    try:
        with engine.connect() as conn:
            df_sales = pd.read_sql(q_sales, conn)
            df_inv = pd.read_sql(q_inv, conn)
            
        # Ensure dates are datetime
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        
        return df_sales, df_inv
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_sales_raw, df_inv_raw = load_data()

if df_sales_raw.empty:
    st.error("No data found. Please run 'python src/etl/generate_mock_data.py' first.")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛍️ ASOS Retail AI")
pages = [
    "1. Executive Summary", 
    "2. Sales Performance", 
    "3. Product Performance", 
    "4. Inventory Management", 
    "5. Customer Analysis", 
    "6. Promotion & Campaign", 
    "7. Store Operations", 
    "8. Forecasting"
]
selected_page = st.sidebar.radio("Navigation", pages)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Date Filter
min_date = df_sales_raw['date'].min()
max_date = df_sales_raw['date'].max()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Store Filter
all_stores = ['All'] + sorted(df_sales_raw['store_name'].unique().tolist())
selected_store = st.sidebar.selectbox("Store", all_stores)

# Category Filter
all_cats = ['All'] + sorted(df_sales_raw['category_name'].unique().tolist())
selected_cat = st.sidebar.selectbox("Category", all_cats)

# --- FILTERING LOGIC ---
mask = (df_sales_raw['date'] >= pd.to_datetime(date_range[0])) & (df_sales_raw['date'] <= pd.to_datetime(date_range[1]))
if selected_store != 'All':
    mask &= (df_sales_raw['store_name'] == selected_store)
if selected_cat != 'All':
    mask &= (df_sales_raw['category_name'] == selected_cat)

df_filtered = df_sales_raw.loc[mask]

# --- PAGE IMPLEMENTATIONS ---

def format_currency(val):
    return f"£{val:,.2f}"

if selected_page == "1. Executive Summary":
    st.title("📊 Executive Summary")
    
    # KPIs
    total_rev = df_filtered['total_amount'].sum()
    total_orders = len(df_filtered)
    gross_profit = df_filtered['profit'].sum()
    margin = (gross_profit / total_rev * 100) if total_rev > 0 else 0
    aov = total_rev / total_orders if total_orders > 0 else 0
    basket_size = df_filtered['quantity'].mean()
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", format_currency(total_rev), delta="Target: £1M")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Gross Profit", format_currency(gross_profit))
    c4.metric("Profit Margin", f"{margin:.1f}%")
    c5.metric("AOV", format_currency(aov))
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Sales Trend (Daily)")
        daily_sales = df_filtered.groupby('date')['total_amount'].sum().reset_index()
        fig_trend = px.line(daily_sales, x='date', y='total_amount', title="Daily Revenue", template="plotly_white")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col2:
        st.subheader("Top 5 Categories")
        top_cat = df_filtered.groupby('category_name')['total_amount'].sum().nlargest(5).reset_index()
        fig_pie = px.pie(top_cat, values='total_amount', names='category_name', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

elif selected_page == "2. Sales Performance":
    st.title("📈 Sales Performance")
    
    # Heatmap
    st.subheader("Sales Heatmap (Hour vs Day)")
    df_heat = df_filtered.copy()
    df_heat['hour'] = pd.to_datetime(df_heat['time'], format='%H:%M:%S').dt.hour
    df_heat['day_of_week'] = df_heat['date'].dt.day_name()
    
    heatmap_data = df_heat.pivot_table(index='day_of_week', columns='hour', values='total_amount', aggfunc='sum')
    # Sort days
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(days_order)
    
    fig_heat = px.imshow(heatmap_data, labels=dict(x="Hour", y="Day", color="Revenue"), color_continuous_scale="Viridis")
    st.plotly_chart(fig_heat, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Revenue by Payment Method")
        fig_pay = px.bar(df_filtered.groupby('payment_method')['total_amount'].sum().reset_index(), 
                         x='payment_method', y='total_amount', color='payment_method')
        st.plotly_chart(fig_pay, use_container_width=True)
        
    with c2:
        st.subheader("Online vs Offline Channel")
        fig_chan = px.pie(df_filtered.groupby('channel')['total_amount'].sum().reset_index(), 
                          values='total_amount', names='channel')
        st.plotly_chart(fig_chan, use_container_width=True)

elif selected_page == "3. Product Performance":
    st.title("👗 Product Performance")
    
    # Aggregates
    prod_perf = df_filtered.groupby('product_name').agg(
        Total_Revenue=('total_amount', 'sum'),
        Qty_Sold=('quantity', 'sum'),
        Total_Profit=('profit', 'sum')
    ).reset_index()
    prod_perf['Margin'] = prod_perf['Total_Profit'] / prod_perf['Total_Revenue']
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 Selling Products")
        st.dataframe(prod_perf.nlargest(10, 'Qty_Sold').style.format({'Total_Revenue': '£{:.2f}', 'Margin': '{:.1%}'}), use_container_width=True)
        
    with c2:
        st.subheader("Most Profitable Products")
        st.dataframe(prod_perf.nlargest(10, 'Total_Profit').style.format({'Total_Revenue': '£{:.2f}', 'Margin': '{:.1%}'}), use_container_width=True)

    st.subheader("Price Elasticity Proxy (Price vs Qty)")
    # Need avg price per product (incase of variations, but mock has fixed base price + discount)
    # Let's join back with base_price from product dim or avg unit_price
    prod_price = df_filtered.groupby('product_name')['unit_price'].mean().reset_index()
    scatter_data = prod_perf.merge(prod_price, on='product_name')
    
    fig_scat = px.scatter(scatter_data, x='unit_price', y='Qty_Sold', size='Total_Revenue', 
                          hover_name='product_name', title="Price vs Quantity Sold")
    st.plotly_chart(fig_scat, use_container_width=True)

elif selected_page == "4. Inventory Management":
    st.title("📦 Inventory Management")
    
    # Filter inventory by store if selected
    df_inv_curr = df_inv_raw.copy()
    if selected_store != 'All':
        df_inv_curr = df_inv_curr[df_inv_curr['store_name'] == selected_store]
        
    c1, c2, c3 = st.columns(3)
    c1.metric("Total SKU Count", f"{len(df_inv_curr):,}")
    c2.metric("Total Stock Quantity", f"{df_inv_curr['stock_on_hand'].sum():,}")
    low_stock = df_inv_curr[df_inv_curr['stock_on_hand'] <= df_inv_curr['reorder_point']]
    c3.metric("Low Stock Alerts", f"{len(low_stock)}", delta_color="inverse")
    
    st.subheader("⚠️ Out of Stock / Low Stock Alert")
    st.dataframe(low_stock[['store_name', 'product_name', 'sku', 'stock_on_hand', 'reorder_point']].sort_values('stock_on_hand'), use_container_width=True)
    
    st.subheader("Inventory Distribution by Store")
    fig_inv = px.bar(df_inv_curr.groupby('store_name')['stock_on_hand'].sum().reset_index(), 
                     x='store_name', y='stock_on_hand', color='store_name')
    st.plotly_chart(fig_inv, use_container_width=True)

elif selected_page == "5. Customer Analysis":
    st.title("👥 Customer Analysis")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Gender Distribution")
        fig_gen = px.pie(df_filtered.groupby('gender')['customer_id'].nunique().reset_index(), 
                         values='customer_id', names='gender')
        st.plotly_chart(fig_gen, use_container_width=True)
    
    with c2:
        st.subheader("Age Distribution")
        fig_age = px.histogram(df_filtered.drop_duplicates('customer_id'), x='age', nbins=20)
        st.plotly_chart(fig_age, use_container_width=True)
        
    st.subheader("RFM Segmentation (Simplified)")
    # Recency: Days since last purchase
    # Frequency: Count of transactions
    # Monetary: Total spend
    current_date = df_filtered['date'].max() + timedelta(days=1)
    rfm = df_filtered.groupby('customer_id').agg({
        'date': lambda x: (current_date - x.max()).days,
        'quantity': 'count', # frequency
        'total_amount': 'sum'
    }).rename(columns={'date': 'Recency', 'quantity': 'Frequency', 'total_amount': 'Monetary'})
    
    # Simple scoring (1-5 ideally, but let's just plot)
    fig_rfm = px.scatter_3d(rfm, x='Recency', y='Frequency', z='Monetary', opacity=0.7, title="RFM 3D View")
    st.plotly_chart(fig_rfm, use_container_width=True)

elif selected_page == "6. Promotion & Campaign":
    st.title("📢 Promotion Analysis")
    
    st.info("Simulating Campaign Analysis based on Date filters")
    
    # Compare current selection vs previous period
    curr_days = (pd.to_datetime(date_range[1]) - pd.to_datetime(date_range[0])).days
    prev_start = pd.to_datetime(date_range[0]) - timedelta(days=curr_days)
    prev_end = pd.to_datetime(date_range[0]) - timedelta(days=1)
    
    mask_prev = (df_sales_raw['date'] >= prev_start) & (df_sales_raw['date'] <= prev_end)
    # Apply other filters
    if selected_store != 'All': mask_prev &= (df_sales_raw['store_name'] == selected_store)
    if selected_cat != 'All': mask_prev &= (df_sales_raw['category_name'] == selected_cat)
    
    df_prev = df_sales_raw.loc[mask_prev]
    
    st.subheader(f"Comparison: Current Period vs Previous {curr_days} Days")
    
    rev_curr = df_filtered['total_amount'].sum()
    rev_prev = df_prev['total_amount'].sum()
    uplift = ((rev_curr - rev_prev) / rev_prev * 100) if rev_prev > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue Current", format_currency(rev_curr))
    c2.metric("Revenue Previous", format_currency(rev_prev))
    c3.metric("Sales Uplift", f"{uplift:.2f}%", delta=f"{uplift:.2f}%")
    
    # Chart comparison
    daily_curr = df_filtered.groupby('date')['total_amount'].sum().reset_index()
    daily_curr['Type'] = 'Current'
    # Normalize previous dates to align graph? Or just show side by side.
    # Aligning by Day Number (1 to N)
    daily_curr['DayNum'] = range(1, len(daily_curr)+1)
    
    daily_prev = df_prev.groupby('date')['total_amount'].sum().reset_index()
    daily_prev['Type'] = 'Previous'
    daily_prev['DayNum'] = range(1, len(daily_prev)+1)
    
    combined = pd.concat([daily_curr, daily_prev])
    fig_comp = px.line(combined, x='DayNum', y='total_amount', color='Type', title="Campaign Impact Curve")
    st.plotly_chart(fig_comp, use_container_width=True)

elif selected_page == "7. Store Operations":
    st.title("🏪 Store Operations")
    
    # Store Comparison Table
    store_stats = df_filtered.groupby('store_name').agg(
        Revenue=('total_amount', 'sum'),
        Orders=('quantity', 'count'),
        AOV=('total_amount', 'mean')
    ).reset_index()
    
    st.subheader("Store League Table")
    st.dataframe(store_stats.style.background_gradient(subset=['Revenue'], cmap='Greens').format({'Revenue': '£{:.2f}', 'AOV': '£{:.2f}'}), use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig_store = px.bar(store_stats, x='store_name', y='Revenue', title="Revenue by Store", color='Revenue')
        st.plotly_chart(fig_store, use_container_width=True)
        
    with col2:
        fig_orders = px.pie(store_stats, names='store_name', values='Orders', title="Order Volume Share")
        st.plotly_chart(fig_orders, use_container_width=True)

elif selected_page == "8. Forecasting":
    st.title("🔮 Sales Forecasting")
    
    st.markdown("Simple 30-day forecast using Moving Average (Prophet/ARIMA would go here in prod).")
    
    daily_sales = df_sales_raw.groupby('date')['total_amount'].sum().reset_index()
    daily_sales = daily_sales.set_index('date').sort_index()
    
    # Clean data (fill missing)
    idx = pd.date_range(daily_sales.index.min(), daily_sales.index.max())
    daily_sales = daily_sales.reindex(idx, fill_value=0)
    
    # Rolling mean
    daily_sales['Moving_Avg_7d'] = daily_sales['total_amount'].rolling(window=7).mean()
    
    # Simple projection: Last 30 days avg applied forward
    last_avg = daily_sales['total_amount'].tail(30).mean()
    future_dates = pd.date_range(daily_sales.index.max() + timedelta(days=1), periods=30)
    future_df = pd.DataFrame({'date': future_dates, 'Forecast': [last_avg] * 30})
    
    # Plot
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=daily_sales.index, y=daily_sales['total_amount'], mode='lines', name='Actual', line=dict(color='blue', width=1)))
    fig_forecast.add_trace(go.Scatter(x=daily_sales.index, y=daily_sales['Moving_Avg_7d'], mode='lines', name='7-Day MA', line=dict(color='orange')))
    fig_forecast.add_trace(go.Scatter(x=future_df['date'], y=future_df['Forecast'], mode='lines', name='Forecast (Naive)', line=dict(color='green', dash='dash')))
    
    st.plotly_chart(fig_forecast, use_container_width=True)
