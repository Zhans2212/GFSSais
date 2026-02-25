from fastapi import FastAPI, Depends, Request, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from pydantic import BaseModel
from typing import List

from app.core.security import get_current_user_optional
from app.db.engine import get_db
from app.db.models import ApprovedRefund, Person
from app.config import templates
from app.utils.no_cache import no_cache

router = APIRouter()


class AcceptAllRequest(BaseModel):
    sior_ids: List[int]

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    refunds = db.query(ApprovedRefund).all()

    return no_cache(templates.TemplateResponse(
        "pages/reports.html",
        {"request": request, "refunds": refunds, "user": user}
    ))

@router.get("/person/{iin}")
async def get_person(iin: str, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.iin == iin).first()

    if not person:
        return None

    return {
        "iin": person.iin,
        "lastname": person.lastname,
        "firstname": person.firstname,
        "middlename": person.middlename,
        "birthdate": person.birthdate.strftime("%d.%m.%Y") if person.birthdate else "",
        "address": person.address
    }

@router.post("/accept_all")
async def accept_all(payload: AcceptAllRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sior_ids = [int(x) for x in payload.sior_ids if x is not None]
    if not sior_ids:
        return {"ok": True, "requested": 0, "called": 0}

    status_to = user.get("top_control") + 1

    plsql = text("begin DASORP_TEST.appl.set_status(:sior_id, :status); end;")

    try:
        called = 0
        for sior_id in sior_ids:
            db.execute(plsql, {"sior_id": sior_id, "status": status_to})
            called += 1

        db.commit()
        return {"ok": True, "requested": len(sior_ids), "called": called, "status_to": status_to}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="DB error")