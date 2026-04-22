from sqlalchemy import text

from app.db.engine import engine

def _fetch_cursor_data(query: str, params: dict) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        row = result.fetchone()

        if not row or not row[0]:
            return []

        cursor = row[0]
        try:
            columns = [col[0].lower() for col in cursor.description]
            return [dict(zip(columns, r)) for r in cursor.fetchall()]
        finally:
            cursor.close()


def get_refunds(status: int, package_name: str = "DASORP_TEST") -> list[dict]:
    query = f"""
            SELECT {package_name}.MANAGE.GET_BY_STATUS(:status) AS refund_cursor 
            FROM DUAL
        """
    return _fetch_cursor_data(query, {"status": status})

def get_refunds_list(status: int, package_name: str = "DASORP_TEST") -> list[dict]:
    query = f"""
            SELECT {package_name}.MANAGE.GET_BY_STATUS_LIST(:status) AS refund_list_cursor 
            FROM DUAL
        """
    return _fetch_cursor_data(query, {"status": status})


def get_persons_by_sior(sior_id: int, package_name: str = "DASORP_TEST"):
    query = text(
        f"SELECT {package_name}.MANAGE.GET_ORDER_INFO(:sior_id) AS person_cursor FROM DUAL"
    )

    with engine.connect() as conn:
        result = conn.execute(query, {"sior_id": sior_id})
        row = result.fetchone()

        persons = []

        if row and row[0]:
            cursor = row[0]
            try:
                columns = [col[0].lower() for col in cursor.description]
                persons = [dict(zip(columns, r)) for r in cursor.fetchall()]
            finally:
                cursor.close()

    return persons


def get_order_rows(package_name: str = "DASORP_TEST") -> list:
    query = text(f"SELECT {package_name}.MANAGE.GET_ORDER() FROM DUAL")

    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()

        if not row or not row[0]:
            return []

        cursor = row[0]
        try:
            return cursor.fetchall()
        finally:
            cursor.close()


def get_who_approved(package_name: str = "DASORP_TEST"):
    conn = engine.raw_connection()
    cursor = conn.cursor()

    try:
        post = cursor.var(str)
        fio = cursor.var(str)

        cursor.callproc(
            f"{package_name}.MANAGE.GET_PASSPORT",
            [post, fio]
        )

        return {
            "post": post.getvalue(),
            "fio": fio.getvalue()
        }
    finally:
        cursor.close()
        conn.close()
