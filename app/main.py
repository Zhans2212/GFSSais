from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import setup_static, hostname, port, settings
from app.routers import reports, auth, user

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

class AuthRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # login/logout и api пропускаем
        if (
            request.url.path in ("/login", "/logout")
            or request.url.path.startswith("/api")
            or request.url.path.startswith("/static")
        ):
            return await call_next(request)

        response = await call_next(request)

        if response.status_code == HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=303)

        return response


def create_app() -> FastAPI:
    app = FastAPI()

    # Сессии нужны для request.session
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
    )

    app.add_middleware(AuthRedirectMiddleware)
    @app.middleware("http")
    async def add_no_cache_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    # Роутеры
    app.include_router(reports.router, prefix="/reports", tags=["Reports"])
    app.include_router(auth.router, prefix="/login", tags=["Login"])
    app.include_router(user.router, prefix="/profile", tags=["User"])

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return RedirectResponse(url="/reports", status_code=303)

    return app


app = create_app()
app.mount("/static", StaticFiles(directory="app/static"), name="static")