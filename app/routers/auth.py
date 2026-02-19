from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.config import templates
from app.core.sso_client import sso_login, sso_logout
from app.core.security import create_access_token, get_current_user_optional
from app.core.security import build_user_from_sso
from app.db.engine import get_db

router = APIRouter()

class LoginRequest(BaseModel):
    # Accept both: {"username": "..."} and {"login_name": "..."}
    username: str = Field(validation_alias="username")
    password: str


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse("/reports", status_code=303)

    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request}
    )

@router.post("/auth")
async def login(payload: LoginRequest, request: Request):
    ip = request.client.host
    print(f'/LOGIN. client: {ip}')

    resp = sso_login(payload.username, payload.password, ip)
    print(f'SSO response: {resp.json()}')
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="SSO error")

    resp_json = resp.json()

    if resp_json["status"] != 200:
        raise HTTPException(status_code=401, detail="Wrong credentials")

    user = build_user_from_sso(resp_json["user"])

    access_token = create_access_token(
        data={
            "sub": user.username,
            "roles": user.roles,
            "top_control": user.top_control
        }
    )

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
    return response



@router.post("/logout")
async def logout(request: Request):
    ip = request.client.host
    sso_logout(ip)

    response = JSONResponse(content={"message": "logged out"})
    response.delete_cookie("access_token")
    return response
