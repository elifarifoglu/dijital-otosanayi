from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.dependencies import require_roles
from app.models.business import Business
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.workorder import WorkOrder, WorkOrderStatus
from app.schemas.workorder import (
    OwnerCustomerOptionResponse,
    OwnerCustomerVehicleOptionResponse,
    OwnerWorkOrderResponse,
    WorkOrderAveragePriceResponse,
    WorkOrderCreate,
    WorkOrderCreateResponse,
    WorkOrderStatusUpdate,
)

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

API_STATUS_TO_MODEL_STATUS = {
    "received": WorkOrderStatus.received,
    "inspection": WorkOrderStatus.inspection,
    "repair": WorkOrderStatus.repair,
    "ready": WorkOrderStatus.ready_for_delivery,
    "delivered": WorkOrderStatus.delivered,
}


def to_api_status(status_value: WorkOrderStatus | str) -> str:
    value = status_value.value if hasattr(status_value, "value") else str(status_value)
    if value == WorkOrderStatus.ready_for_delivery.value:
        return "ready"
    return value


@router.get("/my-business/customers", response_model=list[OwnerCustomerOptionResponse])
def list_active_customer_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    _ = current_user

    customers = (
        db.query(User)
        .filter(
            User.role == UserRole.customer,
            User.is_active.is_(True),
        )
        .order_by(
            func.coalesce(func.nullif(User.full_name, ""), User.email),
            User.id.asc(),
        )
        .all()
    )

    return [
        {
            "id": customer.id,
            "full_name": customer.full_name,
            "email": customer.email,
            "phone": customer.phone,
        }
        for customer in customers
    ]


@router.get(
    "/my-business/customers/{customer_id}/vehicles",
    response_model=list[OwnerCustomerVehicleOptionResponse],
)
def list_customer_vehicle_options(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    _ = current_user

    customer = (
        db.query(User)
        .filter(
            User.id == customer_id,
            User.role == UserRole.customer,
            User.is_active.is_(True),
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Müşteri bulunamadı",
        )

    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.owner_id == customer_id)
        .order_by(Vehicle.plate.asc(), Vehicle.id.asc())
        .all()
    )

    return [
        {
            "id": vehicle.id,
            "owner_id": vehicle.owner_id,
            "plate": vehicle.plate,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
        }
        for vehicle in vehicles
    ]


@router.get("/my-business", response_model=list[OwnerWorkOrderResponse])
def list_my_business_work_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    workorders = (
        db.query(WorkOrder)
        .join(Business, WorkOrder.business_id == Business.id)
        .options(
            joinedload(WorkOrder.customer),
            joinedload(WorkOrder.vehicle),
            joinedload(WorkOrder.business),
        )
        .filter(Business.owner_id == current_user.id)
        .order_by(WorkOrder.created_at.desc())
        .all()
    )

    return [
        {
            "id": wo.id,
            "customer_id": wo.customer_id,
            "customer_name": wo.customer.full_name if wo.customer else None,
            "customer_email": wo.customer.email if wo.customer else None,
            "vehicle_id": wo.vehicle_id,
            "vehicle_plate": wo.vehicle.plate if wo.vehicle else None,
            "vehicle_make": wo.vehicle.make if wo.vehicle else None,
            "vehicle_model": wo.vehicle.model if wo.vehicle else None,
            "business_id": wo.business_id,
            "business_name": wo.business.name if wo.business else None,
            "service_type": wo.service_type,
            "price": wo.estimated_price,
            "status": to_api_status(wo.status),
            "created_at": wo.created_at,
            "updated_at": wo.updated_at,
        }
        for wo in workorders
    ]


@router.get("/average-price", response_model=WorkOrderAveragePriceResponse)
def get_average_price_by_service_type(
    service_type: str,
    db: Session = Depends(get_db),
):
    normalized_input = service_type.strip().lower()
    if not normalized_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="service_type bos veya sadece bosluk olamaz",
        )

    average_price, work_order_count = db.query(
        func.avg(WorkOrder.estimated_price),
        func.count(WorkOrder.id),
    ).filter(
        func.lower(func.trim(WorkOrder.service_type)) == normalized_input
    ).one()

    return {
        "service_type": service_type.strip(),
        "average_price": float(average_price) if average_price is not None else None,
        "work_order_count": int(work_order_count),
    }


@router.post("", response_model=WorkOrderCreateResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(
    work_order_data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    business = db.query(Business).filter(Business.id == work_order_data.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Isletme bulunamadi",
        )

    if business.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu isletme icin is emri olusturma yetkiniz yok",
        )

    customer = db.query(User).filter(User.id == work_order_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Musteri bulunamadi",
        )

    if customer.role != UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_id musteri rolundeki bir kullaniciya ait olmali",
        )

    vehicle = db.query(Vehicle).filter(Vehicle.id == work_order_data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arac bulunamadi",
        )

    if vehicle.owner_id != work_order_data.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arac secilen musteriye ait degil",
        )

    default_description = f"{work_order_data.service_type} islemi icin olusturulan is emri"

    new_workorder = WorkOrder(
        customer_id=work_order_data.customer_id,
        vehicle_id=work_order_data.vehicle_id,
        business_id=work_order_data.business_id,
        service_type=work_order_data.service_type,
        description=default_description,
        estimated_price=work_order_data.price,
    )

    db.add(new_workorder)
    db.commit()
    db.refresh(new_workorder)

    return {
        "id": new_workorder.id,
        "customer_id": new_workorder.customer_id,
        "vehicle_id": new_workorder.vehicle_id,
        "business_id": new_workorder.business_id,
        "service_type": new_workorder.service_type,
        "price": new_workorder.estimated_price,
        "status": to_api_status(new_workorder.status),
        "created_at": new_workorder.created_at,
        "updated_at": new_workorder.updated_at,
    }


@router.patch("/{work_order_id}/status", response_model=WorkOrderCreateResponse)
def update_work_order_status(
    work_order_id: int,
    status_data: WorkOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("business_owner")),
):
    workorder = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not workorder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Is emri bulunamadi",
        )

    business = db.query(Business).filter(Business.id == workorder.business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Is emrine bagli isletme bulunamadi",
        )

    if business.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu is emrinin durumunu guncelleme yetkiniz yok",
        )

    requested_status = status_data.status.strip().lower()
    mapped_status = API_STATUS_TO_MODEL_STATUS.get(requested_status)
    if mapped_status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gecersiz status. Kabul edilen degerler: received, inspection, repair, ready, delivered",
        )

    workorder.status = mapped_status
    db.commit()
    db.refresh(workorder)

    return {
        "id": workorder.id,
        "customer_id": workorder.customer_id,
        "vehicle_id": workorder.vehicle_id,
        "business_id": workorder.business_id,
        "service_type": workorder.service_type,
        "price": workorder.estimated_price,
        "status": to_api_status(workorder.status),
        "created_at": workorder.created_at,
        "updated_at": workorder.updated_at,
    }