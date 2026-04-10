from sqlalchemy import text
from app.db.engine import engine


def bulk_accept_all(package_name: str = "DASORP_TEST") -> None:
    query = text(
        f"BEGIN {package_name}.MANAGE.ACCEPT_ALL(:post); END;"
    )

    with engine.begin() as conn:
        conn.execute(query, {
            "package_name": package_name
        })