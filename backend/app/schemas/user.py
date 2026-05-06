from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Yeni kullanıcı oluşturma şeması."""
    email: EmailStr
    password: str
    full_name: str
    role: str = "customer"


class UserResponse(BaseModel):
    """Kullanıcı response şeması (password_hash içermez)."""
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
