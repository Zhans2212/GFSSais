from fastapi import HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED

import requests

from app.config import settings
from app.core.sso_client import sso_check
from app.models.user_model import USER
from app.utils.logger import log


def check_login(request: Request):
    ip = request.client.host if request.client else ""
    resp = sso_check(ip)

    log.info(f"LOGIN CHECK → {resp}")

    if resp.status_code != 200:
        return None

    resp_json = resp.json()
    log.info(f"LOGIN GET. resp_json: {resp_json}")

    if resp_json.get("status") != 200:
        log.info(f"Try auto login → USER {ip} not registered")
        return None

    json_user = resp_json["user"]
    log.info(f"LOGIN GET. json_user: {json_user}")
    return json_user


def try_auto_login(request: Request, json_user):
    ip = request.client.host if request.client else ""
    user = USER().authenticate_and_init(json_user, request)

    if not user:
        log.info("Try auto login → user object empty")
        request.state.user = None
        return False

    request.state.user = user

    log.info(f"SUCCESS. Try auto login → USER IP {ip}: {request.session}")
    return True


def login_required(request: Request):
    json_user = check_login(request)
    if not json_user:
        log.info(f'---> login_required. user out of session')
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    # if "username" not in session or 'roles' not in session:
    session = request.session

    if "username" not in session or 'roles' not in session:
        log.info(f'---> login_required. USERNAME not in SESSION: {session}')
        status = try_auto_login(request, json_user)
        if not status:
            log.info(f'---> login_required. try_auto_login: {status}')
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    user = USER().restore_user(request)
    if not user:
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    request.state.user = user
    return request.state.user