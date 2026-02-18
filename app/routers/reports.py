from fastapi import FastAPI, Depends, Request, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.engine import get_db
from app.db.models import ApprovedRefund, Person
from app.config import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    refunds = db.query(ApprovedRefund).all()

    return templates.TemplateResponse(
        "reports/reports_so.html",
        {"request": request, "refunds": refunds}
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
