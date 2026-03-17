from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import setup_static, hostname, port
from app.routers import reports
from app.routers import auth
from app.routers import user
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    app = FastAPI(
        title="My API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Роутеры
    app.include_router(reports.router, prefix="/reports", tags=["Reports"])
    app.include_router(auth.router, prefix="/login", tags=["Login"])
    app.include_router(user.router, prefix="/profile", tags=["User"])

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return RedirectResponse("/reports", status_code=303)

    return app


app = create_app()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

