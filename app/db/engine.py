from sqlalchemy import create_engine
import os
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path("app/.env")
load_dotenv(dotenv_path=dotenv_path)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SERVICE = os.getenv("DB_SERVICE")

DATABASE_URL = (
    f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/"
    f"?service_name={DB_SERVICE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)