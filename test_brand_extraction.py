import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import re

load_dotenv()

# Database Connection
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "asos_ecommerce")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

def extract_brand(name):
    if not name:
        return None
    
    # Heuristic: Take leading Title/Upper case words
    # Split by space
    words = name.split()
    brand_words = []
    
    for word in words:
        if not word: continue
        # Check if word contains uppercase letter (Simple check for consistency)
        # OR just check if it STARTS with uppercase
        if word[0].isupper():
            brand_words.append(word)
        else:
            break
            
    if not brand_words:
        # Fallback: Just take first word if available
        return words[0] if words else None
        
    # Validation: Some brands might be "New Look" but "ASOS DESIGN" or "River Island"
    # User said "New Look boxy..." -> "New Look"
    # "Bershka faux..." -> "Bershka"
    
    return " ".join(brand_words)

# Fetch sample data
query = "SELECT name FROM dim_product LIMIT 20"
try:
    df = pd.read_sql(query, engine)
    if df.empty:
        # Try stg_asos_raw if dim_product is empty
        query = "SELECT name FROM stg_asos_raw LIMIT 20"
        df = pd.read_sql(query, engine)
        print("Fetched from stg_asos_raw")
    else:
        print("Fetched from dim_product")

    print(f"{'Original Name':<50} | {'Extracted Brand':<20}")
    print("-" * 75)
    
    for name in df['name']:
        brand = extract_brand(name)
        print(f"{str(name)[:47]:<50} | {str(brand):<20}")

except Exception as e:
    print(f"Error: {e}")
