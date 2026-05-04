from datetime import datetime
from typing import List

from fastapi import Depends, Request, APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.config import templates
from app.core.security import login_required
from app.db.get_tables import get_refunds, get_persons_by_sior, get_418_rows, get_who_approved, get_refunds_list, \
    get_refunds_by_filter
from app.db.update_tables import bulk_accept_all
from app.models.refund_filters_model import FilterParams
from app.utils.get_excel_418 import rows_to_excel, rows_to_pdf
from app.utils.logger import log

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
    status: int = Query(),
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
        refunds = get_refunds(status)

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

@router.post("/data1c")
async def get_reports_data(
    filters: FilterParams,
    status: int = Query(),
    user=Depends(login_required)
):
    user_name = user.masked_name

    if user.top_control != 1 and user.top_control != 2:
        log.warning(
            "Forbidden POST /reports/data1c by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to POST /reports/data1c")

    log.info("POST /reports/data1c requested by user=%s, status=%s", user_name, status)

    try:
        log.info("FILTERS: %s", filters)
        refunds = get_refunds_by_filter(**filters.model_dump(exclude_none=True))

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
            "Failed to load refunds data1c for user=%s, status=%s",
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

@router.get("/418-data")
async def get_418_data(user=Depends(login_required)):
    user_name = user.masked_name

    if user.top_control not in (1, 2):
        log.warning(
            "Forbidden GET /reports/418-data by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to GET /reports/418-data")

    log.info("GET /reports/418-data requested by user=%s", user_name)

    try:
        order = get_418_rows()

        log.info(
            "Sending order 418: count=%s, sample=%s",
            len(order),
            order[:2] if order else "EMPTY"
        )

        return {
            "rows": order,
            "count": len(order),
        }

    except Exception:
        log.exception(
            "Failed to load order 418 for user=%s",
            user_name,
        )
        raise HTTPException(status_code=500, detail="Ошибка при загрузке данных")


@router.get("/persons")
async def get_person(
    status: int = Query(),
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

    log.info("GET /reports/persons requested by user=%s, status=%s", user_name, status)

    try:
        persons = get_refunds_list(status)
        log.info(
            "Sending persons: count=%s, sample=%s",
            len(persons),
            persons[:2] if persons else "EMPTY"
        )

        return {
            "rows": persons,
            "status": status,
            "count": len(persons),
        }
    except Exception:
        log.exception(
            "Failed to load refunds data for user=%s, status=%s",
            user_name,
            status
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
            user.masked_name
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
    user=Depends(login_required)
):

    user_name = user.masked_name

    log.info("GET /get_report_excel requested by user=%s", user_name)

    if not user:
        log.warning("Unauthorized access to GET /get_report_excel")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log.info("Excel generation started by user=%s", user_name)

    try:
        approved_by = get_who_approved()
        rows = get_418_rows()

        log.info(
            "Excel source data loaded successfully for user=%s, rows_count=%s",
            user_name,
            len(rows)
        )

        excel_file = rows_to_excel(rows, TODAY, user.fio, approved_by)

        log.info(
            "Excel file created successfully for user=%s, rows_count=%s",
            user_name,
            len(rows)
        )

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="report_{TODAY}.xlsx"'}
        )

    except Exception:
        log.exception(
            "Failed to generate excel report for user=%s",
            user_name,
        )
        raise HTTPException(status_code=500, detail="Ошибка при формировании Excel-отчета")

@router.get("/get_report_pdf")
async def get_report_pdf(
    request: Request,
    user=Depends(login_required)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    approved_by = get_who_approved()
    rows = get_418_rows()
    pdf_file = rows_to_pdf(rows, TODAY, user.fio, approved_by)

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{TODAY}.pdf"'
        }
    )