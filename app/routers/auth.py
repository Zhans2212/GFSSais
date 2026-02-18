from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from app.core.sso_client import sso_login, sso_logout
from app.core.security import create_access_token
from app.core.security import build_user_from_sso

router = APIRouter()

class LoginRequest(BaseModel):
    # Accept both: {"username": "..."} and {"login_name": "..."}
    username: str = Field(validation_alias="username")
    password: str

@router.post("/login")
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

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



@router.post("/logout")
async def logout(request: Request):
    ip = request.client.host
    sso_logout(ip)

    response = JSONResponse(content={"message": "logged out"})
    response.delete_cookie("user")
    return response
