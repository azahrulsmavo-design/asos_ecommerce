# Power BI Python Visualization Tutorial

This guide explains how to use the custom Python scripts in `src/analysis/powerbi_visuals.py` to create advanced visualizations in your ASOS Retail Dashboard.

## Prerequisites

1.  **Python Installed**: Ensure Python is installed on your machine.
2.  **Libraries**: Install the required libraries in your Python environment:
    ```bash
    pip install pandas matplotlib seaborn
    ```
3.  **Power BI Configuration**:
    - Go to **File > Options and settings > Options > Python scripting**.
    - Set the **Detected Python home directory** to your Python installation path (e.g., `C:\Users\Azahr\AppData\Local\Programs\Python\Python310`).

## How to Add a Python Visual

1.  Open your Power BI Report.
2.  In the **Visualizations** pane, click the **Python visual** icon (PY).
3.  **Enable Script Visuals** if prompted.
4.  A placeholder visual will appear on the canvas, and a script editor will open at the bottom.

## Visual 1: Revenue Trend with Moving Average

**Page**: Sales Overview  
**Data Fields Required**: 
- `public dim_date[Date]`
- `_Measures[Total Revenue]` (or `fact_sales[total_amount]`)

**Script**:
Copy and paste the following code into the script editor:

```python
# 'dataset' holds the input data for this script
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Setup
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

def plot_sales_trend(df):
    if df.empty: return
    # Rename default fields if needed
    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})
    if 'total_amount' in df.columns: df = df.rename(columns={'total_amount': 'Total Revenue'})

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Revenue Line
    sns.lineplot(data=df, x='Date', y='Total Revenue', label='Daily Revenue', color='#2d7d9a', ax=ax)
    
    # Moving Average
    df['MA_7'] = df['Total Revenue'].rolling(window=7).mean()
    sns.lineplot(data=df, x='Date', y='MA_7', label='7-Day Avg', color='#e74c3c', linestyle='--', ax=ax)
    
    ax.set_title('Revenue Trend', fontsize=14)
    plt.tight_layout()
    plt.show()

# Run
plot_sales_trend(dataset)
```

## Visual 2: Profitability by Category

**Page**: Sales Overview  
**Data Fields Required**: 
- `public dim_category[category_name]`
- `_Measures[Total Profit]`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

def plot_category_performance(df):
    if df.empty: return
    
    # Check for likely names
    if 'Category' in df.columns: df = df.rename(columns={'Category': 'category_name'})
    if 'Profit' in df.columns: df = df.rename(columns={'Profit': 'Total Profit'})
        
    df = df.sort_values('Total Profit', ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df, x='Total Profit', y='category_name', palette='viridis', ax=ax)
    
    for i, v in enumerate(df['Total Profit']):
        ax.text(v, i, f' ${v:,.0f}', va='center', fontsize=9)
        
    ax.set_title('Profitability by Category', fontsize=14)
    plt.tight_layout()
    plt.show()

plot_category_performance(dataset)
```

## Visual 3: RFM Customer Segments

**Page**: Customer Segmentation  
**Data Fields Required**: 
- From your RFM table: `Recency`, `Frequency`, `Monetary`, `RFM_Segment`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

def plot_rfm_segments(df):
    if df.empty: return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.scatterplot(
        data=df, x='Recency', y='Frequency', 
        hue='RFM_Segment', size='Monetary', sizes=(20, 200),
        alpha=0.7, palette='deep', ax=ax
    )
    
    ax.set_title('RFM Segments', fontsize=14)
    plt.tight_layout()
    plt.show()

plot_rfm_segments(dataset)
```

## Visual 4: Monthly Sales Growth (YoY)

**Page**: Executive Dashboard  
**Data Fields Required**: 
- `public dim_date[Date]`
- `_Measures[Total Revenue]`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

