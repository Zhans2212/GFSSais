from app.models.user import User
from app.utils.roles import first_level, second_level, third_level
from datetime import datetime, timedelta
from jose import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=8)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request):
    token_from_cookie = request.cookies.get("access_token")
    effective_token = token_from_cookie or request.headers.get("Authorization", "").split(" ")[-1]

    if not effective_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    print(f"TOKEN: {effective_token}")
    try:
        payload = jwt.decode(effective_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_optional(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None



def build_user_from_sso(src_user: dict) -> User:
    if not all(k in src_user for k in ["login_name", "fio", "dep_name", "post"]):
        raise HTTPException(status_code=403, detail="Invalid SSO data")

    username = src_user["login_name"]
    dep_name = src_user["dep_name"]
    post = src_user["post"]

    roles = []
    top_control = 0

    if post in first_level:
        roles.append("first_level")
        top_control = 0
    elif post in second_level:
        roles.append("second_level")
        top_control = 1
    elif post in third_level:
        roles.append("third_level")
        top_control = 3
    else:
        roles.append("guest")
        top_control = 4
        # raise HTTPException(status_code=403, detail="No role defined")

    return User(
        username=username,
        fio=src_user["fio"],
        dep_name=dep_name,
        post=post,
        rfbn_id=src_user.get("rfbn_id"),
        roles=roles,
        top_control=top_control
    )
