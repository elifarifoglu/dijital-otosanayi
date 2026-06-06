from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.business import Business
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.workorder import WorkOrder, WorkOrderStatus
from app.schemas.workorder import WorkOrderCreate, WorkOrderCreateResponse, WorkOrderStatusUpdate

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