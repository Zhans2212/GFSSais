from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import setup_static, templates
from app.db.engine import get_db
from app.routers import reports

app = FastAPI()

setup_static(app)

app.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "reports/login.html",
        {"request": request}
    )
