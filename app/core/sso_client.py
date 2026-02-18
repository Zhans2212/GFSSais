import requests
from app.config import settings


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


def sso_check(ip_addr: str):
    resp = requests.post(
        f"{settings.SSO_SERVER}/check",
        json={"ip_addr": ip_addr}
    )
    return resp


def sso_logout(ip_addr: str):
    resp = requests.post(
        f"{settings.SSO_SERVER}/close",
        json={"ip_addr": ip_addr}
    )
    return resp
