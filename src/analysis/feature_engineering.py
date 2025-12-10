import pandas as pd
import numpy as np
import logging
import sqlalchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from src.config import Config
from src.utils.db_utils import get_engine, insert_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Feature Engineering...")
    engine = get_engine()
    
    # 1. Load Data
    logger.info("Loading data from DB...")
    query = """
    SELECT 
        p.product_id, 
        p.description_clean, 
        p.category_id, 
        p.base_price,
        c.category_name
    FROM dim_product p
    JOIN dim_category c ON p.category_id = c.category_id
    WHERE p.base_price IS NOT NULL
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        logger.warning("No data found!")
        return

    # 2. Price Normalization (Z-Score per Category)
    logger.info("Computing Price Z-Scores...")
    # Group by category and compute z-score
    df['price_mean'] = df.groupby('category_id')['base_price'].transform('mean')
    df['price_std'] = df.groupby('category_id')['base_price'].transform('std')
    df['price_zscore'] = (df['base_price'] - df['price_mean']) / df['price_std'].replace(0, 1)
    
    # Fill NaN zscores (e.g. single item in category) with 0
    df['price_zscore'] = df['price_zscore'].fillna(0)

    # 3. Text Features (TF-IDF + PCA)
    logger.info("Generating Text Embeddings (TF-IDF + PCA)...")
    
    # TF-IDF
    tfidf = TfidfVectorizer(max_features=500, stop_words='english')
    # Filter out empty descriptions
    df['desc_text'] = df['description_clean'].fillna('')
    tfidf_matrix = tfidf.fit_transform(df['desc_text'])
    
    # PCA to reduce to 50 dimensions
    pca = PCA(n_components=50)
    pca_features = pca.fit_transform(tfidf_matrix.toarray())
    
    # Add PCA features to DF (as a list or individual columns? Let's use individual for DB or JSON?)
    # For DB simplicity, let's just store the cluster_id and maybe top few components if visualization needed.
    # User asked for "embeddings placeholder". 
    # Let's store the full array as a JSON/Array type if Postgres supports it, or just use it for clustering now.
    # Postgres has ARRAY type.
    
    # 4. Clustering (K-Means)
    logger.info("Clustering Products...")
    # Combine Price Z-Score and PCA features for clustering
    # Reshape price_zscore to (n_samples, 1)
    price_feature = df[['price_zscore']].values
    
    # Combine: Scale PCA features to match price scale? 
    # PCA features are already somewhat centered, but let's scale everything together.
    scaler = StandardScaler()
    combined_features = np.hstack([price_feature, pca_features])
    combined_features_scaled = scaler.fit_transform(combined_features)
    
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(combined_features_scaled)
    
    # 5. Save to Database
    logger.info("Saving features to fact_product_features...")
    
    # Prepare output table
    # Columns: product_id, price_zscore, cluster_id, embedding_vector (optional)
    
    # Create the table if not exists (using SQLAlchemy DDL or just to_sql with create)
    # Let's define it explicitly via SQL execution for better control, or rely on to_sql
    
    output_df = df[['product_id', 'price_zscore', 'cluster_id']].copy()
    
    # We can add embedding as a column (Postgres ARRAY)
    # output_df['embedding_vector'] = list(pca_features) 
    # Pandas -> SQL Array support varies. Let's skip vector storage for now to avoid complexity unless requested.
    # The requirement said "embeddings placeholder". Cluster ID is a good proxy for similarity groups.
    
    # To SQL
    output_df.to_sql('fact_product_features', engine, if_exists='replace', index=False)
    
    # Set PK for good measure (optional)
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE fact_product_features ADD PRIMARY KEY (product_id)"))
            conn.commit()
        except:
            pass # PK might fail if duplicates or replace logic varies, strictly optional
            
    logger.info(f"Feature engineering complete. {len(output_df)} rows saved.")

if __name__ == "__main__":
    main()
