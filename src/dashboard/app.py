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
    initial_sidebar_state="expanded",
    page_icon="👗"
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
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    engine = sqlalchemy.create_engine(Config().DATABASE_URL)
    
    # 1. Sales Data (Fact + Dims)
    # Added: order_id, unit_cost, total_cost
    # Removed: channel (use st.type instead)
    q_sales = """
    SELECT 
        s.date, s.time, s.order_id, s.customer_id, s.quantity, s.unit_price, s.total_amount, 
        s.unit_cost, s.total_cost, s.profit, s.payment_method,
        st.store_name, st.region, st.type as store_type,
        p.name as product_name, p.sku, p.base_price, c.category_name, b.brand_name,
        cus.gender, cus.age, cus.region as customer_region, cus.loyalty_score
    FROM fact_sales s
    JOIN dim_store st ON s.store_id = st.store_id
    JOIN dim_product p ON s.product_id = p.product_id
    JOIN dim_category c ON p.category_id = c.category_id
    LEFT JOIN dim_brand b ON p.brand_id = b.brand_id
    LEFT JOIN dim_customer cus ON s.customer_id = cus.customer_id
    """
    
    # 2. Inventory Data
    # Added: snapshot_date
    q_inv = """
    SELECT i.snapshot_date, i.stock_on_hand, i.reorder_point, i.last_restock_date,
           p.name as product_name, p.sku, st.store_name, st.type as store_type
    FROM fact_inventory i
    JOIN dim_product p ON i.product_id = p.product_id
    JOIN dim_store st ON i.store_id = st.store_id
    """
    
    try:
        with engine.connect() as conn:
            df_sales = pd.read_sql(q_sales, conn)
            df_inv = pd.read_sql(q_inv, conn)
            
        # Ensure proper types
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        df_inv['snapshot_date'] = pd.to_datetime(df_inv['snapshot_date'])
        
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
    "3. Product & Margin", 
    "4. Inventory Intelligence", 
    "5. Customer Segments", 
    "6. Basket Analysis", 
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

# Helper
def format_currency(val):
    return f"£{val:,.2f}"

# --- PAGE IMPLEMENTATIONS ---

if selected_page == "1. Executive Summary":
    st.title("📊 Executive Summary")
    
    # KPIs
    total_rev = df_filtered['total_amount'].sum()
    total_orders = df_filtered['order_id'].nunique() # Corrected: Unique Orders
    total_lines = len(df_filtered)
    gross_profit = df_filtered['profit'].sum()
    margin = (gross_profit / total_rev * 100) if total_rev > 0 else 0
    aov = total_rev / total_orders if total_orders > 0 else 0
    basket_size = total_lines / total_orders if total_orders > 0 else 0 # Avg Items per Order
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", format_currency(total_rev), delta="Target: £1M")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Profit Margin", f"{margin:.1f}%")
    c4.metric("Avg Basket Size", f"{basket_size:.2f} Items")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Sales Trend (Daily)")
        daily_sales = df_filtered.groupby('date')['total_amount'].sum().reset_index()
        fig_trend = px.line(daily_sales, x='date', y='total_amount', title="Daily Revenue", template="plotly_white")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col2:
        st.subheader("Revenue by Channel")
        # Use store_type as channel
        fig_chan = px.pie(df_filtered.groupby('store_type')['total_amount'].sum().reset_index(), 
                          values='total_amount', names='store_type', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_chan, use_container_width=True)

