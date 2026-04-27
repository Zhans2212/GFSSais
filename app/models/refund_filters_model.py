from pydantic import BaseModel
from typing import Optional
from datetime import date

class FilterParams(BaseModel):
    sior_id: Optional[int] = None
    refer_in: Optional[str] = None