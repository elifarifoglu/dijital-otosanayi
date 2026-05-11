from fastapi import APIRouter, Depends
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