elif selected_page == "2. Sales Performance":
    st.title("📈 Sales Performance")
    
    # Heatmap
    st.subheader("Sales Heatmap (Peak Times)")
    df_heat = df_filtered.copy()
    df_heat['hour'] = pd.to_datetime(df_heat['time'], format='%H:%M:%S').dt.hour
    df_heat['day_of_week'] = df_heat['date'].dt.day_name()
    
    heatmap_data = df_heat.pivot_table(index='day_of_week', columns='hour', values='order_id', aggfunc='nunique')
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(days_order)
    
    fig_heat = px.imshow(heatmap_data, labels=dict(x="Hour", y="Day", color="Orders"), color_continuous_scale="Viridis")
    st.plotly_chart(fig_heat, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Average Order Value (AOV) by Store")
        store_metrics = df_filtered.groupby('store_name').agg(
            Rev=('total_amount', 'sum'),
            Orders=('order_id', 'nunique')
        ).reset_index()
        store_metrics['AOV'] = store_metrics['Rev'] / store_metrics['Orders']
        
        fig_pay = px.bar(store_metrics, x='store_name', y='AOV', color='AOV', color_continuous_scale='Blues')
        st.plotly_chart(fig_pay, use_container_width=True)
        
    with c2:
        st.subheader("Top Payment Methods")
        fig_chan = px.bar(df_filtered.groupby('payment_method')['order_id'].nunique().reset_index(), 
                          x='payment_method', y='order_id', title="Transaction Volume")
        st.plotly_chart(fig_chan, use_container_width=True)

elif selected_page == "3. Product & Margin":
    st.title("👗 Product Profitability")
    
    prod_perf = df_filtered.groupby('product_name').agg(
        Revenue=('total_amount', 'sum'),
        Cost=('total_cost', 'sum'),
        Profit=('profit', 'sum'),
        Qty_Sold=('quantity', 'sum')
    ).reset_index()
    prod_perf['Margin_Pct'] = prod_perf['Profit'] / prod_perf['Revenue']
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Most Profitable Products (Top 10)")
        top_profit = prod_perf.nlargest(10, 'Profit')
        st.dataframe(top_profit[['product_name', 'Revenue', 'Profit', 'Margin_Pct']].style.format({'Revenue': '£{:.2f}', 'Profit': '£{:.2f}', 'Margin_Pct': '{:.1%}'}), use_container_width=True)

    with c2:
        st.subheader("Margin Scatter Plot")
        fig_scat = px.scatter(prod_perf, x='Revenue', y='Margin_Pct', size='Qty_Sold', 
                              hover_name='product_name', title="Revenue vs Margin %")
        st.plotly_chart(fig_scat, use_container_width=True)

elif selected_page == "4. Inventory Intelligence":
    st.title("📦 Inventory Intelligence")
    
    # 1. Historical Trend
    st.subheader("Stock Level Trends (Historical)")
    # Filter by store if needed, but show trend aggregation
    df_inv_trend = df_inv_raw.copy()
    if selected_store != 'All':
        df_inv_trend = df_inv_trend[df_inv_trend['store_name'] == selected_store]
        
    daily_stock = df_inv_trend.groupby('snapshot_date')['stock_on_hand'].sum().reset_index()
    fig_stock = px.line(daily_stock, x='snapshot_date', y='stock_on_hand', title="Total Stock on Hand over Time")
    st.plotly_chart(fig_stock, use_container_width=True)

    # 2. Current Status
    st.subheader("Current Stock Status (Latest Snapshot)")
    latest_date = df_inv_trend['snapshot_date'].max()
    df_curr = df_inv_trend[df_inv_trend['snapshot_date'] == latest_date]
    
    low_stock = df_curr[df_curr['stock_on_hand'] <= df_curr['reorder_point']]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Date Snapshot", latest_date.strftime('%Y-%m-%d'))
    c2.metric("Total Items", f"{df_curr['stock_on_hand'].sum():,}")
    c3.metric("Critical Low Stock Alerts", f"{len(low_stock)}", delta_color="inverse")
    
    st.dataframe(low_stock[['store_name', 'product_name', 'stock_on_hand', 'reorder_point']].sort_values('stock_on_hand'), use_container_width=True)

elif selected_page == "5. Customer Segments":
    st.title("👥 Customer Segmentation (RFM)")
    
    st.markdown("""
    **Segments:**
    *   **Champions**: Recent, Frequent, High Spend.
    *   **Loyal**: Frequent buyers.
    *   **At Risk**: High value but haven't bought recently.
    """)
    
    # Should use the pre-calculated segments ideally, but let's calc on the fly using dashboard filters
    current_date = df_filtered['date'].max() + timedelta(days=1)
    rfm = df_filtered.groupby('customer_id').agg({
        'date': lambda x: (current_date - x.max()).days,
        'order_id': 'nunique', # Frequency = Orders
        'total_amount': 'sum'
    }).rename(columns={'date': 'Recency', 'order_id': 'Frequency', 'total_amount': 'Monetary'})
    
    # Basic scoring logic for visualization
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 3, labels=['High', 'Mid', 'Low']) # Low recency is Good? No, Low days is good. 
    # Let's just visualize scatter
    
    fig_rfm = px.scatter(rfm, x='Recency', y='Frequency', size='Monetary', color='Monetary', 
                         title="Recency vs Frequency (Size = Spend)", hover_data=['Monetary'])
    st.plotly_chart(fig_rfm, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
            st.subheader("Top Customers (Champions)")
            st.dataframe(rfm.nlargest(10, 'Monetary').style.format({'Monetary': '£{:.2f}'}), use_container_width=True)

elif selected_page == "6. Basket Analysis":
    st.title("🛒 Market Basket Analysis")
    
    # Items per Order Distribution
    basket_sizes = df_filtered.groupby('order_id').size().reset_index(name='item_count')
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribution of Basket Sizes")
        fig_hist = px.histogram(basket_sizes, x='item_count', nbins=10, title="Items per Order")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with c2:
        st.subheader("Basket Size by Category")
        # Join back to get category
        # Which categories stimulate bulk buys?
        cat_basket = df_filtered.groupby('category_name')['quantity'].mean().reset_index() # Avg Qty per Line Item
        fig_bar = px.bar(cat_basket.nlargest(10, 'quantity'), x='category_name', y='quantity', title="Avg Qty per Item (Bulk Potential)")
        st.plotly_chart(fig_bar, use_container_width=True)

elif selected_page == "7. Store Operations":
    st.title("🏪 Store Performance")
    
    store_stats = df_filtered.groupby('store_name').agg(
        Revenue=('total_amount', 'sum'),
        Orders=('order_id', 'nunique')
    ).reset_index()
    store_stats['AOV'] = store_stats['Revenue'] / store_stats['Orders']
    
    st.dataframe(store_stats.style.background_gradient(subset=['Revenue'], cmap='Greens').format({'Revenue': '£{:.2f}', 'AOV': '£{:.2f}'}), use_container_width=True)
    
    st.subheader("Physical vs Online Share")
    # Store Type logic
    type_stats = df_filtered.groupby('store_type')['total_amount'].sum().reset_index()
    fig_pie = px.pie(type_stats, values='total_amount', names='store_type')
    st.plotly_chart(fig_pie, use_container_width=True)

elif selected_page == "8. Forecasting":
    st.title("🔮 Revenue Forecasting")
    
    # Simple Moving Average
    daily_sales = df_filtered.groupby('date')['total_amount'].sum().reset_index().set_index('date').sort_index()
    idx = pd.date_range(daily_sales.index.min(), daily_sales.index.max())
    daily_sales = daily_sales.reindex(idx, fill_value=0)
    
    daily_sales['MA_7'] = daily_sales['total_amount'].rolling(window=7).mean()
    
    st.line_chart(daily_sales[['total_amount', 'MA_7']])
    st.caption("Blue: Actual Daily Revenue, Orange: 7-Day Moving Average trend.")

st.sidebar.markdown("---")
st.sidebar.caption("ASOS Retail Dashboard v2.2 (Enterprise)")
