from sqlalchemy import create_engine, text
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

def get_refund_list(reports_date: str):
    """
    Вызывает функцию DASORP.MANAGE.GET_REFUND_LIST, которая возвращает REF CURSOR,
    и преобразует результат в список словарей.
    """
    query = text("SELECT DASORP.MANAGE.GET_REFUND_LIST(:date) AS refund_cursor FROM DUAL")

    with engine.connect() as conn:
        result = conn.execute(query, {"date": reports_date})
        row = result.fetchone()
        refunds = []

        if row and row[0]:  # обращаемся по индексу, а не по строке
            cursor = row[0]
            columns = [col[0].lower() for col in cursor.description]
            refunds = [dict(zip(columns, r)) for r in cursor.fetchall()]
            cursor.close()

    return refunds