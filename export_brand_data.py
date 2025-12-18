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

try:
    print("Attempting to fetch data from dim_brand...")
    # Check if table exists
    query = "SELECT * FROM dim_brand"
    df = pd.read_sql(query, engine)
    print(f"Successfully fetched {len(df)} rows from dim_brand.")
    
    # Export to CSV
    output_file = "brand_names.csv"
    df.to_csv(output_file, index=False)
    print(f"Exported to {os.path.abspath(output_file)}")

except Exception as e:
    print(f"Error fetching dim_brand: {e}")
    # Fallback: List tables to see what's available
    print("Listing all tables in public schema:")
    try:
        tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'", engine)
        print(tables)
    except Exception as e2:
        print(f"Error listing tables: {e2}")
