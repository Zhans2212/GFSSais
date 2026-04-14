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
from app.utils.no_cache import no_cache

router = APIRouter()

class AcceptAllRequest(BaseModel):
    sior_ids: List[int]

TODAY = datetime.today().strftime("%d.%m.%Y")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(login_required)):
    log.info("GET /reports requested by user=%s", user.masked_name)

    return no_cache(
        templates.TemplateResponse(
            "pages/reports.html",
            {"request": request, "user": user}
        )
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

@router.get("/order-data")
async def get_order_data(
    date: str,
    user=Depends(login_required)
):
    user_name = user.masked_name

    if user.top_control != 1 and user.top_control != 2:
        log.warning(
            "Forbidden GET /reports/order-data by user=%s, top_control=%s",
            user_name,
            user.top_control
        )
        raise HTTPException(status_code=403, detail="Forbidden to GET /reports/order-data")

    if date == '':
        log.warning("Empty date to GET /order-data by user=%s", user_name)
        raise HTTPException(status_code=400, detail="Bad request")

    log.info("GET /reports/order-data requested by user=%s, date=%s", user_name, date)

    if not user:
        log.warning("Unauthorized access to GET /reports/order-data")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        person = get_who_approved(PACKAGE_NAME)
        log.info("PERSON WHO APPROVED = %s", person.get("fio"))
        rows = get_order_rows(date, PACKAGE_NAME)

        data = {
            "026": {
                "label": "026 ТТК б-ша ӘА",
                "count": 0,
                "amount": 0.0,
            },
            "094_penalty": {
                "label": "094 ТТК б-ша ӘА өсімпұлы",
                "count": 0,
                "amount": 0.0,
            },
            "094_bt": {
                "label": "БТ",
                "count": 0,
                "amount": 0.0,
            },
            "026_sz": {
                "label": "СЗ_026",
                "count": 0,
                "amount": 0.0,
            },
            "094_sz": {
                "label": "СЗ_094",
                "count": 0,
                "amount": 0.0,
            },
        }

        for amount, count, knp, typ in rows:
            amount_value = float(amount or 0)
            count_value = int(count or 0)
            knp_value = str(knp or "").zfill(3)
            typ_value = str(typ or "").strip()

            if typ_value == "СЗ" and knp_value == "026":
                data["026_sz"]["count"] = count_value
                data["026_sz"]["amount"] = amount_value

            elif typ_value == "СЗ" and knp_value == "094":
                data["094_sz"]["count"] = count_value
                data["094_sz"]["amount"] = amount_value

            elif knp_value == "026":
                data["026"]["count"] = count_value
                data["026"]["amount"] = amount_value

            elif knp_value == "094" and typ is None:
                data["094_penalty"]["count"] = count_value
                data["094_penalty"]["amount"] = amount_value

            elif knp_value == "094" and str(typ) == "О":
                data["094_bt"]["count"] = count_value
                data["094_bt"]["amount"] = amount_value

        table_rows = [
            {
                "ttk": "026",
                "total_count": data["026"]["count"] + data["026_sz"]["count"],
                "total_amount": data["026"]["amount"] + data["026_sz"]["amount"],
                "part_026_count": data["026"]["count"],
                "part_026_amount": data["026"]["amount"],
                "part_094_count": 0,
                "part_094_amount": 0.0,
                "part_bt_count": 0,
                "part_bt_amount": 0.0,
                "part_sz_count": data["026_sz"]["count"],
                "part_sz_amount": data["026_sz"]["amount"],
            },
            {
                "ttk": "094",
                "total_count": data["094_penalty"]["count"] + data["094_bt"]["count"] + data["094_sz"]["count"],
                "total_amount": data["094_penalty"]["amount"] + data["094_bt"]["amount"] + data["094_sz"]["amount"],
                "part_026_count": 0,
                "part_026_amount": 0.0,
                "part_094_count": data["094_penalty"]["count"],
                "part_094_amount": data["094_penalty"]["amount"],
                "part_bt_count": data["094_bt"]["count"],
                "part_bt_amount": data["094_bt"]["amount"],
                "part_sz_count": data["094_sz"]["count"],
                "part_sz_amount": data["094_sz"]["amount"],
            },
        ]

        total_row = {
            "ttk": "Барлығы",
            "total_count": sum(r["total_count"] for r in table_rows),
            "total_amount": sum(r["total_amount"] for r in table_rows),
            "part_026_count": sum(r["part_026_count"] for r in table_rows),
            "part_026_amount": sum(r["part_026_amount"] for r in table_rows),
            "part_094_count": sum(r["part_094_count"] for r in table_rows),
            "part_094_amount": sum(r["part_094_amount"] for r in table_rows),
            "part_bt_count": sum(r["part_bt_count"] for r in table_rows),
            "part_bt_amount": sum(r["part_bt_amount"] for r in table_rows),
            "part_sz_count": sum(r["part_sz_count"] for r in table_rows),
            "part_sz_amount": sum(r["part_sz_amount"] for r in table_rows),
        }

        return {
            "date": date,
            "rows": table_rows,
            "total": total_row,
        }

    except Exception:
        log.exception(
            "Failed to build order report data for user=%s, date=%s",
            user_name,
            date
        )
        raise HTTPException(status_code=500, detail="Ошибка при формировании данных отчета")


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
async def accept_all(request: Request, user=Depends(login_required)):
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
        bulk_accept_all(user.post, user.masked_name, package_name=PACKAGE_NAME)

        log.info(
            "Bulk status update completed successfully by user=%s",
            user_name
        )

        return {
            "ok": True
        }

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