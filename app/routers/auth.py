from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.config import templates
from app.core.sso_client import sso_login, sso_logout
from app.core.security import create_access_token, get_current_user_optional
from app.core.security import build_user_from_sso
from app.utils.logger import log
from app.utils.masker import mask_username, mask_ip
from app.utils.no_cache import no_cache

router = APIRouter()

class LoginRequest(BaseModel):
    # Accept both: {"username": "..."} and {"login_name": "..."}
    username: str = Field(validation_alias="username")
    password: str


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    log.info("GET /login requested")

    user = get_current_user_optional(request)
    if user:
        user_name = str(user.get("fio") or user.get("sub") or "authorized_user")
        log.info("Authorized user already has session, redirecting to /reports, user=%s", user_name)
        return RedirectResponse("/reports", status_code=303)

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

    try:
        user = build_user_from_sso(resp_json["user"])
    except Exception:
        log.exception(
            "Failed to build user from SSO response, username=%s, ip=%s",
            masked_username,
            masked_ip
        )
        raise HTTPException(status_code=500, detail="Ошибка формирования профиля пользователя")

    try:
        access_token = create_access_token(
            data={
                "sub": user.username,
                "roles": user.roles,
                "top_control": user.top_control,
                "fio": user.fio,
                "dep_name": user.dep_name,
                "post": user.post
            }
        )
    except Exception:
        log.exception(
            "Failed to create access token, username=%s, ip=%s, user=%s",
            masked_username,
            masked_ip
        )
        raise HTTPException(status_code=500, detail="Ошибка создания токена доступа")

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # True если будет HTTPS
        max_age=8 * 60 * 60,
    )

    log.info(
        "User authenticated successfully, username=%s, user=%s, ip=%s",
        masked_username,
        masked_ip
    )

    return response



@router.post("/logout")
async def logout(request: Request):
    ip = request.client.host if request.client else ""
    masked_ip = mask_ip(ip)

    current_user = get_current_user_optional(request)
    user_name = str(current_user.get("fio") or current_user.get("sub") or "authorized_user") if current_user else "anonymous"

    log.info("POST /logout requested, user=%s, ip=%s", user_name, masked_ip)

    try:
        sso_logout(ip)
        log.info("SSO logout completed, user=%s, ip=%s", user_name, masked_ip)
    except Exception:
        log.exception("SSO logout failed, user=%s, ip=%s", user_name, masked_ip)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")

    log.info("Local session cookie deleted, user=%s, ip=%s", user_name, masked_ip)
    return response