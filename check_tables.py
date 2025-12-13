
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "asos_ecommerce")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

tables = ["dim_product", "dim_customer", "dim_store", "fact_sales", "fact_inventory"]

print(f"{'Table':<20} | {'Row Count':<10}")
print("-" * 35)

for table in tables:
    try:
        count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", engine).iloc[0, 0]
        print(f"{table:<20} | {count:<10}")
    except Exception as e:
        print(f"{table:<20} | Error: {e}")

print("-" * 35)
