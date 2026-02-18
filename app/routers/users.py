from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def protected(user=Depends(get_current_user)):
    return {"message": "You are authorized", "user": user}
