from fastapi import Request
from app.utils.roles import manager_posts, viewer_deps
from app.utils.logger import log


SECURITY_KEYS = {
    "username",
    "fio",
    "full_name",
    "dep_name",
    "post",
    "roles",
    "top_control",
    "rfbn_id",
}


class USER:
    """
    FastAPI-совместимый объект пользователя.
    Не использует Flask session, не использует g.
    Все данные передаются извне.
    """

    def __init__(self):
        self.username = None
        self.src_user = None
        self.post = ""
        self.dep_name = ""
        self.roles = ""
        self.top_control = 0
        self.rfbn_id = ""
        self.fio = ""
        self.full_name = ""
        self.ip_addr = ""

    def restore_user(self, request: Request):
        session=request.session

        self.username = session.get("username", None)
        if "username" not in session:
            log.info(f"RESTORE_USER. USERNAME not in SESSION: {session}")
            return None

        self.fio = session.get("fio", "")
        self.full_name = session.get("full_name", "")
        self.dep_name = session.get("dep_name", "")
        self.post = session.get("post", "")
        self.roles = session.get("roles", "")
        self.top_control = session.get("top_control", 4)
        self.rfbn_id = session.get("rfbn_id", "")
        self.ip_addr = session.get("ip_addr", "")
        self.full_name = session.get("fio", "")
        return self

    def authenticate_and_init(self, src_user: dict, request):
        ip = request.client.host if request.client else ""
        self.src_user = src_user

        if not src_user or "login_name" not in src_user:
            log.info(f"SSO FAIL. USERNAME: {src_user}, ip_addr: {ip}")
            return None

        log.debug(f"SSO_USER. src_user: {src_user}")

        self.username = src_user["login_name"]

        # Проверка обязательных полей
        required = ["fio", "dep_name", "post"]
        for field in required:
            if field not in src_user:
                log.info(f"SSO FAIL. USER {self.username}: missing {field}")
                return None

        # Основные поля
        self.rfbn_id = src_user.get("rfbn_id", "")
        self.dep_name = src_user.get("dep_name", "")
        self.post = src_user.get("post", "")
        self.fio = src_user.get("fio", "")
        self.full_name = self.fio
        self.ip_addr = ip

        # Определение ролей
        self._assign_roles()

        # Сохраним в контексте
        self.save_context(request)

        log.info(
            f"---> SSO SUCCESS\n"
            f"\tUSERNAME: {self.username}\n"
            f"\tIP_ADDR: {self.ip_addr}\n"
            f"\tFIO: {self.fio}\n"
            f"\tROLES: {self.roles}\n"
            f"\tPOST: {self.post}\n"
            f"\tTOP_LEVEL: {self.top_control}\n"
            f"\tRFBN: {self.rfbn_id}\n"
            f"\tDEP_NAME: {self.dep_name}\n<---"
        )

        return self

    def save_context(self, request):
        session = request.session
        # удалить только security‑контекст
        for key in SECURITY_KEYS:
            session.pop(key, None)

        session["username"] = self.username
        session["fio"] = self.fio
        session["full_name"] = self.full_name
        session["dep_name"] = self.dep_name
        session["post"] = self.post
        session["roles"] = self.roles
        session["top_control"] = self.top_control
        session["rfbn_id"] = self.rfbn_id
        session["ip_addr"] = self.ip_addr

    def _assign_roles(self):
        """
        top_control:
        - 1 -> управляющий директор
        - 0 -> остальные
        """
        if self.post in manager_posts:
            self.top_control = 2
        elif self.dep_name in viewer_deps:
            self.top_control = 1
        else:
            self.top_control = 0

    def is_authenticated(self):
        log.info(f'Check is_authenticated {self.username}')
        return bool(self.roles)

    def have_role(self, role_name):
        return role_name == self.roles

    @property
    def masked_name(self) -> str:
        if not self.fio:
            return "unknown_user"

        fio = str(self.fio).strip()
        if not fio:
            return "unknown_user"

        parts = fio.split()
        if len(parts) == 1:
            return parts[0]

        last_name = parts[0]
        initials = "".join(f"{p[0]}." for p in parts[1:] if p)
        return f"{last_name} {initials}".strip()
