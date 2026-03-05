from datetime import datetime

from fastapi import FastAPI, Depends, Request, APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import oracledb

from pydantic import BaseModel
from typing import List

from starlette.responses import StreamingResponse

from app.core.security import get_current_user_optional
from app.db.engine import engine
from app.db.models import ApprovedRefund, Person
from app.config import templates
from app.utils.get_excel_418 import rows_to_excel
from app.utils.no_cache import no_cache

router = APIRouter()


class AcceptAllRequest(BaseModel):
    sior_ids: List[int]

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    refund_date = "05.12.2024"

    query = text("SELECT DASORP_TEST.MANAGE.GET_REFUND_LIST(:date) FROM DUAL")

    with engine.connect() as conn:
        result = conn.execute(query, {"date": refund_date})
        row = result.fetchone()

        refunds = []

        if row and row[0]:
            cursor = row[0]

            columns = [col[0].lower() for col in cursor.description]
            refunds = [dict(zip(columns, r)) for r in cursor.fetchall()]

            cursor.close()

    return no_cache(templates.TemplateResponse(
        "pages/reports.html",
        {"request": request, "refunds": refunds, "user": user}
    ))

@router.get("/person/{iin}")
async def get_person(iin: str):

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
        row = result.fetchone()

    if not row:
        return None

    birthdate = row[4]
    if birthdate:
        birthdate = birthdate.strftime("%d.%m.%Y")

    return {
        "iin": row[0],
        "lastname": row[1],
        "firstname": row[2],
        "middlename": row[3],
        "birthdate": birthdate or "",
        "address": row[5]
    }

@router.post("/accept_all")
async def accept_all(payload: AcceptAllRequest, request: Request):

    user = get_current_user_optional(request)

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user.get("top_control") == "4":
        raise HTTPException(status_code=403, detail="Forbidden to accept all")

    sior_ids = [int(x) for x in payload.sior_ids if x]
    if not sior_ids:
        return {"ok": True, "requested": 0, "called": 0}

    status_to = int(user.get("top_control")) + 1

    plsql = text("begin DASORP_TEST.MANAGE.set_status(:sior_id, :status); end;")

    try:
        with engine.begin() as conn:
            for sior_id in sior_ids:
                conn.execute(plsql, {
                    "sior_id": sior_id,
                    "status": status_to
                })

        print(f"Status to {status_to} for {len(sior_ids)} sior_ids")
        return {
            "ok": True,
            "requested": len(sior_ids),
            "called": len(sior_ids),
            "status_to": status_to
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report418")
async def get_report418(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    refund_date = "05.12.2024"

    return no_cache(templates.TemplateResponse(
        "pages/report418.html",
        {"request": request, "user": user}
    ))


@router.get("/get_report_excel")
async def get_report_excel(request: Request, date: str = Query(default=datetime.today().strftime('%d.%m.%Y'))):
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = text("SELECT DASORP.MANAGE.GET_ORDER(:date) FROM DUAL")

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"date": date})
            row = result.fetchone()

            rows = []
            if row and row[0]:
                cursor = row[0]
                rows = cursor.fetchall()
                cursor.close()

        excel_file = rows_to_excel(
            rows,
            headers=["Column1", "Column2", "Column3", "Column4"]
        )

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="report_{date}.xlsx"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))