from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# --- Config ---
DATABASE_URL = "sqlite:///my_database.db"  # Update path/engine for other DBs
DB_FILE_PATH = DATABASE_URL.replace("sqlite:///", "")  # Extract path from URL


# --- DB Core ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # SQLite-specific arg
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# # --- Initialize DB (create tables) ---
# def init_db():
#     #if not os.path.exists(DB_FILE_PATH):
#     #    print(" Database file not found. Initializing...")
#     from models import File, DicomTag  # Import models here to register with Base
#     print("📁 DB URL:", engine.url)
#     print("📁 DB absolute path:", os.path.abspath("my_database.db"))
#     Base.metadata.create_all(bind=engine)
#     print("📦 Tables registered in metadata:", Base.metadata.tables.keys())
#     print("Database initialized.")
    
    
