# app/models.py
from enum import Enum
from pydantic import BaseModel

class DataType(str, Enum):
    TOTAL = "total"
    DAILY = "daily"
    TIME = "time"
    GENDER = "gender"
    AGE = "age"

class SalesResponse(BaseModel):
    status: str
    message: str
    data: dict