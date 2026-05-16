from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# === Pydantic схемы ===
class UserCreate(BaseModel):
    name: str
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    login: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    login: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
