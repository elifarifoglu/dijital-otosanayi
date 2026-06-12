from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.business import Business
from app.models.business_service import BusinessService
from app.models.service import Service
from app.models.user import User
from app.schemas.service import (
    BusinessServiceCreate,
    BusinessServiceItemResponse,
    BusinessServiceManagementResponse,
    BusinessServiceUpdate,
    ServiceCatalogItemResponse,
    ServicePriceComparisonResponse,
)

router = APIRouter(tags=["services"])

MARKET_TOLERANCE = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


def get_active_business_or_404(db: Session, business_id: int) -> Business:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business or not business.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı",
        )
    return business


def ensure_business_owner_or_403(business: Business, current_user: User) -> None:
    if business.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işletme için işlem yapma yetkiniz yok",
        )


def get_active_service_or_404(db: Session, service_id: int) -> Service:
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.is_active.is_(True))
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı",
        )
    return service


def to_management_response(
    offering: BusinessService,
    service_name: str,
) -> dict:
    return {
        "business_id": offering.business_id,
        "service_id": offering.service_id,
        "service_name": service_name,
        "minimum_price": offering.minimum_price,
        "is_active": offering.is_active,
        "created_at": offering.created_at,
        "updated_at": offering.updated_at,
    }


@router.get("/services", response_model=list[ServiceCatalogItemResponse])
def list_active_services(db: Session = Depends(get_db)):
    services = (
        db.query(Service)
        .filter(Service.is_active.is_(True))
        .order_by(Service.name.asc(), Service.id.asc())
        .all()
    )
    return services


@router.get(
    "/businesses/{business_id}/services",
    response_model=list[BusinessServiceItemResponse],
)
def list_business_services(
    business_id: int,
    db: Session = Depends(get_db),
):
    business = (
        db.query(Business)
        .filter(
            Business.id == business_id,
            Business.is_active.is_(True),
        )
        .first()
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı",
        )

    offerings = (
        db.query(BusinessService, Service)
        .join(Service, Service.id == BusinessService.service_id)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.is_active.is_(True),
            Service.is_active.is_(True),
            BusinessService.minimum_price > 0,
        )
        .order_by(Service.name.asc(), Service.id.asc())
        .all()
    )

    return [
        {
            "business_id": offering.business_id,
            "service_id": service.id,
            "service_name": service.name,
            "service_description": service.description,
            "minimum_price": offering.minimum_price,
        }
        for offering, service in offerings
    ]


@router.get(
    "/businesses/{business_id}/services/{service_id}/price-comparison",
    response_model=ServicePriceComparisonResponse,
)
def compare_business_service_price(
    business_id: int,
    service_id: int,
    db: Session = Depends(get_db),
):
    business = (
        db.query(Business)
        .filter(
            Business.id == business_id,
            Business.is_active.is_(True),
        )
        .first()
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme bulunamadı",
        )

    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.is_active.is_(True),
        )
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı",
        )

    business_offering = (
        db.query(BusinessService)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.service_id == service_id,
            BusinessService.is_active.is_(True),
            BusinessService.minimum_price > 0,
        )
        .first()
    )
    if not business_offering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu işletme seçilen hizmeti sunmuyor",
        )

    market_average_price, business_count = (
        db.query(
            func.avg(BusinessService.minimum_price),
            func.count(BusinessService.id),
        )
        .join(Business, Business.id == BusinessService.business_id)
        .join(Service, Service.id == BusinessService.service_id)
        .filter(
            BusinessService.service_id == service_id,
            BusinessService.is_active.is_(True),
            BusinessService.minimum_price > 0,
            Business.is_active.is_(True),
            Service.is_active.is_(True),
        )
        .one()
    )

    if market_average_price is None or business_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu hizmet için fiyat karşılaştırma verisi bulunamadı",
        )

    business_minimum_price = business_offering.minimum_price
    difference_amount = business_minimum_price - market_average_price
    difference_percentage = (difference_amount / market_average_price) * ONE_HUNDRED

    if difference_amount < -MARKET_TOLERANCE:
        market_position = "below_market"
    elif difference_amount > MARKET_TOLERANCE:
        market_position = "above_market"
    else:
        market_position = "at_market"

    return {
        "service_id": service.id,
        "service_name": service.name,
        "business_id": business.id,
        "business_name": business.name,
        "business_minimum_price": business_minimum_price,
        "market_average_price": market_average_price,
        "business_count": int(business_count),
        "difference_amount": difference_amount,
        "difference_percentage": difference_percentage,
        "market_position": market_position,
    }


@router.post(
    "/businesses/{business_id}/services",
    response_model=BusinessServiceManagementResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_service_to_business(
    business_id: int,
    payload: BusinessServiceCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    business = get_active_business_or_404(db, business_id)
    ensure_business_owner_or_403(business, current_user)
    service = get_active_service_or_404(db, payload.service_id)

    existing = (
        db.query(BusinessService)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.service_id == payload.service_id,
        )
        .first()
    )

    if existing and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu hizmet işletmeye zaten eklenmiş",
        )

    if existing and not existing.is_active:
        existing.is_active = True
        existing.minimum_price = payload.minimum_price
        existing.updated_at = datetime.utcnow()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İşletme hizmet kaydı güncellenemedi",
            )

        db.refresh(existing)
        response.status_code = status.HTTP_200_OK
        return to_management_response(existing, service.name)

    new_offering = BusinessService(
        business_id=business_id,
        service_id=payload.service_id,
        minimum_price=payload.minimum_price,
        is_active=True,
    )

    db.add(new_offering)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        error_text = str(exc.orig).lower() if exc.orig else ""
        if "uq_business_services_business_service" in error_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu hizmet işletmeye zaten eklenmiş",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İşletme hizmet kaydı oluşturulamadı",
        )

    db.refresh(new_offering)
    return to_management_response(new_offering, service.name)


@router.patch(
    "/businesses/{business_id}/services/{service_id}",
    response_model=BusinessServiceManagementResponse,
)
def update_business_service(
    business_id: int,
    service_id: int,
    payload: BusinessServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    business = get_active_business_or_404(db, business_id)
    ensure_business_owner_or_403(business, current_user)

    offering = (
        db.query(BusinessService)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.service_id == service_id,
        )
        .first()
    )
    if not offering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme hizmet kaydı bulunamadı",
        )

    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı",
        )

    if payload.is_active is True and not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pasif bir hizmet işletme için aktifleştirilemez",
        )

    if payload.minimum_price is not None:
        offering.minimum_price = payload.minimum_price
    if payload.is_active is not None:
        offering.is_active = payload.is_active

    offering.updated_at = datetime.utcnow()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İşletme hizmet kaydı güncellenemedi",
        )

    db.refresh(offering)
    return to_management_response(offering, service.name)


@router.delete(
    "/businesses/{business_id}/services/{service_id}",
    response_model=BusinessServiceManagementResponse,
)
def soft_delete_business_service(
    business_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    business = get_active_business_or_404(db, business_id)
    ensure_business_owner_or_403(business, current_user)

    offering = (
        db.query(BusinessService)
        .filter(
            BusinessService.business_id == business_id,
            BusinessService.service_id == service_id,
        )
        .first()
    )
    if not offering:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşletme hizmet kaydı bulunamadı",
        )

    service = db.query(Service).filter(Service.id == service_id).first()
    service_name = service.name if service else ""

    if offering.is_active:
        offering.is_active = False
        offering.updated_at = datetime.utcnow()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İşletme hizmet kaydı güncellenemedi",
            )

        db.refresh(offering)

    return to_management_response(offering, service_name)