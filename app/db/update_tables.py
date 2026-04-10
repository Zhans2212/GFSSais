from sqlalchemy import text
from app.db.engine import engine


def bulk_accept_all(post: str, fio: str, package_name: str = "DASORP_TEST") -> None:
    query = text(
        f"BEGIN {package_name}.MANAGE.APPROVE_ALL(:post, :fio); END;"
    )

    with engine.begin() as conn:
        conn.execute(query, {
            "post": post,
            "fio": fio
        })