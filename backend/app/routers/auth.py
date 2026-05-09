from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError

from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.auth import hash_password, authenticate_user, create_access_token
from app.dependencies import get_current_user, require_roles

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


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Kullanıcı girişi ve JWT token oluştur.
    
    - Email ve password ile doğrulama
    - İnaktif kullanıcılar giriş yapamaz
    """
    
    # Kullanıcıyı doğrula
    user = authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre yanlış",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Aktif kullanıcı kontrolü
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kullanıcı hesabı devre dışı bırakılmıştır"
        )
    
    # Token oluştur
    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    )
    
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Mevcut kullanıcı bilgisini al.
    
    - JWT token ile doğrulama gerekir
    - Token'daki sub (user_id) değerinden kullanıcı bulunur
    """
    return current_user


@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_roles("admin"))):
    return {"message": "Admin erişimi başarılı", "user": current_user.email}


@router.get("/business-owner-only")
def business_owner_only(current_user: User = Depends(require_roles("business_owner"))):
    return {"message": "Business owner erişimi başarılı", "user": current_user.email}


@router.get("/customer-only")
def customer_only(current_user: User = Depends(require_roles("customer"))):
    return {"message": "Customer erişimi başarılı", "user": current_user.email}
