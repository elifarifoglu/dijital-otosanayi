from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models.user import User
from app.models.workorder import WorkOrder, WorkOrderStatus
from app.schemas.workorder import MyWorkOrderResponse

router = APIRouter(prefix="/my", tags=["my"])


def _to_api_status(status_value) -> str:
    value = status_value.value if hasattr(status_value, "value") else str(status_value)
    if value == WorkOrderStatus.ready_for_delivery.value:
        return "ready"
    return value


@router.get("/work-orders", response_model=list[MyWorkOrderResponse])
def list_my_work_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("customer")),
):
    workorders = (
        db.query(WorkOrder)
        .filter(WorkOrder.customer_id == current_user.id)
        .order_by(WorkOrder.created_at.desc())
        .all()
    )

    return [
        {
            "id": wo.id,
            "business_id": wo.business_id,
            "business_name": wo.business.name,
            "vehicle_id": wo.vehicle_id,
            "vehicle_plate": wo.vehicle.plate,
            "vehicle_model": wo.vehicle.model,
            "service_type": wo.service_type,
            "price": wo.estimated_price,
            "status": _to_api_status(wo.status),
            "created_at": wo.created_at,
            "updated_at": wo.updated_at,
        }
        for wo in workorders
    ]
