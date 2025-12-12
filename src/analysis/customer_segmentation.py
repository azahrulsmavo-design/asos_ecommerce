import pandas as pd
import numpy as np
import logging
import sqlalchemy
import sys
import os
from datetime import datetime

# Add project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Config
from src.utils.db_utils import get_engine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Customer Segmentation Analysis (RFM)...")
    engine = get_engine()
    
    # 1. Load Sales Data
    query = """
    SELECT customer_id, date, total_amount
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    """
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        logger.error(f"Error loading sales data: {e}")
        return

    if df.empty:
        logger.warning("No sales data found. Cannot perform segmentation.")
        return

    # 2. Calculate RFM Metrics
    # Reference date = max date + 1 day
    reference_date = pd.to_datetime(df['date']).max() + pd.Timedelta(days=1)
    
    rfm = df.groupby('customer_id').agg({
        'date': lambda x: (reference_date - pd.to_datetime(x).max()).days, # Recency
        'customer_id': 'count', # Frequency
        'total_amount': 'sum'   # Monetary
    }).rename(columns={
        'date': 'Recency',
        'customer_id': 'Frequency',
        'total_amount': 'Monetary'
    })
    
    # 3. Score Segments (Quintiles 1-5)
    # Recency: Lower is better (5 = Newest)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    # Frequency: Higher is better
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    # Monetary: Higher is better
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    # Combine Scores
    rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    
    # Define Segment Names
    def segment_label(row):
        r = int(row['R_Score'])
        f = int(row['F_Score'])
        m = int(row['M_Score'])
        avg = (r + f + m) / 3
        
        if r >= 5 and f >= 5 and m >= 5:
            return "Champions"
        elif r >= 4 and f >= 4:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "New Customers"
        elif r <= 2 and f >= 4:
            return "At Risk"
        elif r <= 2 and f <= 2:
            return "Lost"
        else:
            return "Potential Loyalist"
            
    rfm['Customer_Segment'] = rfm.apply(segment_label, axis=1)
    
    # 4. Save Results
    # We could update dim_customer or create fact_customer_segmentation.
    # Let's create a new table for clarity: analysis_rfm_segments
    
    output_df = rfm.reset_index()[['customer_id', 'Recency', 'Frequency', 'Monetary', 'RFM_Segment', 'Customer_Segment']]
    
    logger.info(f"Saving {len(output_df)} segments to analysis_rfm_segments table...")
    output_df.to_sql('analysis_rfm_segments', engine, if_exists='replace', index=False)
    
    logger.info("Segmentation Complete.")
    logger.info("\n" + str(output_df['Customer_Segment'].value_counts()))

if __name__ == "__main__":
    main()
