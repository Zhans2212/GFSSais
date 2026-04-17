from datetime import datetime
from typing import List

from fastapi import Depends, Request, APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.config import templates, PACKAGE_NAME
from app.core.security import login_required
from app.db.get_tables import get_refund_list, get_persons_by_sior, get_order_rows, get_who_approved
from app.db.update_tables import bulk_accept_all
from app.utils.get_excel_418 import rows_to_excel, rows_to_pdf
from app.utils.logger import log
from app.utils.order_report_418 import build_order_report

router = APIRouter()

class AcceptAllRequest(BaseModel):
    sior_ids: List[int]

TODAY = datetime.today().strftime("%d.%m.%Y")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(login_required)):
    log.info("GET /reports requested by user=%s", user.masked_name)

    return templates.TemplateResponse(
        "pages/reports.html",
        {"request": request, "user": user}
    )


@router.get("/data")
async def get_reports_data(
    status: int = Query(default=2),
    user=Depends(login_required)
):
    user_name = user.masked_name

    if user.top_control != 1 and user.top_control != 2:
        log.warning(
            "Forbidden GET /reports/data by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to GET /reports/data")

    log.info("GET /reports/data requested by user=%s, status=%s", user_name, status)

    try:
        refunds = get_refund_list(status, package_name=PACKAGE_NAME)
        # refunds = json.loads(json.dumps(refunds, default=float))

        log.info(
            "Sending refunds: count=%s, sample=%s",
            len(refunds),
            refunds[:2] if refunds else "EMPTY"
        )

        return {
            "rows": refunds,
            "status": status,
            "count": len(refunds),
        }
    except Exception:
        log.exception(
            "Failed to load refunds data for user=%s, status=%s",
            user_name,
            status
        )
        raise HTTPException(status_code=500, detail="Ошибка при загрузке данных")


@router.get("/access-to-approve")
async def check_role(user=Depends(login_required)):
    log.info("GET /access-to-approve requested by user=%s", user.masked_name)

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    log.info("The result of /access-to-approve for user=%s with top_control %s: %s",
             user.masked_name, user.top_control, user.top_control == 2)
    return user.top_control == 2

@router.get("/order-data")
async def get_order_data(date: str, user=Depends(login_required)):
    user_name = user.masked_name

    if user.top_control not in (1, 2):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not date:
        raise HTTPException(status_code=400, detail="Bad request")

    try:
        rows = get_order_rows(date, PACKAGE_NAME)

        log.info("Got rows = %s", rows)

        result = build_order_report(rows)

        return {
            "date": date,
            **result
        }

    except Exception:
        log.exception("Failed report user=%s date=%s", user_name, date)
        raise HTTPException(status_code=500, detail="Ошибка формирования отчета")


@router.get("/persons")
async def get_person(
    sior_id: int,
    user=Depends(login_required)
):
    user_name = user.masked_name

    if user.top_control != 1 and user.top_control != 2:
        log.warning(
            "Forbidden GET /reports/persons by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to GET /reports/persons")

    log.info("GET /reports/data requested by user=%s, sior_id=%s", user_name, sior_id)

    try:
        persons = get_persons_by_sior(sior_id, package_name=PACKAGE_NAME)
        log.info(
            "Sending persons: count=%s, sample=%s",
            len(persons),
            persons[:2] if persons else "EMPTY"
        )

        return {
            "rows": persons,
            "sior_id": sior_id,
            "count": len(persons),
        }
    except Exception:
        log.exception(
            "Failed to load refunds data for user=%s, sior_id=%s",
            user_name,
            sior_id
        )
        raise HTTPException(status_code=500, detail="Ошибка при загрузке данных")


@router.post("/accept_all")
async def accept_all(request: Request, typ: str = Query(), user=Depends(login_required)):
    user_name = user.masked_name

    log.info("POST /accept_all requested by user=%s", user_name)

    if not user:
        log.warning("Unauthorized access to POST /accept_all")
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user.top_control != 2:
        log.warning(
            "Forbidden bulk accept attempt by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to accept all")

    try:
        filter_map = ["all", "ep", "so", "sz"]

        if typ not in filter_map:
            raise HTTPException(status_code=400, detail="Invalid type")

        log.info("TYPE OF REPORTS APPROVED: " + typ)

        bulk_accept_all(
            typ,
            user.post,
            user.masked_name,
            package_name=PACKAGE_NAME
        )

        return {"ok": True}

    except Exception:
        log.exception(
            "Bulk status update failed by user=%s",
            user_name
        )
        raise HTTPException(status_code=500, detail="Ошибка при массовом согласовании")


@router.get("/get_report_excel")
async def get_report_excel(
    request: Request,
    date: str,
    user=Depends(login_required)
):

    user_name = user.masked_name

    log.info("GET /get_report_excel requested, date=%s", date)

    if not user:
        log.warning("Unauthorized access to GET /get_report_excel")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log.info("Excel generation started by user=%s, date=%s", user_name, date)

    try:
        approved_by = get_who_approved(PACKAGE_NAME)
        rows = get_order_rows(date, PACKAGE_NAME)

        log.info(
            "Excel source data loaded successfully for user=%s, date=%s, rows_count=%s",
            user_name,
            date,
            len(rows)
        )

        excel_file = rows_to_excel(rows, TODAY, user.fio, approved_by)

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

@router.get("/get_report_pdf")
async def get_report_pdf(
    request: Request,
    date: str = Query(default=datetime.today().strftime("%d.%m.%Y")),
    user=Depends(login_required)
):

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    approved_by = get_who_approved(PACKAGE_NAME)
    rows = get_order_rows(date, PACKAGE_NAME)
    pdf_file = rows_to_pdf(rows, TODAY, user.fio, approved_by)

    safe_date = date.replace(".", "_")

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{safe_date}.pdf"'
        }
    )