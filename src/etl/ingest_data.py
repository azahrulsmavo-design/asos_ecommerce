import os
import logging
from datasets import load_dataset
import pandas as pd
from src.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_data():
    """
    Downloads the ASOS product dataset from Hugging Face and saves it locally.
    """
    dataset_name = "UniqueData/asos-e-commerce-dataset"
    logger.info(f"Starting data ingestion from {dataset_name}...")

    try:
        # Load dataset
        # Note: This might require authentication. Ensure `huggingface-cli login` is run if needed.
        # Although this specific dataset might be public.
        ds = load_dataset(dataset_name, split='train')
        logger.info(f"Dataset loaded successfully. Rows: {len(ds)}")

        # Convert to Pandas DataFrame for easier handling in staging
        df = ds.to_pandas()
        
        # Create output directory if not exists
        os.makedirs(os.path.dirname(Config.RAW_DATA_PATH), exist_ok=True)
        
        # Save to Parquet (efficient storage)
        df.to_parquet(Config.RAW_DATA_PATH, index=False)
        logger.info(f"Raw data saved to {Config.RAW_DATA_PATH}")
        
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise

if __name__ == "__main__":
    ingest_data()
