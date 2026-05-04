from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date

class FilterParams(BaseModel):
    date_from: Optional[date] = None
    sior_id: Optional[int] = None
    refer_in: Optional[str] = None
