import pandas as pd
import sqlalchemy
from src.config import Config
import logging

logger = logging.getLogger(__name__)

def get_engine():
    """Create and return a SQLAlchemy engine."""
    return sqlalchemy.create_engine(Config().DATABASE_URL)

def insert_data(df, table_name, engine, if_exists='append'):
    """
    Insert DataFrame into PostgreSQL table.
    
    Args:
        df (pd.DataFrame): Data to insert.
        table_name (str): Target table name.
        engine (sqlalchemy.engine.Engine): Database engine.
        if_exists (str): 'fail', 'replace', or 'append'. Default 'append'.
    """
    try:
        logger.info(f"Inserting {len(df)} rows into {table_name}...")
        df.to_sql(table_name, engine, if_exists=if_exists, index=False, method='multi', chunksize=1000)
        logger.info(f"Successfully inserted into {table_name}.")
    except Exception as e:
        logger.error(f"Failed to insert into {table_name}: {e}")
        raise
