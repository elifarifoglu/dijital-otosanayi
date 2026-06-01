from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import require_roles
from app.db import get_db
from app.models.business import Business
from app.models.review import Review
from app.models.user import User
from app.models.workorder import WorkOrder
from app.schemas.business import BusinessResponse, BusinessDetailResponse
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    """
    Sistemde kayıtlı işletmeleri listeler.
    """
    businesses = db.query(Business).all()
    return businesses


@router.get("/{business_id}", response_model=BusinessDetailResponse)
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

    average_rating, review_count = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(Review.business_id == business_id).one()

    return {
        "id": business.id,
        "owner_id": business.owner_id,
        "name": business.name,
        "description": business.description,
        "address": business.address,
        "phone": business.phone,
        "created_at": business.created_at,
        "average_rating": float(average_rating) if average_rating is not None else None,
        "review_count": review_count,
    }


@router.get("/{business_id}/reviews", response_model=list[ReviewResponse])
def list_business_reviews(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı"
        )

    reviews = db.query(Review).filter(Review.business_id == business_id).order_by(Review.created_at.desc()).all()
    return reviews


@router.post("/{business_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review_for_business(
    business_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("customer")),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı"
        )

    workorder = db.query(WorkOrder).filter(WorkOrder.id == review_data.workorder_id).first()
    if not workorder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İş emri bulunamadı"
        )

    if workorder.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu iş emrine yorum yapma yetkiniz yok"
        )

    if workorder.business_id != business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İş emri bu işletmeye ait değil"
        )

    new_review = Review(
        workorder_id=review_data.workorder_id,
        customer_id=current_user.id,
        business_id=business_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(new_review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        error_text = str(exc.orig).lower()
        if "unique" in error_text and "workorder" in error_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu iş emri için zaten yorum yapılmış."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yorum oluşturulamadı"
        )

    db.refresh(new_review)
    return new_review
