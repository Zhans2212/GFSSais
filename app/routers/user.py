from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import templates
from app.core.security import get_current_user_optional

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    print(user)
    return templates.TemplateResponse(
        "pages/profile.html",
        {"request": request, "user": user}
    )