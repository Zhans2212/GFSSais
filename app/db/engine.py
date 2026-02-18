from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import oracledb
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from app.db.models import Base

# Optional: thin mode (default)
# oracledb.init_oracle_client(lib_dir="path_to_instant_client")  # only if thick mode

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in your .env file or in the OS environment."
        )
    return value


DB_USER = "dasorp_test"
DB_PASSWORD = "dasorp"
DB_HOST = "192.168.20.60"
DB_PORT = "1521"
DB_SERVICE = "gfssdb.gfss.kz"

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