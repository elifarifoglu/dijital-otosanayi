from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceCatalogItemResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BusinessServiceItemResponse(BaseModel):
    business_id: int
    service_id: int
    service_name: str
    service_description: str | None = None
    minimum_price: Decimal


class ServicePriceComparisonResponse(BaseModel):
    service_id: int
    service_name: str
    business_id: int
    business_name: str
    business_minimum_price: Decimal
    market_average_price: Decimal
    business_count: int
    difference_amount: Decimal
    difference_percentage: Decimal
    market_position: Literal["below_market", "at_market", "above_market"]


class BusinessServiceCreate(BaseModel):
    service_id: int = Field(..., gt=0)
    minimum_price: Decimal = Field(..., gt=0)


class BusinessServiceUpdate(BaseModel):
    minimum_price: Decimal | None = Field(default=None, gt=0)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_not_empty(self):
        if self.minimum_price is None and self.is_active is None:
            raise ValueError("En az bir alan gonderilmelidir")
        return self


class BusinessServiceManagementResponse(BaseModel):
    business_id: int
    service_id: int
    service_name: str
    minimum_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime