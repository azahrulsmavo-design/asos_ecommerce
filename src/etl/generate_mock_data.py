import pandas as pd
import numpy as np
import sqlalchemy
from datetime import datetime, timedelta
import random
import sys
import os
import uuid

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config
from src.utils.db_utils import get_engine, insert_data, logger

# Constants
NUM_CUSTOMERS = 1000
TARGET_NUM_ORDERS = 12000 # Actual target for unique orders
STORES = [
    {'store_name': 'ASOS Online', 'region': 'Global', 'type': 'Online'},
    {'store_name': 'Oxford Street Flagship', 'region': 'London', 'type': 'Physical'},
    {'store_name': 'Manchester Arndale', 'region': 'North West', 'type': 'Physical'},
    {'store_name': 'Birmingham Bullring', 'region': 'West Midlands', 'type': 'Physical'},
    {'store_name': 'Edinburgh St James', 'region': 'Scotland', 'type': 'Physical'}
]
START_DATE = datetime.now() - timedelta(days=365)
END_DATE = datetime.now()

def generate_stores(engine):
    logger.info("Generating Stores...")
    df_stores = pd.DataFrame(STORES)
    df_stores['store_id'] = range(1, len(df_stores) + 1)
    insert_data(df_stores, 'dim_store', engine, if_exists='replace')
    return df_stores

def generate_customers(engine):
    logger.info("Generating Customers...")
    regions = ['London', 'South East', 'North West', 'West Midlands', 'Scotland', 'Wales', 'Northern Ireland']
    
    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        customers.append({
            'customer_id': i,
            'gender': random.choice(['Male', 'Female', 'Non-Binary']),
            'age': random.randint(18, 65),
            'region': random.choice(regions),
            'join_date': START_DATE - timedelta(days=random.randint(0, 1000)),
            'loyalty_score': random.randint(1, 100)
        })
    
    df_customers = pd.DataFrame(customers)
    insert_data(df_customers, 'dim_customer', engine, if_exists='replace')
    return df_customers

