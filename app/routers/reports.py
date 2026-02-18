from fastapi import FastAPI, Depends, Request, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user_optional
from app.db.engine import get_db
from app.db.models import ApprovedRefund, Person
from app.config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    refunds = db.query(ApprovedRefund).all()

    return templates.TemplateResponse(
        "reports/reports_so.html",
        {"request": request, "refunds": refunds, "user": user}
    )

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
