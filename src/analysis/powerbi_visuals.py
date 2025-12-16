import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for professional look
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

def plot_sales_trend(df):
    """
    Expects DataFrame with columns: ['Date', 'Total Revenue']
    Used for: Sales Overview Page
    """
    if df.empty:
        return
    
    # Handle potential column renaming if user drags generic fields
    if 'Total Sales' in df.columns:
        df = df.rename(columns={'Total Sales': 'Total Revenue'})
    if 'total_amount' in df.columns:
        df = df.rename(columns={'total_amount': 'Total Revenue'})

    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Main Line
    sns.lineplot(data=df, x='Date', y='Total Revenue', label='Daily Revenue', color='#2d7d9a', linewidth=2, ax=ax)
    
    # Moving Average (7-day)
    df['MA_7'] = df['Total Revenue'].rolling(window=7).mean()
    sns.lineplot(data=df, x='Date', y='MA_7', label='7-Day Avg', color='#e74c3c', linestyle='--', linewidth=2, ax=ax)
    
    ax.set_title('Revenue Trend & 7-Day Moving Average', fontsize=16, pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Revenue', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_category_performance(df):
    """
    Expects DataFrame with columns: ['category_name', 'Total Profit']
    Used for: Sales Overview Page
    """
    if df.empty:
        return
    
    # Rename for consistency if needed
    if 'Category' in df.columns:
        df = df.rename(columns={'Category': 'category_name'})
    if 'Profit' in df.columns:
        df = df.rename(columns={'Profit': 'Total Profit'})
        
    df = df.sort_values('Total Profit', ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Bar Chart for Profit
    sns.barplot(data=df, x='Total Profit', y='category_name', palette='viridis', ax=ax)
    
    # Add text labels
    for i, v in enumerate(df['Total Profit']):
        ax.text(v, i, f' ${v:,.0f}', va='center', fontsize=10, fontweight='bold')
        
    ax.set_title('Profitability by Category', fontsize=16, pad=20)
    ax.set_xlabel('Total Profit', fontsize=12)
    ax.set_ylabel('')
    plt.tight_layout()
    plt.show()

def plot_rfm_segments(df):
    """
    Expects DataFrame with columns: ['Recency', 'Frequency', 'Monetary', 'RFM_Segment']
    Used for: Customer Segmentation Page
    """
    if df.empty:
        return
        
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    sns.scatterplot(
        data=df, 
        x='Recency', 
        y='Frequency', 
        hue='RFM_Segment', 
        size='Monetary', 
        sizes=(20, 200),
        alpha=0.7,
        palette='deep',
        ax=ax
    )
    
    ax.set_title('Customer Segments (Recency vs Frequency)', fontsize=16, pad=20)
    ax.set_xlabel('Recency (Days since last order)', fontsize=12)
    ax.set_ylabel('Frequency (Total Orders)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

def plot_price_elasticity(df):
    """
    Expects DataFrame with columns: ['unit_price', 'quantity']
    Used for: Product Analysis Page
    """
    if df.empty:
        return

    # Map likely generic names
    if 'Unit Price' in df.columns:
        df = df.rename(columns={'Unit Price': 'unit_price'})
    if 'Quantity Sold' in df.columns:
        df = df.rename(columns={'Quantity Sold': 'quantity'})

    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.regplot(
        data=df,
        x='unit_price',
        y='quantity',
        scatter_kws={'alpha':0.5},
        line_kws={'color': 'red'},
        ax=ax
    )
    
    ax.set_title('Price Elasticity: Price vs Quantity', fontsize=16, pad=20)
    ax.set_xlabel('Unit Price', fontsize=12)
    ax.set_ylabel('Quantity Sold', fontsize=12)
    plt.tight_layout()
    plt.show()

def plot_monthly_growth_yoy(df):
    """
    Expects DataFrame with columns: ['Date', 'Total Revenue']
    Used for: Executive Page
    """
    if df.empty:
        return
    
    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})
    
    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    # Group by Year and Month
    monthly = df.groupby(['Year', 'Month'])['Total Revenue'].sum().reset_index()
    
    # Pivot for easier plotting: Index=Month, Columns=Year
    pivot = monthly.pivot(index='Month', columns='Year', values='Total Revenue')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot each year
    sns.lineplot(data=monthly, x='Month', y='Total Revenue', hue='Year', palette='tab10', marker='o', linewidth=2.5, ax=ax)
    
    ax.set_title('Monthly Revenue Growth (Year-over-Year)', fontsize=16, pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Total Revenue', fontsize=12)
    plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.legend(title='Year')
    plt.tight_layout()
    plt.show()

def plot_kpi_heatmap(df):
    """
    Expects DataFrame with columns: ['Month', 'category_name', 'Total Revenue']
    Used for: Executive Page
    """
    if df.empty:
        return
    
    if 'Category' in df.columns: df = df.rename(columns={'Category': 'category_name'})
    if 'Sales' in df.columns: df = df.rename(columns={'Sales': 'Total Revenue'})
    
    pivot = df.pivot_table(index='category_name', columns='Month', values='Total Revenue', aggfunc='sum').fillna(0)
    
    # Sort columns if numeric
    if all(isinstance(c, (int, float)) for c in pivot.columns):
        pivot = pivot.sort_index(axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(pivot, annot=True, fmt=',.0f', cmap='YlGnBu', linewidths=.5, ax=ax, cbar_kws={'label': 'Revenue'})
    
    ax.set_title('Revenue Performance Heatmap (Category vs Month)', fontsize=16, pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Category', fontsize=12)
    plt.tight_layout()
    plt.show()

def plot_feature_correlation(df):
    """
    Expects DataFrame with columns: ['unit_price', 'rating', 'num_images', 'quantity']
    Used for: Product Analysis Page
    """
    if df.empty:
        return
        
    # Standardize column names
    rename_map = {
        'Price': 'unit_price', 'Rating': 'rating', 
        'Num Images': 'num_images', 'Sales': 'quantity'
    }
    df = df.rename(columns=rename_map)
    
    corr = df.corr()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, ax=ax)
    
    ax.set_title('Feature Correlation Matrix', fontsize=16, pad=20)
    plt.tight_layout()
    plt.show()

def plot_small_multiples(df):
    """
    Expects DataFrame with columns: ['Date', 'Category', 'Total Revenue']
    Used for: Sales Deep Dive Page (Small Multiples)
    """
    if df.empty:
        return

    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})
    if 'category_name' in df.columns: df = df.rename(columns={'category_name': 'Category'})

    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create the FacetGrid
    g = sns.FacetGrid(df, col="Category", col_wrap=3, height=3, aspect=1.5, sharey=False)
    g.map(sns.lineplot, "Date", "Total Revenue", color="#2d7d9a", linewidth=2)
    
    # Adjust titles and layout
    g.set_titles("{col_name}")
    g.set_axis_labels("Date", "Revenue")
    
    # Improve date formatting on x-axis
    for ax in g.axes.flatten():
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        
    g.fig.suptitle('Revenue Trend by Category (Small Multiples)', fontsize=16, y=1.05)
    plt.tight_layout()
    plt.show()

def plot_product_clusters(df):
    """
    Expects DataFrame with columns: ['Revenue', 'Margin', 'cluster_id']
    Used for: Product Intelligence (Advanced)
    """
    if df.empty:
        return
        
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.scatterplot(
        data=df, 
        x='Revenue', 
        y='Margin', 
        hue='cluster_id',
        palette='tab10',
        s=100,
        alpha=0.7,
        ax=ax
    )
    
    ax.set_title('Product Clusters: Revenue vs Margin', fontsize=16, pad=20)
    ax.set_xlabel('Revenue', fontsize=12)
    ax.set_ylabel('Margin %', fontsize=12)
    plt.legend(title='Cluster ID')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # --- Sample Data Generation for Testing ---
    print("Generating sample plots...")
    
    # 1. Sales Trend Data
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    revenue = np.random.randint(1000, 5000, size=30)
    df_sales = pd.DataFrame({'Date': dates, 'Total Revenue': revenue})
    # plot_sales_trend(df_sales)
    
    # 2. Category Data
    categories = ['Dresses', 'Shoes', 'Accessories', 'Tops', 'Jeans']
    profit = [15000, 12000, 8000, 9500, 11000]
    df_cat = pd.DataFrame({'category_name': categories, 'Total Profit': profit})
    # plot_category_performance(df_cat)
    
    # 3. RFM Data
    df_rfm = pd.DataFrame({
        'Recency': np.random.randint(1, 100, 50),
        'Frequency': np.random.randint(1, 20, 50),
        'Monetary': np.random.randint(100, 1000, 50),
        'RFM_Segment': np.random.choice(['Champions', 'Loyal', 'At Risk', 'Lost'], 50)
    })
    # plot_rfm_segments(df_rfm)

    # 4. Executive - Monthly Growth (YoY)
    dates_2y = pd.date_range(start='2022-01-01', end='2023-12-31', freq='M')
    sales_2y = np.random.randint(20000, 50000, size=len(dates_2y))
    df_growth = pd.DataFrame({'Date': dates_2y, 'Total Revenue': sales_2y})
    # plot_monthly_growth_yoy(df_growth)

    # 5. Executive - Heatmap
    df_heatmap = pd.DataFrame({
        'category_name': np.random.choice(['Tops', 'Bottoms', 'Shoes'], 100),
        'Month': np.random.randint(1, 13, 100),
        'Total Revenue': np.random.randint(100, 1000, 100)
    })
    # plot_kpi_heatmap(df_heatmap)

    # 6. Product - Correlation
    df_corr = pd.DataFrame({
        'unit_price': np.random.normal(50, 15, 100),
        'rating': np.random.normal(4.0, 0.5, 100),
        'num_images': np.random.randint(1, 5, 100),
        'quantity': np.random.randint(10, 100, 100)
    })
    # plot_feature_correlation(df_corr)

    # 7. Small Multiples
    dates_sm = pd.date_range(start='2023-01-01', periods=20, freq='D')
    df_sm = pd.DataFrame({
        'Date': np.tile(dates_sm, 3),
        'Category': np.repeat(['Tops', 'Shoes', 'Accessories'], 20),
        'Total Revenue': np.random.randint(100, 1000, 60)
    })
    # plot_small_multiples(df_sm)

    # 8. Product Clusters
    df_clust = pd.DataFrame({
        'Revenue': np.random.randint(1000, 5000, 50),
        'Margin': np.random.uniform(0.1, 0.5, 50),
        'cluster_id': np.random.choice([0, 1, 2], 50)
    })
    # plot_product_clusters(df_clust)

    print("Script loaded successfully. Copy relevant functions to Power BI.")