def generate_sales_and_inventory(engine):
    logger.info("Reading Products...")
    products = pd.read_sql("SELECT product_id, base_price, category_id, brand_id FROM dim_product", engine)
    
    if products.empty:
        logger.error("No products found! Please load product data first.")
        return

    stores = pd.read_sql("SELECT store_id, type FROM dim_store", engine)
    customer_ids = range(1, NUM_CUSTOMERS + 1)
    
    # --- 1. Generate Sales (Target Based) ---
    logger.info(f"Generating Sales for target {TARGET_NUM_ORDERS} Orders...")
    
    sales_data = []
    product_list = products.to_dict('records')
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Klarna', 'Apple Pay']
    
    # Date Weighted Selection
    date_range = pd.date_range(START_DATE, END_DATE).to_pydatetime().tolist()
    # Weights: Higher in Q4
    weights = [1.5 if d.month in [11, 12] else (0.8 if d.month in [1, 2] else 1.0) for d in date_range]
    
    # Sample actual dates for orders
    selected_dates = random.choices(date_range, weights=weights, k=TARGET_NUM_ORDERS)
    
    transaction_counter = 1
    
    for order_date in selected_dates:
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        store = stores.sample(1).iloc[0]
        customer_id = random.choice(customer_ids)
        pay_method = random.choice(payment_methods)
        # Random time between 8am-10pm
        order_time = order_date.replace(hour=random.randint(8, 22), minute=random.randint(0, 59))
        
        # Basket Size (1-5 items)
        num_items = np.random.choice([1, 2, 3, 4, 5], p=[0.65, 0.2, 0.1, 0.03, 0.02])
        
        for _ in range(num_items):
            prod = random.choice(product_list)
            qty = np.random.choice([1, 2], p=[0.9, 0.1])
            
            # Pricing Logic
            # Discount affects PRICE, but not COST
            discount_pct = np.random.choice([0, 0.1, 0.2, 0.5], p=[0.7, 0.15, 0.1, 0.05])
            base_price = float(prod['base_price'])
            
            unit_price = round(base_price * (1 - discount_pct), 2)
            total_amount = round(unit_price * qty, 2)
            
            # Cost Logic (Stable COGS)
            # COGS is typically 40-60% of BASE price, unaffected by promo
            margin_pct = random.uniform(0.4, 0.6) 
            unit_cost = round(base_price * (1 - margin_pct), 2)
            total_cost = round(unit_cost * qty, 2)
            
            profit = round(total_amount - total_cost, 2)
            
            sales_data.append({
                'transaction_id': transaction_counter, 
                'order_id': order_id,
                'date': order_date,
                'time': order_time,
                'store_id': store['store_id'],
                'customer_id': customer_id,
                'product_id': prod['product_id'],
                'quantity': qty,
                'unit_price': unit_price,
                'total_amount': total_amount,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
                'profit': profit,
                'payment_method': pay_method
                # Channel removed, derived from store type in BI
            })
            transaction_counter += 1
            
    df_sales = pd.DataFrame(sales_data)
    insert_data(df_sales, 'fact_sales', engine, if_exists='replace')
    
    # --- 2. Generate Inventory (Historical Snapshots) ---
    logger.info("Generating Inventory Snapshots (Historical + Current)...")
    inventory_data = []
    
    # Snapshot dates: 1st of every month in the last 12 months + Today
    snapshot_dates = [START_DATE + timedelta(days=30*i) for i in range(12)]
    snapshot_dates.append(datetime.now())
    
    # Optimization: Not every product is in every store.
    # Online store has 90% products, Physical stores have 30% products
    # To reduce size: Online (Store 1) + 1 Physical Store (Store 2) get full history?
    # Or just sample products? 
    # User claimed 135k rows. 13 snapshots.
    # 135,000 / 13 ~= 10,000 rows per snapshot.
    # We have 30k products. So we can't snapshot ALL products for ALL stores.
    # Let's snapshot Top 2000 products for all stores (~10k rows) per month?
    # OR snapshot ALL products only for Online Store? 
    # Let's stick to the previous logic but apply to limited items for history to match volume.
    
    # Let's allow growing volume. 
    # If we do full coverage: 5 stores * 30k products = 150k rows PER SNAPSHOT. 
    # 13 snapshots = 2 Million rows. 
    # User loved the "135k" number. 
    # Let's generate ~10k records per snapshot (Sampled products).
    
    ids = [p['product_id'] for p in product_list]
    sampled_ids = random.sample(ids, k=min(2000, len(ids))) # Track 2000 core items across time
    
    for snap_date in snapshot_dates:
        s_date = snap_date.date()
        for _, store in stores.iterrows():
             # Physical stores only track a subset of the subset
             if store['type'] == 'Physical':
                 current_store_ids = random.sample(sampled_ids, k=500)
             else:
                 current_store_ids = sampled_ids # Online tracks all 2000 core items
                 
             for pid in current_store_ids:
                inventory_data.append({
                    'snapshot_date': s_date,
                    'store_id': store['store_id'],
                    'product_id': pid,
                    'stock_on_hand': random.randint(0, 100),
                    'reorder_point': random.randint(5, 10),
                    'last_restock_date': snap_date - timedelta(days=random.randint(0, 30))
                })
                
    df_inventory = pd.DataFrame(inventory_data)
    insert_data(df_inventory, 'fact_inventory', engine, if_exists='replace')
    
    # --- 3. Verification Log ---
    logger.info("--- Data Verification ---")
    logger.info(f"Target Orders: {TARGET_NUM_ORDERS}")
    logger.info(f"Actual Unique Orders: {df_sales['order_id'].nunique()}")
    logger.info(f"Actual Line Items: {len(df_sales)}")
    logger.info(f"Inventory Snapshots Rows: {len(df_inventory)}")
    logger.info(f"Unique Products in Inventory: {df_inventory['product_id'].nunique()}")

def main():
    engine = get_engine()
    generate_stores(engine)
    generate_customers(engine)
    generate_sales_and_inventory(engine)
    logger.info("Data Generation Complete (Enterprise Mode V2).")

if __name__ == "__main__":
    main()
