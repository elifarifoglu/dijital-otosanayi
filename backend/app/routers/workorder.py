from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.business import Business
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.workorder import WorkOrder
from app.schemas.workorder import WorkOrderCreate, WorkOrderCreateResponse

router = APIRouter(prefix="/work-orders", tags=["work-orders"])


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
        "status": new_workorder.status.value if hasattr(new_workorder.status, "value") else str(new_workorder.status),
        "created_at": new_workorder.created_at,
        "updated_at": new_workorder.updated_at,
    }