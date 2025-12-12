import pandas as pd
import numpy as np
import sqlalchemy
from datetime import datetime, timedelta
import random
import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config
from src.utils.db_utils import get_engine, insert_data, logger

# Constants
NUM_CUSTOMERS = 1000
NUM_TRANSACTIONS = 15000  # ~40 per day for a year
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
        logger.error("No products found! Please run the ETL pipeline first to load product data.")
        return

    stores = pd.read_sql("SELECT store_id, type FROM dim_store", engine)
    customer_ids = range(1, NUM_CUSTOMERS + 1)
    
    # 1. Generate Sales
    logger.info(f"Generating {NUM_TRANSACTIONS} Sales Transactions...")
    
    transactions = []
    
    # Seasonality weights (simple)
    month_weights = {
        1: 0.8, 2: 0.8, 3: 0.9, 4: 0.9, 5: 1.0, 6: 1.1,
        7: 1.1, 8: 1.0, 9: 1.0, 10: 1.1, 11: 1.5, 12: 1.8 # Peak in Nov/Dec
    }
    
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Klarna', 'Apple Pay']
    
    # Pre-compute product list for faster sampling
    product_list = products.to_dict('records')
    
    dates = []
    current = START_DATE
    while current <= END_DATE:
        dates.append(current)
        current += timedelta(days=1)
        
    transaction_id = 1
    
    # Vectorized generation approach would be faster, but loop is clearer for logic
    # To speed up, we'll batch generate
    
    # Randomly select dates with weights applied?
    # Let's iterate days and pick N transactions per day based on seasonality
    
    sales_data = []
    
    for day in dates:
        weight = month_weights.get(day.month, 1.0)
        # Base daily volume + noise
        daily_vol = int(random.normalvariate(40, 10) * weight)
        if daily_vol < 5: daily_vol = 5
        
        for _ in range(daily_vol):
            store = stores.sample(1).iloc[0]
            prod = random.choice(product_list)
            
            # Quantity skewed to 1
            qty = np.random.choice([1, 2, 3, 4, 5], p=[0.7, 0.15, 0.1, 0.03, 0.02])
            
            # Price variation (discount)
            discount_pct = np.random.choice([0, 0.1, 0.2, 0.5], p=[0.8, 0.1, 0.05, 0.05])
            final_price = prod['base_price'] * (1 - discount_pct)
            
            # Cost simulation (assuming ~40-60% margin)
            cost = prod['base_price'] * random.uniform(0.3, 0.5)
            
            sales_data.append({
                # 'transaction_id': transaction_id, # generating on insert or let pandas do it
                'date': day,
                'time': day.replace(hour=random.randint(8, 22), minute=random.randint(0, 59)),
                'store_id': store['store_id'],
                'customer_id': random.choice(customer_ids),
                'product_id': prod['product_id'],
                'quantity': qty,
                'unit_price': round(final_price, 2),
                'total_amount': round(final_price * qty, 2),
                'cost': round(cost * qty, 2),
                'profit': round((final_price * qty) - (cost * qty), 2),
                'payment_method': random.choice(payment_methods),
                'channel': 'Online' if store['type'] == 'Online' else 'Offline'
            })
            transaction_id += 1
            
    df_sales = pd.DataFrame(sales_data)
    df_sales['transaction_id'] = range(1, len(df_sales) + 1)
    
    insert_data(df_sales, 'fact_sales', engine, if_exists='replace')
    
    # 2. Generate Inventory
    logger.info("Generating Inventory Snapshots...")
    inventory_data = []
    
    # For each store, each product has some stock
    for _, store in stores.iterrows():
        for prod in product_list:
            # Not every store has every product, but most do
            if random.random() > 0.1: 
                inventory_data.append({
                    'store_id': store['store_id'],
                    'product_id': prod['product_id'],
                    'stock_on_hand': random.randint(0, 50),
                    'reorder_point': random.randint(5, 15),
                    'last_restock_date': datetime.now() - timedelta(days=random.randint(0, 30))
                })
                
    df_inventory = pd.DataFrame(inventory_data)
    insert_data(df_inventory, 'fact_inventory', engine, if_exists='replace')

def main():
    engine = get_engine()
    generate_stores(engine)
    generate_customers(engine)
    generate_sales_and_inventory(engine)
    logger.info("Mock Data Generation Complete!")

if __name__ == "__main__":
    main()
