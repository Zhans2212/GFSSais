from datetime import datetime

from fastapi import FastAPI, Depends, Request, APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from decimal import Decimal

from pydantic import BaseModel
from typing import List

from starlette.responses import StreamingResponse

from app.core.security import login_required
from app.db.get_tables import get_refund_list, get_persons_by_sior, get_order_rows
from app.config import templates, PACKAGE_NAME
from app.db.update_tables import bulk_set_status
from app.utils.get_excel_418 import rows_to_excel, rows_to_pdf
from app.utils.logger import log
from app.utils.masker import mask_iin, mask_ids
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
    date: str = Query(default=datetime.today().strftime("%d.%m.%Y")),
    user=Depends(login_required)
):
    user_name = user.masked_name
    log.info("GET /reports/order-data requested by user=%s, date=%s", user_name, date)

    if not user:
        log.warning("Unauthorized access to GET /reports/order-data")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        rows = get_order_rows(date)

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
        }

        for amount, count, knp, typ in rows:
            amount_value = float(amount or 0)
            count_value = int(count or 0)
            knp_value = str(knp or "").zfill(3)

            if knp_value == "026":
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
                "total_count": data["026"]["count"],
                "total_amount": data["026"]["amount"],
                "part_026_count": data["026"]["count"],
                "part_026_amount": data["026"]["amount"],
                "part_094_count": 0,
                "part_094_amount": 0.0,
                "part_bt_count": 0,
                "part_bt_amount": 0.0,
            },
            {
                "ttk": "094",
                "total_count": data["094_penalty"]["count"] + data["094_bt"]["count"],
                "total_amount": data["094_penalty"]["amount"] + data["094_bt"]["amount"],
                "part_026_count": 0,
                "part_026_amount": 0.0,
                "part_094_count": data["094_penalty"]["count"],
                "part_094_amount": data["094_penalty"]["amount"],
                "part_bt_count": data["094_bt"]["count"],
                "part_bt_amount": data["094_bt"]["amount"],
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
async def accept_all(payload: AcceptAllRequest, request: Request, user=Depends(login_required)):
    user_name = user.masked_name

    log.info("POST /accept_all requested by user=%s", user_name)

    if not user:
        log.warning("Unauthorized access to POST /accept_all")
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_top_control = user.top_control

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


@router.get("/get_report_excel")
async def get_report_excel(
    request: Request,
    date: str = Query(default=datetime.today().strftime("%d.%m.%Y")),
    user=Depends(login_required)
):

    user_name = user.masked_name

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

        excel_file = rows_to_excel(rows, TODAY, user.fio)

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

    rows = get_order_rows(date)
    pdf_file = rows_to_pdf(rows, TODAY, user.fio)

    safe_date = date.replace(".", "_")

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{safe_date}.pdf"'
        }
    )