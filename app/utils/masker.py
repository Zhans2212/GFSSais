from typing import List, Optional

def mask_iin(iin: Optional[str]) -> str:
    if not iin:
        return "UNKNOWN_IIN"
    iin = str(iin).strip()
    if len(iin) <= 4:
        return "*" * len(iin)
    return f"{iin[:2]}******{iin[-2:]}"

def mask_username(username: str) -> str:
    if not username:
        return "unknown_user"

    username = str(username).strip()
    if len(username) <= 2:
        return "*" * len(username)

    if len(username) <= 4:
        return username[0] + "*" * (len(username) - 1)

    return f"{username[:2]}***{username[-1:]}"

def mask_user_name(user: Optional[dict]) -> str:
    if not user:
        return "anonymous"

    fio = str(user.get("fio") or "").strip()
    if not fio:
        return "unknown_user"

    parts = fio.split()
    if len(parts) == 1:
        return parts[0]

    # Пример: Иванов И.П.
    last_name = parts[0]
    initials = "".join(f"{p[0]}." for p in parts[1:] if p)
    return f"{last_name} {initials}".strip()


def mask_ids(ids: List[int], visible: int = 3) -> str:
    if not ids:
        return "[]"
    if len(ids) <= visible:
        return str(ids)
    return f"{ids[:visible]} ... total={len(ids)}"


def mask_ip(ip: str) -> str:
    if not ip:
        return "unknown_ip"

    ip = str(ip).strip()

    if "." in ip:  # IPv4
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"

    if ":" in ip:  # IPv6
        parts = ip.split(":")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}:*:*"

    return "***"