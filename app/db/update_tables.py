from fastapi import HTTPException
from sqlalchemy import text

from app.config import PACKAGE_NAME
from app.db.engine import engine


def bulk_accept_all(typ: str, post: str, fio: str) -> None:
    empt = None

    match typ:
        case "all":
            code = empt
            type_payer = empt
        case "sz":
            code = empt
            type_payer = "СЗ"
        case "so":
            code = "СО"
            type_payer = empt
        case "ep":
            code = "ЕП"
            type_payer = empt
        case _:
            raise HTTPException(status_code=400, detail="Invalid type")

    if code is None and type_payer is None:
        query = text(
            f"BEGIN {PACKAGE_NAME}.MANAGE.APPROVE_ALL(:post, :fio); END;"
        )

        with engine.begin() as conn:
            conn.execute(query, {
                "post": post,
                "fio": fio
            })
    else:
        query = text(
            f"BEGIN {PACKAGE_NAME}.MANAGE.APPROVE_ALL(:code, :type_payer, :post, :fio); END;"
        )

        with engine.begin() as conn:
            conn.execute(query, {
                "code": code,
                "type_payer": type_payer,
                "post": post,
                "fio": fio
            })