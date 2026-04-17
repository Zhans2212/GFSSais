from fastapi import HTTPException
from sqlalchemy import text
from app.db.engine import engine


def bulk_accept_all(typ: str, post: str, fio: str, package_name: str = "DASORP_TEST") -> None:
    empt = None

    if typ == "all":
        code = empt
        type_payer = empt
    elif typ == "sz":
        code = empt
        type_payer = "СЗ"
    elif typ == "so":
        code = "СО"
        type_payer = empt
    elif typ == "ep":
        code = "ЕП"
        type_payer = empt
    else:
        raise HTTPException(status_code=400, detail="Invalid type")

    query = text(
        f"BEGIN {package_name}.MANAGE.APPROVE_ALL(:code, :type_payer, :post, :fio); END;"
    )

    with engine.begin() as conn:
        conn.execute(query, {
            "code": code,
            "type_payer": type_payer,
            "post": post,
            "fio": fio
        })