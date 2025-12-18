import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import re
from rapidfuzz import fuzz

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

def evaluate_brands():
    print("Fetching brands from dim_brand...")
    df = pd.read_sql("SELECT brand_id, brand_name FROM dim_brand", engine)
    
    if df.empty:
        print("No brands found.")
        return

    print(f"Total brands: {len(df)}")

    # Step 1: Normalization
    df['brand_normalized'] = df['brand_name'].apply(normalize_brand)

    # Step 2: Detect Exact Duplicates (Normalized)
    dup_counts = df.groupby('brand_normalized').size().sort_values(ascending=False)
    duplicates = dup_counts[dup_counts > 1]
    
    print("\n--- STEP 2: Normalized Duplicates (Potential Merges) ---")
    if not duplicates.empty:
        print(f"Found {len(duplicates)} normalized collision groups.")
        for norm_name, count in duplicates.head(10).items():
            variations = df[df['brand_normalized'] == norm_name]['brand_name'].unique()
            print(f"- '{norm_name}' ({count}): {list(variations)}")
    else:
        print("No normalized duplicates found!")

    # Step 3: Fuzzy Matching
    print("\n--- STEP 3: Fuzzy Duplicates (Similarity > 90) ---")
    unique_norms = df['brand_normalized'].unique()
    checked = set()
    clusters = []

    # Simple O(N^2) comparison for unique normalized brands
    # Optimization: Use rapidfuzz process.cdist or similar if N is large. 
    # For < 30k brands, standard loop might be slow but okay for analysis.
    # Let's verify size first.
    if len(unique_norms) > 5000:
        print("Warning: Large number of brands, sampling top 1000 for fuzzy check.")
        unique_norms = unique_norms[:1000]

    processed_count = 0 
    for i, a in enumerate(unique_norms):
        if a in checked: continue
        
        current_cluster = [a]
        checked.add(a)
        
        for b in unique_norms[i+1:]:
            if b in checked: continue
            
            # Skip very short brands to avoid false positives?
            if len(a) < 3 or len(b) < 3: continue

            if fuzz.ratio(a, b) >= 90:
                current_cluster.append(b)
                checked.add(b)
        
        if len(current_cluster) > 1:
            clusters.append(current_cluster)
            
    if clusters:
        print(f"Found {len(clusters)} fuzzy clusters.")
        for cluster in clusters[:10]:
            # Get original names for these normalized values
            originals = df[df['brand_normalized'].isin(cluster)]['brand_name'].unique()
            print(f"Cluster {cluster}: {list(originals)}")
    else:
        print("No fuzzy duplicates found.")
        
    # Stats
    print("\n--- SUMMARY ---")
    print(f"Unique Raw Brands: {df['brand_name'].nunique()}")
    print(f"Unique Normalized Brands: {df['brand_normalized'].nunique()}")
    print(f"Potential Reduction: {df['brand_name'].nunique() - df['brand_normalized'].nunique()}")

if __name__ == "__main__":
    evaluate_brands()
