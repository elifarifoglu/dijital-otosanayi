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


class OwnerWorkOrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None = None
    customer_email: str | None = None
    vehicle_id: int
    vehicle_plate: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    business_id: int
    business_name: str | None = None
    service_type: str
    price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OwnerCustomerOptionResponse(BaseModel):
    id: int
    full_name: str | None = None
    email: str
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OwnerCustomerVehicleOptionResponse(BaseModel):
    id: int
    owner_id: int
    plate: str
    make: str
    model: str
    year: int

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


class WorkOrderAveragePriceResponse(BaseModel):
    service_type: str
    average_price: Decimal | None
    work_order_count: int