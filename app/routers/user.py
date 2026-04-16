from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import templates
from app.core.security import login_required
from app.utils.logger import log

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(login_required)):

    if not user:
        log.warning("Unauthorized access to GET /, redirecting to /login")
        return RedirectResponse("/login", status_code=303)

    log.info("User %s requested the profile page", user.username)
    return templates.TemplateResponse(
        "pages/profile.html",
        {"request": request, "user": user}
    )