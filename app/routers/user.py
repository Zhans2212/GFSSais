from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import templates
from app.core.security import get_current_user_optional
from app.utils.logger import log
from app.utils.masker import mask_user_name
from app.utils.no_cache import no_cache

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_optional(request)
    user_name = mask_user_name(user)

    if not user:
        log.warning("Unauthorized access to GET /, redirecting to /login")
        return RedirectResponse("/login", status_code=303)

    log.info("User %s requested the profile page", user_name)
    return no_cache(templates.TemplateResponse(
        "pages/profile.html",
        {"request": request, "user": user}
    ))