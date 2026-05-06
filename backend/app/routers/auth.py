from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError

from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.auth import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Yeni kullanıcı kaydı.
    
    - Email benzersiz olmalı
    - Password hash'lenerek kaydedilir
    - Varsayılan role: customer
    """
    
    # Email formatını doğrula
    try:
        validate_email(user_data.email)
    except EmailNotValidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz email formatı"
        )
    
    # Email daha önce kayıtlıysa hata
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı"
        )
    
    # Role enum doğrulaması
    try:
        role = UserRole[user_data.role]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geçersiz role. Seçenekler: {', '.join([r.value for r in UserRole])}"
        )
    
    # Yeni kullanıcı oluştur
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
