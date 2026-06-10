from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# === Pydantic схемы ===
class UserCreate(BaseModel):
    name: str
    login: str
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    login: str
    password: str = Field(..., min_length=1, description="Пароль не может быть пустым")

class UserOut(BaseModel):
    id: int
    name: str
    login: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)