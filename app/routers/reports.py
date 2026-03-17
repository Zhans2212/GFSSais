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
from app.db.get_tables import get_refund_list, get_person_by_iin, get_order_rows
from app.config import templates, PACKAGE_NAME
from app.db.update_tables import bulk_set_status
from app.utils.get_excel_418 import rows_to_excel
from app.utils.logger import log
from app.utils.masker import mask_user_name, mask_iin, mask_ids
from app.utils.no_cache import no_cache

router = APIRouter()

class AcceptAllRequest(BaseModel):
    sior_ids: List[int]

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_optional(request)
    user_name = mask_user_name(user)

    log.info("GET / requested")

    if not user:
        log.warning("Unauthorized access to GET /, redirecting to /login")
        return RedirectResponse("/login", status_code=303)

    refund_date = "05.12.2024"
    log.info("User %s requested refunds list for date=%s", user_name, refund_date)

    try:
        refunds = get_refund_list(refund_date, package_name=PACKAGE_NAME)

        log.info(
            "Refunds list loaded successfully for user=%s, records_count=%s, date=%s",
            user_name,
            len(refunds),
            refund_date
        )

    except Exception:
        log.exception(
            "Failed to load refunds list for user=%s, date=%s",
            user_name,
            refund_date
        )
        raise HTTPException(status_code=500, detail="Ошибка при загрузке списка")

    return no_cache(
        templates.TemplateResponse(
            "pages/reports.html",
            {"request": request, "refunds": refunds, "user": user}
        )
    )


@router.get("/person/{iin}")
async def get_person(iin: str):
    masked_iin = mask_iin(iin)
    log.info("GET /person requested for iin=%s", masked_iin)

    try:
        row = get_person_by_iin(iin)
    except Exception:
        log.exception("Failed to get person by iin=%s", masked_iin)
        raise HTTPException(status_code=500, detail="Ошибка при получении данных физического лица")

    if not row:
        log.warning("Person not found for iin=%s", masked_iin)
        return None

    birthdate = row[4].strftime("%d.%m.%Y") if row[4] else ""

    log.info("Person found successfully for iin=%s", masked_iin)

    return {
        "iin": row[0],
        "lastname": row[1],
        "firstname": row[2],
        "middlename": row[3],
        "birthdate": birthdate,
        "address": row[5]
    }


@router.post("/accept_all")
async def accept_all(payload: AcceptAllRequest, request: Request):
    user = get_current_user_optional(request)
    user_name = mask_user_name(user)

    log.info("POST /accept_all requested by user=%s", user_name)

    if not user:
        log.warning("Unauthorized access to POST /accept_all")
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_top_control = user.get("top_control")

    if user_top_control == "4":
        log.warning(
            "Forbidden bulk accept attempt by user=%s, top_control=%s",
            user_name,
            user_top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to accept all")

    sior_ids = [int(x) for x in payload.sior_ids if x]
    if not sior_ids:
        log.info("Empty sior_ids received in POST /accept_all by user=%s", user_name)
        return {"ok": True, "requested": 0, "called": 0}

    try:
        status_to = int(user_top_control) + 1
    except (TypeError, ValueError):
        log.warning(
            "Invalid top_control for bulk accept, user=%s, top_control=%s",
            user_name,
            user_top_control
        )
        raise HTTPException(status_code=400, detail="Некорректный уровень согласования")

    log.info(
        "Bulk status update started by user=%s, status_to=%s, sior_ids=%s",
        user_name,
        status_to,
        mask_ids(sior_ids)
    )

    try:
        bulk_set_status(sior_ids, status_to, package_name=PACKAGE_NAME)

        log.info(
            "Bulk status update completed successfully by user=%s, status_to=%s, count=%s",
            user_name,
            status_to,
            len(sior_ids)
        )

        return {
            "ok": True,
            "requested": len(sior_ids),
            "called": len(sior_ids),
            "status_to": status_to
        }

    except Exception:
        log.exception(
            "Bulk status update failed by user=%s, status_to=%s, sior_ids=%s",
            user_name,
            status_to,
            mask_ids(sior_ids)
        )
        raise HTTPException(status_code=500, detail="Ошибка при массовом согласовании")


@router.get("/report418")
async def get_report418(request: Request):
    user = get_current_user_optional(request)
    user_name = mask_user_name(user)

    log.info("GET /report418 requested")

    if not user:
        log.warning("Unauthorized access to GET /report418, redirecting to /login")
        return RedirectResponse("/login", status_code=303)

    log.info("User %s opened report418 page", user_name)

    return no_cache(
        templates.TemplateResponse(
            "pages/report418.html",
            {"request": request, "user": user}
        )
    )


@router.get("/get_report_excel")
async def get_report_excel(
    request: Request,
    date: str = Query(default=datetime.today().strftime("%d.%m.%Y"))
):
    user = get_current_user_optional(request)
    user_name = mask_user_name(user)

    log.info("GET /get_report_excel requested, date=%s", date)

    if not user:
        log.warning("Unauthorized access to GET /get_report_excel")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log.info("Excel generation started by user=%s, date=%s", user_name, date)

    try:
        rows = get_order_rows(date)

        log.info(
            "Excel source data loaded successfully for user=%s, date=%s, rows_count=%s",
            user_name,
            date,
            len(rows)
        )

        excel_file = rows_to_excel(rows, date, user.get("fio"))

        log.info(
            "Excel file created successfully for user=%s, date=%s, rows_count=%s",
            user_name,
            date,
            len(rows)
        )

        safe_date = date.replace(".", "_")

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="report_{safe_date}.xlsx"'}
        )

    except Exception:
        log.exception(
            "Failed to generate excel report for user=%s, date=%s",
            user_name,
            date
        )
        raise HTTPException(status_code=500, detail="Ошибка при формировании Excel-отчета")