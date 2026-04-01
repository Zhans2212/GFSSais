from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.config import templates
from app.core.security import login_required
from app.core.sso_client import sso_login, sso_logout
from app.models.user_model import USER
from app.utils.logger import log
from app.utils.masker import mask_username, mask_ip
from app.utils.no_cache import no_cache

router = APIRouter()

class LoginRequest(BaseModel):
    username: str = Field(validation_alias="username")
    password: str


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # user = login_required(request)
    log.info("GET /login requested")

    # if user:
    #     log.info("Authorized user already has session, redirecting to /reports, user=%s", user.masked_name)
    #     return RedirectResponse("/reports", status_code=303)

    log.info("Login page rendered")
    return no_cache(
        templates.TemplateResponse(
            "pages/login.html",
            {"request": request}
        )
    )

@router.post("/auth")
async def login(payload: LoginRequest, request: Request):
    ip = request.client.host if request.client else ""
    masked_ip = mask_ip(ip)
    masked_username = mask_username(payload.username)

    log.info("POST /auth requested, username=%s, ip=%s", masked_username, masked_ip)

    try:
        resp = sso_login(payload.username, payload.password, ip)
    except Exception:
        log.exception(
            "SSO login request failed, username=%s, ip=%s",
            masked_username,
            masked_ip
        )
        raise HTTPException(status_code=500, detail="Ошибка авторизации")

    if resp.status_code != 200:
        log.error(
            "SSO returned non-200 HTTP status, username=%s, ip=%s, sso_status=%s",
            masked_username,
            masked_ip,
            resp.status_code
        )
        raise HTTPException(status_code=500, detail="SSO error")

    try:
        resp_json = resp.json()
    except Exception:
        log.exception(
            "Failed to parse SSO response JSON, username=%s, ip=%s",
            masked_username,
            masked_ip
        )
        raise HTTPException(status_code=500, detail="Ошибка обработки ответа авторизации")

    if resp_json.get("status") != 200:
        log.warning(
            "Authentication failed: wrong credentials or access denied, username=%s, ip=%s, sso_status=%s",
            masked_username,
            masked_ip,
            resp_json.get("status")
        )
        raise HTTPException(status_code=401, detail="Wrong credentials")

    resp_json = resp.json()
    if resp_json.get("status") != 200:
        log.info(
            f"LOGIN_PAGE. POST. USER {payload.username} not registered"
        )
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {"request": request,
             "user": None,
             "info": "Неверна Фамилия (или ИИН) или пароль",
             },
        )

    # JSON получили
    json_user = resp_json["user"]
    log.info(f"LOGIN POST. json_user: {json_user}")

    try:
        user = USER().authenticate_and_init(json_user, request)
    except Exception:
        log.exception(
            "Failed to build user from SSO response, username=%s, ip=%s",
            masked_username,
            masked_ip
        )
        raise HTTPException(status_code=500, detail="Ошибка формирования профиля пользователя")

    log.info(
        "User authenticated successfully, username=%s, user=%s, ip=%s",
        masked_username,
        masked_ip
    )

    response = RedirectResponse(url="/login", status_code=303)
    return response



@router.post("/logout")
async def logout(request: Request):
    ip = request.client.host if request.client else ""
    masked_ip = mask_ip(ip)

    current_user = request.state.user if hasattr(request.state, "user") else None
    user_name = str(current_user.fio or "authorized_user") if current_user else "anonymous"

    log.info("POST /logout requested, user=%s, ip=%s", user_name, masked_ip)
    # session = request.session
    # request.session.clear()

    try:
        sso_logout(ip)
        log.info("SSO logout completed, user=%s, ip=%s", user_name, masked_ip)
    except Exception:
        log.exception("SSO logout failed, user=%s, ip=%s", user_name, masked_ip)

    response = RedirectResponse(url="/login", status_code=303)
    return response