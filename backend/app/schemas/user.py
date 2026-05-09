from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Yeni kullanıcı oluşturma şeması."""
    email: EmailStr
    password: str
    full_name: str
    role: str = "customer"


class UserLogin(BaseModel):
    """Kullanıcı giriş şeması."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response şeması."""
    access_token: str
    token_type: str = "bearer"


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
