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
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewableWorkOrderResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    """
    Sistemde kayıtlı işletmeleri listeler.
    """
    review_stats_subquery = (
        db.query(
            Review.business_id.label("business_id"),
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.business_id)
        .subquery()
    )

    businesses_with_stats = (
        db.query(
            Business,
            review_stats_subquery.c.average_rating,
            review_stats_subquery.c.review_count,
        )
        .outerjoin(review_stats_subquery, review_stats_subquery.c.business_id == Business.id)
        .all()
    )

    return [
        {
            "id": business.id,
            "owner_id": business.owner_id,
            "name": business.name,
            "description": business.description,
            "address": business.address,
            "phone": business.phone,
            "created_at": business.created_at,
            "average_rating": float(average_rating) if average_rating is not None else None,
            "review_count": int(review_count or 0),
        }
        for business, average_rating, review_count in businesses_with_stats
    ]


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

    reviews = db.query(Review, WorkOrder).join(WorkOrder, WorkOrder.id == Review.workorder_id).filter(
        Review.business_id == business_id
    ).order_by(Review.created_at.desc()).all()

    return [
        {
            "id": review.id,
            "workorder_id": review.workorder_id,
            "customer_id": review.customer_id,
            "business_id": review.business_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "service_type": workorder.service_type,
            "workorder_description": workorder.description,
        }
        for review, workorder in reviews
    ]


@router.get("/{business_id}/my-reviewable-workorders", response_model=list[ReviewableWorkOrderResponse])
def list_my_reviewable_workorders(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("customer")),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı"
        )

    workorders = db.query(WorkOrder).outerjoin(Review, Review.workorder_id == WorkOrder.id).filter(
        WorkOrder.business_id == business_id,
        WorkOrder.customer_id == current_user.id,
        Review.id.is_(None),
    ).order_by(WorkOrder.created_at.desc()).all()

    return [
        {
            "workorder_id": workorder.id,
            "service_type": workorder.service_type,
            "description": workorder.description,
            "status": workorder.status.value if hasattr(workorder.status, "value") else str(workorder.status),
        }
        for workorder in workorders
    ]


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
