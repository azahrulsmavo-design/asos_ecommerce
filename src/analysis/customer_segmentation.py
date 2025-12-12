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
    
    # 1. Load Sales Data with Order ID
    logger.info("Loading Sales Data (Grain: Order ID)...")
    query = """
    SELECT customer_id, order_id, date, total_amount
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
    
    # Aggregation: 
    # Recency: Days since last order
    # Frequency: Count unique orders (not line items!)
    # Monetary: Sum of total_amount
    rfm = df.groupby('customer_id').agg({
        'date': lambda x: (reference_date - pd.to_datetime(x).max()).days,
        'order_id': 'nunique', # Corrected Frequency Logic
        'total_amount': 'sum'
    }).rename(columns={
        'date': 'Recency',
        'order_id': 'Frequency',
        'total_amount': 'Monetary'
    })
    
    # 3. Score Segments (Quintiles 1-5)
    # Recency: Lower is better (5 = Newest)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    # Frequency: Higher is better 
    # Note: If Frequency has low variance (e.g. most are 1), qcut might fail without duplicates='drop'
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    # Monetary: Higher is better
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    # Combine Scores
    rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    
    # Define Segment Names (Realistic Logic)
    def segment_label(row):
        r = int(row['R_Score'])
        f = int(row['F_Score'])
        m = int(row['M_Score'])

        # 1) Champions
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"

        # 2) Loyal Customers
        if f >= 4 and m >= 3 and r >= 3:
            return "Loyal Customers"

        # 3) Potential Loyalists
        if r >= 4 and f in [2, 3]:
            return "Potential Loyalists"

        # 4) New Customers
        if r >= 4 and f == 1:
            return "New Customers"

        # 5) Promising
        if r == 3 and f in [1, 2]:
            return "Promising"

        # 6) Need Attention
        if (r == 3 and f == 3) or (r in [2, 3] and m >= 3):
            return "Need Attention"

        # 7) At Risk
        if r <= 2 and (f >= 3 or m >= 4):
            return "At Risk"

        # 9) Lost (Specific)
        if r == 1 and f == 1 and m <= 2:
            return "Lost"

        # 8) Hibernating (Broad)
        if r <= 2 and f <= 2 and m <= 3:
            return "Hibernating"

        # Default fallback
        return "Others"
            
    rfm['Customer_Segment'] = rfm.apply(segment_label, axis=1)
    
    # 4. Save Results
    output_df = rfm.reset_index()[['customer_id', 'Recency', 'Frequency', 'Monetary', 'RFM_Segment', 'Customer_Segment']]
    
    logger.info(f"Saving {len(output_df)} segments to analysis_rfm_segments table...")
    output_df.to_sql('analysis_rfm_segments', engine, if_exists='replace', index=False)
    
    logger.info("Segmentation Complete.")
    logger.info("\n" + str(output_df['Customer_Segment'].value_counts()))

if __name__ == "__main__":
    main()
