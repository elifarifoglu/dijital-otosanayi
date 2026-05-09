from fastapi import Header, HTTPException, status, Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.models.user import User


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT token'dan current user'ı al.
    
    - Authorization: Bearer <token> header'ını kontrol eder
    - Token doğrulaması yapar
    - Kullanıcıyı DB'den bulur
    - is_active kontrolü yapar
    """
    
    # Token kontrolü
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token eksik",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Bearer token parse etme
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token formatı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token doğrulaması
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kullanıcı kontrolü
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Aktif olma kontrolü
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı hesabı devre dışı bırakılmıştır"
        )
    
    return user


def require_roles(*allowed_roles: str):
    """Re-usable role kontrol dependency'si."""
    
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlemi yapmak için yetkiniz yok"
            )
        return current_user

    return role_dependency
