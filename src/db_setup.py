import logging
import sqlalchemy
from src.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """
    Applies the schema.sql to the configured database.
    """
    logger.info("Connecting to database...")
    try:
        # Create engine
        engine = sqlalchemy.create_engine(Config().DATABASE_URL)
        
        # Read schema file
        with open('sql/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        with engine.connect() as connection:
            # We might need to split statements if the driver doesn't support multiple tokens
            # But usually sqlalchemy execute can handle it or we can use generic text
            connection.execute(sqlalchemy.text(schema_sql))
            connection.commit()
            
        logger.info("Database schema applied successfully.")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise

if __name__ == "__main__":
    setup_database()
