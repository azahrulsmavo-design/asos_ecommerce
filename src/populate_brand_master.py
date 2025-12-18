import pandas as pd
from sqlalchemy import create_engine, text
import os
import re
from rapidfuzz import fuzz
from src.utils.db_utils import get_engine

def normalize_brand(b):
    if not b: return ""
    b = str(b).lower().strip()
    b = re.sub(r"[^a-z0-9\s]", "", b)
    b = re.sub(r"\s+", " ", b)
    return b

def get_canonical_name(variants):
    return sorted(variants, key=lambda x: (sum(1 for c in str(x) if c.isupper()), str(x)), reverse=True)[0]

def populate_master():
    engine = get_engine()
    print("1. Fetching raw brands ...", flush=True)
    
    try:
        with engine.connect() as conn:
            # READ
            df = pd.read_sql(text("SELECT brand_id, brand_name FROM dim_brand"), conn)
            
            if df.empty:
                print("No brands to process.", flush=True)
                return
            
            print(f"   Found {len(df)} entries.", flush=True)
            
            # PROCESS
            df['normalized'] = df['brand_name'].apply(normalize_brand)
            groups = df.groupby('normalized')['brand_name'].unique()
            unique_norms = list(groups.index)
            unique_norms.sort()
            
            visited = set()
            clusters = [] 
            norm_to_raw = groups.to_dict()
            
            print("2. Clustering...", flush=True)
            for i, norm_a in enumerate(unique_norms):
                if norm_a in visited: continue
                if not norm_a: continue 
                
                cluster_norms = [norm_a]
                visited.add(norm_a)
                
                for norm_b in unique_norms[i+1:]:
                    if norm_b in visited: continue
                    if abs(len(norm_a) - len(norm_b)) > 3: continue
                    
                    if fuzz.ratio(norm_a, norm_b) >= 90:
                        cluster_norms.append(norm_b)
                        visited.add(norm_b)
                
                all_raw_variants = []
                for n in cluster_norms:
                    all_raw_variants.extend(norm_to_raw[n])
                
                all_raw_variants = list(set(all_raw_variants))
                canonical = get_canonical_name(all_raw_variants)
                
                clusters.append({
                    "canonical": str(canonical),
                    "aliases": [str(a) for a in all_raw_variants],
                })
                
            print(f"   Identified {len(clusters)} unique brand masters.", flush=True)
            
            # WRITE
            print("3. DB Update...", flush=True)
            
            # Reset (Use DELETE to avoid CASCADE wiping dim_product)
            conn.execute(text("UPDATE dim_product SET brand_master_id = NULL"))
            conn.execute(text("DELETE FROM brand_alias"))
            conn.execute(text("DELETE FROM brand_master"))
            # Reset sequences
            conn.execute(text("ALTER SEQUENCE brand_master_brand_master_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE brand_alias_alias_id_seq RESTART WITH 1"))
            conn.commit()
            
            # Insert Master
            master_df = pd.DataFrame([{"brand_canonical": c['canonical']} for c in clusters])
            master_df.to_sql('brand_master', conn, if_exists='append', index=False)
            
            # Read IDs
            saved_masters = pd.read_sql(text("SELECT brand_master_id, brand_canonical FROM brand_master"), conn)
            canonical_to_id = dict(zip(saved_masters['brand_canonical'], saved_masters['brand_master_id']))
            
            # Insert Alias
            alias_rows = []
            raw_to_master = {}
            for c in clusters:
                mid = canonical_to_id.get(c['canonical'])
                if not mid: continue
                for alias in c['aliases']:
                    alias_rows.append({
                        "brand_master_id": mid,
                        "alias_text": alias,
                        "source": "dim_brand",
                        "confidence": 1.0
                    })
                    raw_to_master[alias] = mid
            
            alias_df = pd.DataFrame(alias_rows)
            alias_df.to_sql('brand_alias', conn, if_exists='append', index=False)
            
            # Update Product
            map_df = pd.DataFrame([{"raw_name": k, "m_id": v} for k, v in raw_to_master.items()])
            map_df.to_sql('tmp_brand_map', conn, if_exists='replace', index=False)
            
            conn.execute(text("""
                UPDATE dim_product
                SET brand_master_id = m.m_id
                FROM dim_brand b, tmp_brand_map m
                WHERE dim_product.brand_id = b.brand_id
                    AND b.brand_name = m.raw_name
            """))
            conn.execute(text("DROP TABLE tmp_brand_map"))
            conn.commit()
            
            print("[SUCCESS] Brand Master populated!", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    populate_master()
