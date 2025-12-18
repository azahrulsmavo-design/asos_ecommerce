from sqlalchemy import create_engine, text
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

def apply_schema():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Creating brand_master table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS brand_master (
                    brand_master_id SERIAL PRIMARY KEY,
                    brand_canonical TEXT UNIQUE NOT NULL,
                    brand_parent TEXT,
                    is_sub_brand BOOLEAN DEFAULT FALSE,
                    active_flag BOOLEAN DEFAULT TRUE
                );
            """))
            
            print("Creating brand_alias table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS brand_alias (
                    alias_id SERIAL PRIMARY KEY,
                    brand_master_id INT REFERENCES brand_master(brand_master_id),
                    alias_text TEXT UNIQUE NOT NULL,
                    source TEXT,
                    confidence NUMERIC
                );
            """))

            print("Adding brand_master_id to dim_product...")
            # Check if column exists first
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='dim_product' AND column_name='brand_master_id';
            """))
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE dim_product 
                    ADD COLUMN brand_master_id INT REFERENCES brand_master(brand_master_id);
                """))
                print("Column added.")
            else:
                print("Column already exists.")

            trans.commit()
            print("✅ Schema applied successfully!")
        except Exception as e:
            trans.rollback()
            print(f"❌ Error applying schema: {e}")

if __name__ == "__main__":
    apply_schema()
