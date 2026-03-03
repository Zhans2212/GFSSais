from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import setup_static
from app.routers import reports
from app.routers import auth
from app.routers import user

app = FastAPI()

setup_static(app)

app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(auth.router, prefix="/login", tags=["Login"])
app.include_router(user.router, prefix="/profile", tags=["User"])

@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse("/reports", status_code=303)