import oracledb
import json
from sqlalchemy import text

from app.db.engine import engine
from app.utils.logger import log


def _fetch_cursor_data(query: str, params=None) -> list[dict]:
    if params is None:
        params = {}
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

def _call_proc_with_cursor(proc_name: str, params: dict) -> list[dict]:
    conn = engine.raw_connection()
    cursor = conn.cursor()

    try:
        rc = cursor.var(oracledb.CURSOR)

        # добавляем rc в параметры
        call_params = params.copy()
        call_params["rc"] = rc

        # формируем PL/SQL блок
        placeholders = ", ".join(f":{k}" for k in call_params.keys())

        cursor.execute(f"""
        begin
            {proc_name}({placeholders});
        end;
        """, call_params)

        result_cursor = rc.getvalue()

        if not result_cursor:
            return []

        columns = [col[0].lower() for col in result_cursor.description]
        return [dict(zip(columns, r)) for r in result_cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()


def get_refunds(status: int, package_name: str = "DASORP_TEST") -> list[dict]:
    query = f"""
            SELECT {package_name}.MANAGE.GET_BY_STATUS(:status) AS refund_cursor 
            FROM DUAL
        """
    return _fetch_cursor_data(query, {"status": status})

def get_refunds_by_filter(package_name: str = "DASORP_TEST", **filters) -> list[dict]:
    clean = {k: v for k, v in filters.items() if v is not None}
    if "date_from" in clean:
        clean["date_from"] = clean["date_from"].isoformat()

    log.info("CLEAN FILTERS: %s", clean)

    return _call_proc_with_cursor(
        f"{package_name}.MANAGE.GET_BY_FILTER",
        {
            "p_filter": json.dumps(clean, ensure_ascii=False)
        }
    )

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


def get_418_rows(package_name: str = "DASORP_TEST") -> list:
    query = f"""
                SELECT {package_name}.MANAGE.GET_418_INFO() FROM DUAL
            """

    return _fetch_cursor_data(query)


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
