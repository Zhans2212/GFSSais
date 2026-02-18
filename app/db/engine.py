from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import oracledb
import os
from pathlib import Path
from dotenv import load_dotenv

# Optional: thin mode (default)
# oracledb.init_oracle_client(lib_dir="path_to_instant_client")  # only if thick mode

dotenv_path = Path('app/.env')
load_dotenv(dotenv_path=dotenv_path)

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_SERVICE = os.getenv('DB_SERVICE')

DATABASE_URL = (
    f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/"
    f"?service_name={DB_SERVICE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Dependency для сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()