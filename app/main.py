from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import setup_static, templates
from app.db.engine import get_db
from app.routers import reports
from app.routers import auth
from app.routers import users

app = FastAPI()

setup_static(app)

app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(auth.router, prefix="/login", tags=["Login"])
app.include_router(users.router)
