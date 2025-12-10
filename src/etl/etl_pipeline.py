import pandas as pd
import ast
import logging
import numpy as np
import sqlalchemy
from src.config import Config
from src.utils.db_utils import get_engine, insert_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_parse_list(x):
    """Safely parse string representation of list/dict."""
    if pd.isna(x):
        return []
    try:
        # User dataset description often uses Python object string representation
        return ast.literal_eval(x)
    except (ValueError, SyntaxError):
        return []

def extract_info_from_desc(desc_list, key_to_find):
    """
    Extract value from the list of dicts in description.
    Example desc_list: [{'Brand': 'Nike'}, {'About Me': '100% Cotton'}]
    """
    if not isinstance(desc_list, list):
        return None
    
    for item in desc_list:
        if isinstance(item, dict):
            if key_to_find in item:
                return item[key_to_find]
    return None

def main():
    logger.info("Starting ETL Pipeline...")
    engine = get_engine()

    # --- 1. EXTRACT ---
    logger.info("Reading raw data...")
    try:
        df = pd.read_parquet(Config.RAW_DATA_PATH)
    except FileNotFoundError:
        logger.error(f"File not found at {Config.RAW_DATA_PATH}. Run ingestion first.")
        return

    # Basic cleaning
    # Rename columns to match what we expect or keep as is?
    # User columns: url, name, size, category, price, color, sku, description, images
    
    # Parse Description
    logger.info("Parsing descriptions...")
    df['desc_parsed'] = df['description'].apply(safe_parse_list)
    
    # Extract Brand and Material from Description
    df['brand_extracted'] = df['desc_parsed'].apply(lambda x: extract_info_from_desc(x, 'Brand'))
    df['about_me'] = df['desc_parsed'].apply(lambda x: extract_info_from_desc(x, 'About Me'))
    
    # --- 2. TRANSFORM DIMENSIONS ---

    # A. Dim Brand
    # Use extracted brand, fallback to generic if null?
    # Or maybe some brand info is in 'name'? Let's stick to extracted for now.
    unique_brands = df['brand_extracted'].dropna().unique()
    df_brand = pd.DataFrame(unique_brands, columns=['brand_name'])
    df_brand['brand_id'] = range(1, len(df_brand) + 1)
    
    # B. Dim Category
    unique_categories = df['category'].dropna().unique()
    df_category = pd.DataFrame(unique_categories, columns=['category_name'])
    df_category['category_id'] = range(1, len(df_category) + 1)
    # Optional: Logic for category_group could go here

    # C. Dim Color
    unique_colors = df['color'].dropna().unique()
    df_color = pd.DataFrame(unique_colors, columns=['color_name'])
    df_color['color_id'] = range(1, len(df_color) + 1)

    # D. Dim Material
    unique_materials = df['about_me'].dropna().unique()
    df_material = pd.DataFrame(unique_materials, columns=['material_desc'])
    df_material['material_id'] = range(1, len(df_material) + 1)
    # Simple 'main material' extraction could be added (e.g. regex for "Cotton", "Polyester")
    df_material['material_main'] = df_material['material_desc'].apply(lambda x: x.split(',')[0] if x else None)

    # E. Dim Size (Complex because of Many-to-Many potential)
    # But wait, the raw data row is one product. The 'size' column is a string "UK 4, UK 6".
    # We need a master list of all sizes.
    
    # First, get all unique size strings from the comma separated lists
    all_sizes = set()
    for sizes_str in df['size'].dropna():
        # sizes often come as "UK 6, UK 8, UK 10"
        parts = [s.strip() for s in sizes_str.split(',')]
        all_sizes.update(parts)
        
    df_size = pd.DataFrame(list(all_sizes), columns=['size_label'])
    df_size['size_id'] = range(1, len(df_size) + 1)
    # Try to determine region
    df_size['region'] = df_size['size_label'].apply(lambda x: 'UK' if 'UK' in x else ('US' if 'US' in x else ('EU' if 'EU' in x else 'Other')))
    # Try to extract numeric
    df_size['size_numeric'] = df_size['size_label'].str.extract(r'(\d+)').astype(float)


    # --- 3. MAP IDS BACK TO MAIN DF ---
    logger.info("Mapping IDs...")
    
    # Map Brand
    df = df.merge(df_brand, left_on='brand_extracted', right_on='brand_name', how='left')
    
    # Map Category
    df = df.merge(df_category, left_on='category', right_on='category_name', how='left')
    
    # Map Color
    df = df.merge(df_color, left_on='color', right_on='color_name', how='left')
    
    # Map Material
    df = df.merge(df_material, left_on='about_me', right_on='material_desc', how='left')
    
    # Clean Price column (ensure numeric)
    # Removing currency symbols if present
    if df['price'].dtype == 'object':
        try:
             # Keep only digits and decimal point
             df['price'] = df['price'].astype(str).str.replace(r'[^\d\.]', '', regex=True)
        except Exception:
             pass
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # --- 4. PREPARE FACT & PRODUCT TABLES ---
    
    # Dim Product
    # Columns: product_id, sku, name, url, brand_id, category_id, color_id, material_id, base_price, has_multiple_sizes, num_sizes, num_images, description_clean
    
    # robustly handle missing SKUs
    df['sku_clean'] = df['sku'].copy()
    mask_sku_null = df['sku_clean'].isna()
    if mask_sku_null.any():
        # Fallback to id_raw if exists, else index
        if 'id_raw' in df.columns:
             df.loc[mask_sku_null, 'sku_clean'] = df.loc[mask_sku_null, 'id_raw'].astype(str)
        else:
             df.loc[mask_sku_null, 'sku_clean'] = df.index[mask_sku_null].astype(str)
    
    # Ensure SKUs are unique
    df.drop_duplicates(subset=['sku_clean'], keep='first', inplace=True)
    
    # Calculate size metrics
    df['size_list'] = df['size'].apply(lambda x: [s.strip() for s in x.split(',')] if pd.notna(x) else [])
    df['num_sizes'] = df['size_list'].apply(len)
    df['has_multiple_sizes'] = df['num_sizes'] > 1
    
    # Calculate image metrics
    df['images_list'] = df['images'].apply(safe_parse_list)
    df['num_images'] = df['images_list'].apply(len)
    
    # Clean Description text
    # Join the list of dicts into a readable string or just keep raw?
    # Let's just keep the raw 'About Me' or 'Product Details' as the clean description for now
    df['description_clean'] = df['desc_parsed'].apply(lambda x: str(x)) 

    # Prepare final dim_product DataFrame
    # Note: dim_product PK is product_id (serial). 
    # But for insertion, we might want to generate it here to use it for Fact/Bridge?
    # Yes.
    df['product_id'] = range(1, len(df) + 1)
    
    dim_product_output = df[[
        'product_id', 'sku_clean', 'name', 'url', 'brand_id', 'category_id', 
        'color_id', 'material_id', 'price', 'has_multiple_sizes', 
        'num_sizes', 'num_images', 'description_clean'
    ]].copy()
    dim_product_output.rename(columns={'price': 'base_price', 'sku_clean': 'sku'}, inplace=True)
    
    
    # Fact Product Attributes
    fact_output = df[[
        'product_id', 'price', 
        'num_sizes', 'num_images'
    ]].copy()
    
    # Derived fact columns
    fact_output['desc_length_chars'] = df['description_clean'].str.len()
    fact_output['has_neutral_color'] = df['color'].apply(lambda x: 1 if x and any(c in str(x).lower() for c in ['black', 'white', 'grey', 'beige']) else 0).astype(bool)
    
    # Price Buckets
    price_q33 = df['price'].quantile(0.33)
    price_q66 = df['price'].quantile(0.66)
    def get_price_bucket(p):
        if pd.isna(p): return None
        if p <= price_q33: return 'Low'
        elif p <= price_q66: return 'Mid'
        else: return 'High'
    fact_output['price_bucket'] = df['price'].apply(get_price_bucket)
    
    # --- 5. BRIDGE TABLE LOGIC ---
    logger.info("Building Bridge Table...")
    
    # Explode product sizes
    # We have product_id and size_list
    bridge_data = []
    
    # Create a map for size_label -> size_id
    size_label_to_id = dict(zip(df_size['size_label'], df_size['size_id']))
    
    for pid, sizes in zip(df['product_id'], df['size_list']):
        for s_label in sizes:
            if s_label in size_label_to_id:
                bridge_data.append({'product_id': pid, 'size_id': size_label_to_id[s_label]})
                
    bridge_product_size = pd.DataFrame(bridge_data)
    # Drop duplicates if any
    bridge_product_size.drop_duplicates(inplace=True)


    # --- 6. LOAD TO DB ---
    logger.info("Loading to Database...")
    
    # Truncate tables first? Or append?
    # For this dev/demo run, let's clear existing data (CASCADE) or just use if_exists='replace' (but replace drops the table and schema constraints!)
    # Better to truncate using connection execute.
    
    with engine.connect() as conn:
        logger.info("Truncating tables...")
        conn.execute(sqlalchemy.text("TRUNCATE TABLE fact_product_attributes, bridge_product_size, dim_product, dim_size, dim_material, dim_color, dim_category, dim_brand CASCADE"))
        conn.commit()

    insert_data(df_brand, 'dim_brand', engine)
    insert_data(df_category, 'dim_category', engine)
    insert_data(df_color, 'dim_color', engine)
    insert_data(df_material, 'dim_material', engine)
    insert_data(df_size, 'dim_size', engine)
    
    insert_data(dim_product_output, 'dim_product', engine)
    
    insert_data(bridge_product_size, 'bridge_product_size', engine)
    insert_data(fact_output, 'fact_product_attributes', engine)
    
    logger.info("ETL Completed Successfully.")

if __name__ == "__main__":
    main()
