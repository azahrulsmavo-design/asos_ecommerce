
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "asos_ecommerce")

try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cur = conn.cursor()
    
    tables = ["dim_product", "dim_customer", "dim_store", "fact_sales", "fact_inventory"]
    
    print("--- Verification Results ---")
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"{table}: {count}")
        except Exception as e:
            print(f"{table}: Error {e}")
            conn.rollback() # Rollback in case of error to proceed to next
            
    cur.close()
    conn.close()

except Exception as e:
    print(f"Database Connection Error: {e}")