def plot_monthly_growth_yoy(df):
    if df.empty: return
    
    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})
    if 'total_amount' in df.columns: df = df.rename(columns={'total_amount': 'Total Revenue'})
    
    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    monthly = df.groupby(['Year', 'Month'])['Total Revenue'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.lineplot(data=monthly, x='Month', y='Total Revenue', hue='Year', palette='tab10', marker='o', linewidth=2.5, ax=ax)
    
    ax.set_title('Monthly Revenue Growth (YoY)', fontsize=14)
    ax.set_xlabel('Month', fontsize=12)
    plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.legend(title='Year')
    plt.tight_layout()
    plt.show()

plot_monthly_growth_yoy(dataset)
```

## Visual 5: Sales Heatmap (Category vs Month)

**Page**: Executive Dashboard  
**Data Fields Required**: 
- `public dim_category[category_name]`
- `public dim_date[Month]`
- `_Measures[Total Revenue]`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="whitegrid")

def plot_kpi_heatmap(df):
    if df.empty: return
    
    if 'Category' in df.columns: df = df.rename(columns={'Category': 'category_name'})
    if 'Sales' in df.columns: df = df.rename(columns={'Sales': 'Total Revenue'})
    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})

    # Pivot
    pivot = df.pivot_table(index='category_name', columns='Month', values='Total Revenue', aggfunc='sum').fillna(0)
    
    # Sort columns if numeric
    if all(isinstance(c, (int, float)) for c in pivot.columns):
        pivot = pivot.sort_index(axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(pivot, annot=True, fmt=',.0f', cmap='YlGnBu', linewidths=.5, ax=ax, cbar_kws={'label': 'Revenue'})
    
    ax.set_title('Revenue Heatmap', fontsize=14)
    plt.tight_layout()
    plt.show()

plot_kpi_heatmap(dataset)
```

## Visual 6: Product Feature Correlation

**Page**: Product Analysis  
**Data Fields Required**: 
- `public fact_sales[unit_price]`
- `public fact_sales[quantity]`
- `public fact_product_attributes[num_images]` (if available)

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="whitegrid")

def plot_feature_correlation(df):
    if df.empty: return
    
    # Map from whatever user drags in to standard names
    rename_map = {
        'Price': 'unit_price', 'Rating': 'rating', 
        'Num Images': 'num_images', 'Sales': 'quantity',
        'Total Quantity': 'quantity'
    }
    df = df.rename(columns=rename_map)
        
    corr = df.corr()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, ax=ax)
    
    ax.set_title('Feature Correlation Matrix', fontsize=14)
    plt.tight_layout()
    plt.show()

plot_feature_correlation(dataset)
```

## Visual 7: Sales Trend Small Multiples
**Page**: Sales Deep Dive
**Data Fields Required**:
- `public dim_date[Date]`
- `public dim_category[Category]`
- `_Measures[Total Revenue]`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

def plot_small_multiples(df):
    if df.empty: return

    if 'Total Sales' in df.columns: df = df.rename(columns={'Total Sales': 'Total Revenue'})
    if 'category_name' in df.columns: df = df.rename(columns={'category_name': 'Category'})

    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create the FacetGrid
    g = sns.FacetGrid(df, col="Category", col_wrap=3, height=3, aspect=1.5, sharey=False)
    g.map(sns.lineplot, "Date", "Total Revenue", color="#2d7d9a", linewidth=2)
    
    # Adjust titles and layout
    g.set_titles("{col_name}")
    g.set_axis_labels("Date", "Revenue")
    
    for ax in g.axes.flatten():
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        
    g.fig.suptitle('Revenue Trend by Category', fontsize=16, y=1.05)
    plt.tight_layout()
    plt.show()

plot_small_multiples(dataset)
```

## Visual 8: Product Clustering
**Page**: Product Intelligence
**Data Fields Required**:
- `public fact_product_features[cluster_id]`
- `_Measures[Total Revenue]`
- `_Measures[Profit Margin %]`

**Script**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

def plot_product_clusters(df):
    if df.empty: return
        
    # Map fields
    if 'Total Revenue' not in df.columns: 
        # try to find likely match if user renamed it
        money_col = [c for c in df.columns if 'Revenue' in c or 'Sales' in c][0]
        df = df.rename(columns={money_col: 'Revenue'})
    else:
        df = df.rename(columns={'Total Revenue': 'Revenue'})
        
    if 'Profit Margin %' not in df.columns:
        margin_col = [c for c in df.columns if 'Margin' in c][0]
        df = df.rename(columns={margin_col: 'Margin'})
    else:
        df = df.rename(columns={'Profit Margin %': 'Margin'})

    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.scatterplot(
        data=df, x='Revenue', y='Margin', hue='cluster_id',
        palette='tab10', s=100, alpha=0.7, ax=ax
    )
    
    ax.set_title('Product Clusters: Revenue vs Margin', fontsize=16, pad=20)
    plt.tight_layout()
    plt.show()

plot_product_clusters(dataset)
```

## Troubleshooting
- **Missing Libraries**: If you see an error about missing modules, ensure you installed them in the correct Python environment Power BI is pointing to.
- **Empty Plot**: Ensure the fields dragged into the "Values" section are not summarized (e.g., select "Don't summarize" for numeric IDs).
