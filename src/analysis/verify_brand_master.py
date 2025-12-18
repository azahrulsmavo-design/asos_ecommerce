import pandas as pd
from sqlalchemy import create_engine, text
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

def normalize_brand(b):
    if not b: return ""
    b = str(b).lower().strip()
    b = re.sub(r"[^a-z0-9\s]", "", b)
    b = re.sub(r"\s+", " ", b)
    return b

def run_checklist():
    print("--- BRAND MASTER QUALITY CHECKLIST ---\n")
    
    with engine.connect() as conn:
        # 1. Normalized Duplicates
        print("1. Checking for Normalized Duplicates in brand_master...")
        result = conn.execute(text("SELECT brand_canonical FROM brand_master"))
        brands = [r[0] for r in result.fetchall()]
        
        normalized = [normalize_brand(b) for b in brands]
        
        # Count duplicates manually
        counts = {}
        for n in normalized:
            counts[n] = counts.get(n, 0) + 1
            
        dupes = {k: v for k, v in counts.items() if v > 1}
        
        if not dupes:
            print("[PASS] No normalized duplicates found.")
        else:
            print(f"[FAIL] Found {len(dupes)} duplicates!")
            print(list(dupes.keys())[:5])
            
        # 2. Canonical Casing Consistency
        print("\n2. Sample Canonical Names (Check Casing):")
        if len(brands) > 10:
            print(brands[:10])
        else:
            print(brands)
        
        # 3. ASOS Family Check
        print("\n3. ASOS Family Check (Rule 2)...")
        # Python-side filtering to avoid SQL param issues
        asos_brands = [b for b in brands if "ASOS" in b.upper()]
        print("   Found ASOS variations:")
        print(asos_brands)
        
        has_asos = "ASOS" in asos_brands
        has_asos_design = "ASOS DESIGN" in asos_brands
        
        if has_asos and has_asos_design:
             print("[PASS] ASOS and ASOS DESIGN are distinct.")
        else:
            print(f"[WARNING] ASOS/ASOS DESIGN distinction might be missing. Found: {asos_brands}")

        # 4. Coverage (dim_product link)
        print("\n4. Checking Product Coverage...")
        total_products = conn.execute(text("SELECT COUNT(*) FROM dim_product")).scalar()
        linked_products = conn.execute(text("SELECT COUNT(*) FROM dim_product WHERE brand_master_id IS NOT NULL")).scalar()
        
        coverage = (linked_products / total_products) * 100 if total_products > 0 else 0
        print(f"   Coverage: {coverage:.2f}% ({linked_products}/{total_products})")
        
        if coverage >= 95:
             print("[PASS] Coverage >= 95%")
        else:
             print("[FAIL] Coverage < 95%")

if __name__ == "__main__":
    run_checklist()
