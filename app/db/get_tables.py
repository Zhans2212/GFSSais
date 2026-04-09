from sqlalchemy import text

from app.db.engine import engine


def get_refund_list(status: int, package_name: str = "DASORP_TEST") -> list[dict]:
    query = text(
        f"SELECT {package_name}.MANAGE.GET_BY_STATUS(:status) AS refund_cursor FROM DUAL"
    )

    with engine.connect() as conn:
        result = conn.execute(query, {"status": status})
        row = result.fetchone()

        refunds = []

        if row and row[0]:
            cursor = row[0]
            try:
                columns = [col[0].lower() for col in cursor.description]
                refunds = [dict(zip(columns, r)) for r in cursor.fetchall()]
            finally:
                cursor.close()

    return refunds


def get_person_by_iin(iin: str):
    query = text("""
        SELECT iin,
               lastname,
               firstname,
               middlename,
               birthdate,
               address
        FROM LOADER.person
        WHERE iin = :iin
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"iin": iin})
        return result.fetchone()


def get_order_rows(report_date: str) -> list:
    query = text("SELECT DASORP.MANAGE.GET_ORDER(:date) FROM DUAL")

    with engine.connect() as conn:
        result = conn.execute(query, {"date": report_date})
        row = result.fetchone()

        if not row or not row[0]:
            return []

        cursor = row[0]
        try:
            return cursor.fetchall()
        finally:
            cursor.close()