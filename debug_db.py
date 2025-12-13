import os
from src.config import Config
import sqlalchemy

print("--- DEBUG INFO ---")
print(f"Current Working Dir: {os.getcwd()}")
print(f"DB_HOST: {Config.DB_HOST}")
print(f"DB_PORT: {Config.DB_PORT}")
print(f"DB_NAME: {Config.DB_NAME}")
print(f"DB_USER: {Config.DB_USER}")
print(f"DB_PASSWORD: {Config.DB_PASSWORD}")
print(f"Constructed URL: {Config().DATABASE_URL}")

try:
    engine = sqlalchemy.create_engine(Config().DATABASE_URL)
    with engine.connect() as conn:
        print("✅ CONNECTION SUCCESSFUL!")
        result = conn.execute(sqlalchemy.text("SELECT version();"))
        print(f"DB Version: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")
