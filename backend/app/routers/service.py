from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.business import Business
from app.models.business_service import BusinessService
from app.models.service import Service
from app.schemas.service import (
    BusinessServiceItemResponse,
    ServiceCatalogItemResponse,
    ServicePriceComparisonResponse,
)

router = APIRouter(tags=["services"])

MARKET_TOLERANCE = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


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