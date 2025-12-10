import nbformat as nbf
import os

def create_notebook():
    nb = nbf.v4.new_notebook()

    # Introduction
    text_intro = """# ASOS E-commerce Data Analysis
This notebook performs Exploratory Data Analysis (EDA) on the ASOS product catalog dataset.
We will analyze:
1. Brand Distribution
2. Category Distribution
3. Price Analysis
4. Size Availability
5. Color Distribution
"""
    
    # Setup Cell
    code_setup = """import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# Add project root to path to access src
# Assuming this notebook is in <root>/notebooks
project_root = os.path.dirname(os.getcwd())
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import Config

# Plotting setup
%matplotlib inline
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = (10, 6)

# Connect to Database
try:
    engine = create_engine(Config().DATABASE_URL)
    connection = engine.connect()
    print("Connected to Database!")
except Exception as e:
    print(f"Connection Failed: {e}")
"""

    # 1. Brand Analysis
    text_brand = "## 1. Top 20 Brands by Product Count"
    code_brand = """query_brand = \"\"\"
SELECT b.brand_name, COUNT(p.product_id) as product_count
FROM dim_product p
JOIN dim_brand b ON p.brand_id = b.brand_id
GROUP BY b.brand_name
ORDER BY product_count DESC
LIMIT 20;
\"\"\"

df_brand = pd.read_sql(query_brand, connection)

plt.figure(figsize=(12, 8))
sns.barplot(data=df_brand, x='product_count', y='brand_name')
plt.title('Top 20 Brands by Product Count')
plt.xlabel('Number of Products')
plt.ylabel('Brand')
plt.show()
"""

    # 2. Category Analysis
    text_cat = "## 2. Product Count by Category"
    code_cat = """query_cat = \"\"\"
SELECT c.category_name, COUNT(p.product_id) as product_count
FROM dim_product p
JOIN dim_category c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY product_count DESC
LIMIT 20;
\"\"\"

df_cat = pd.read_sql(query_cat, connection)

plt.figure(figsize=(12, 8))
sns.barplot(data=df_cat, x='product_count', y='category_name')
plt.title('Top 20 Categories')
plt.xlabel('Count')
plt.ylabel('Category')
plt.show()
"""

    # 3. Price Analysis
    text_price = "## 3. Price Distribution"
    code_price = """query_price = \"\"\"
SELECT price
FROM fact_product_attributes
WHERE price IS NOT NULL AND price < 500 -- Filter outliers for better viz
\"\"\"

df_price = pd.read_sql(query_price, connection)

plt.figure(figsize=(10, 6))
sns.histplot(df_price['price'], bins=50, kde=True)
plt.title('Price Distribution (Under £500)')
plt.xlabel('Price')
plt.show()
"""

    # 4. Price by Category Boxplot
    text_price_box = "### Price Distribution by Top Categories"
    code_price_box = """# Get top 10 categories
top_cats = df_cat.head(10)['category_name'].tolist()

query_price_cat = f\"\"\"
SELECT c.category_name, p.base_price
FROM dim_product p
JOIN dim_category c ON p.category_id = c.category_id
WHERE c.category_name IN {tuple(top_cats)} 
  AND p.base_price IS NOT NULL 
  AND p.base_price < 300
\"\"\"

df_price_cat = pd.read_sql(query_price_cat, connection)

plt.figure(figsize=(14, 8))
sns.boxplot(data=df_price_cat, x='base_price', y='category_name')
plt.title('Price Distribution by Top Categories')
plt.xlabel('Price')
plt.show()
"""

    # Close connection
    code_close = "connection.close()"

    # Add cells
    nb.cells.append(nbf.v4.new_markdown_cell(text_intro))
    nb.cells.append(nbf.v4.new_code_cell(code_setup))
    nb.cells.append(nbf.v4.new_markdown_cell(text_brand))
    nb.cells.append(nbf.v4.new_code_cell(code_brand))
    nb.cells.append(nbf.v4.new_markdown_cell(text_cat))
    nb.cells.append(nbf.v4.new_code_cell(code_cat))
    nb.cells.append(nbf.v4.new_markdown_cell(text_price))
    nb.cells.append(nbf.v4.new_code_cell(code_price))
    nb.cells.append(nbf.v4.new_markdown_cell(text_price_box))
    nb.cells.append(nbf.v4.new_code_cell(code_price_box))
    nb.cells.append(nbf.v4.new_code_cell(code_close))

    # Write file
    os.makedirs('notebooks', exist_ok=True)
    with open('notebooks/eda_analysis.ipynb', 'w') as f:
        nbf.write(nb, f)
    
    print("Notebook created at notebooks/eda_analysis.ipynb")

if __name__ == "__main__":
    create_notebook()
