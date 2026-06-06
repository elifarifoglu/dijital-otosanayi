from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkOrderCreate(BaseModel):
    customer_id: int
    vehicle_id: int
    business_id: int
    service_type: str
    price: Decimal = Field(..., ge=0)

    @field_validator("service_type")
    @classmethod
    def validate_service_type(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Servis tipi bos olamaz")
        return cleaned


class WorkOrderCreateResponse(BaseModel):
    id: int
    customer_id: int
    vehicle_id: int
    business_id: int
    service_type: str
    price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderStatusUpdate(BaseModel):
    status: str


class MyWorkOrderResponse(BaseModel):
    id: int
    business_id: int
    business_name: str
    vehicle_id: int
    vehicle_plate: str
    vehicle_model: str
    service_type: str
    price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)