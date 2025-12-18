import pandas as pd
from sqlalchemy import create_engine, text
import sqlalchemy.types
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

def extract_brand(name):
    if not name:
        return None
    words = name.split()
    brand_words = []
    
    for word in words:
        if not word: continue
        # Heuristic: Take leading Title/Upper case words
        if word[0].isupper():
            brand_words.append(word)
        else:
            break
            
    if not brand_words:
        return words[0] if words else "Unknown"
        
    return " ".join(brand_words)

def fix_brands():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("1. Fetching products...")
            df = pd.read_sql("SELECT product_id, name FROM dim_product", conn)
            print(f"   Found {len(df)} products.")
            
            if df.empty:
                print("   No products found in dim_product. Checking stg_asos_raw...")
                # If dim_product is empty, we can't extract brands for it?
                # Assuming pipeline flow: stg -> dim_product + dim_brand
                # If dim_product is empty, we should populate it first?
                # User request implies updating existing incorrect data.
                # If dim_product is empty, there is nothing to update.
                print("   WARNING: dim_product is empty. Aborting update.")
                return

            print("2. Extracting brand names...")
            df['brand_name'] = df['name'].apply(extract_brand)
            unique_brands = df['brand_name'].unique()
            unique_brands = [b for b in unique_brands if b] # filter None
            print(f"   Identified {len(unique_brands)} unique brands.")
            print(f"   Sample: {unique_brands[:5]}")

            print("3. Resetting dim_brand table...")
            # Unlink products first
            conn.execute(text("UPDATE dim_product SET brand_id = NULL"))
            # Clear brands
            conn.execute(text("DELETE FROM dim_brand"))
            # Reset sequence if possible (optional)
            try:
                conn.execute(text("ALTER SEQUENCE dim_brand_brand_id_seq RESTART WITH 1"))
            except Exception as e:
                print(f"   (Could not reset sequence: {e})")

            print("4. Inserting new brands...")
            # Insert unique brands
            params = [{"name": b} for b in unique_brands]
            # Use raw SQL for insertion to get IDs back or just insert and read back
            # Bulk insert
            conn.execute(
                text("INSERT INTO dim_brand (brand_name) VALUES (:name)"),
                params
            )
            
            print("5. Mapping brands to products...")
            # Fetch back brand IDs
            brands_df = pd.read_sql("SELECT brand_id, brand_name FROM dim_brand", conn)
            brand_map = dict(zip(brands_df['brand_name'], brands_df['brand_id']))
            
            # Update df with brand_id
            df['brand_id'] = df['brand_name'].map(brand_map)
            
            # Prepare update data for dim_product
            # Create a temp table or use a loop?
            # For robustness with small data, loop is safely easy.
            # But let's try a bulk update approach if possible.
            # SQLAlchemy `update` with `bindparam`?
            
            # For simplicity:
            print("   Updating dim_product (this might take a moment)...")
            
            # Ensure brand_id is nullable integer
            # map returns NaN for missing keys, so we fillna with something or keep as float-like with NaNs
            # But for SQL insert, we want None.
            # Pandas Int64 handles NaNs.
            df['brand_id'] = df['brand_id'].astype("Int64") # Nullable integer type
            
            # Create temp table using pandas to schema match
            # We need to make sure we are in the same transaction context?
            # to_sql with 'method' might need connection.
            
            # Using temporary table with to_sql
            df[['product_id', 'brand_id']].rename(columns={'product_id':'p_id', 'brand_id':'b_id'}).to_sql(
                'tmp_product_brands', 
                conn, 
                if_exists='replace', 
                index=False,
                dtype={'p_id': sqlalchemy.types.Integer, 'b_id': sqlalchemy.types.Integer}
            )
            
            # Perform update
            conn.execute(text("""
                UPDATE dim_product
                SET brand_id = tmp_product_brands.b_id
                FROM tmp_product_brands
                WHERE dim_product.product_id = tmp_product_brands.p_id
            """))
            
            conn.execute(text("DROP TABLE tmp_product_brands"))
            
            trans.commit()
            print("SUCCESS: Successfully updated brands!")
            
        except Exception as e:
            trans.rollback()
            print(f"ERROR: Error occurred: {repr(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    fix_brands()
