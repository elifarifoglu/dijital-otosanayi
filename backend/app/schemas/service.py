from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


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