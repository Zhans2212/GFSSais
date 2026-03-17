from sqlalchemy import text
from app.db.engine import engine


def bulk_set_status(sior_ids: list[int], status_to: int, package_name: str = "DASORP_TEST") -> None:
    plsql = text(f"begin {package_name}.MANAGE.set_status(:sior_id, :status); end;")

    with engine.begin() as conn:
        for sior_id in sior_ids:
            conn.execute(plsql, {
                "sior_id": sior_id,
                "status": status_to
            })