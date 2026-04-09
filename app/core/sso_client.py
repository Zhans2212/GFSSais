
import requests
from app.config import settings
from app.utils.logger import log


def sso_login(username: str, password: str, ip_addr: str):
    resp = requests.post(
        f"{settings.SSO_SERVER}/login",
        json={
            "login_name": username,
            "password": password,
            "ip_addr": ip_addr
        }
    )
    return resp


def sso_check(ip_addr: str, username: str | None = None):
    req_json = {"ip_addr": ip_addr}

    if username:
        req_json["login_name"] = username

    resp = requests.post(
        f"{settings.SSO_SERVER}/check",
        json=req_json
    )
    return resp


def sso_logout(ip_addr: str):
    resp = requests.post(
        f"{settings.SSO_SERVER}/close",
        json={"ip_addr": ip_addr}
    )
    return resp
