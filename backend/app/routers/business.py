from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.business import Business
from app.schemas.business import BusinessResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    """
    Sistemde kayıtlı işletmeleri listeler.
    """
    businesses = db.query(Business).all()
    return businesses


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(business_id: int, db: Session = Depends(get_db)):
    """
    Verilen ID'ye sahip işletmeyi döndürür.
    
    - İşletme bulunamazsa 404 Not Found döner
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı"
        )
    return business
