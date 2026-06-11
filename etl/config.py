import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cart_db")
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY", "")
BRONZE_CONTAINER = "bronze"
SILVER_CONTAINER = "silver"
GOLD_CONTAINER = "gold"
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/etl")
