from sqlalchemy import create_engine, MetaData
from databases import Database
import os

# Ensure the directory exists
os.makedirs("app_data", exist_ok=True)

# Set path to app_data/data.db
DATABASE_URL = "sqlite:///./app_data/data.db"

# Connect
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
