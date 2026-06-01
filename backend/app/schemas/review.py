from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    workorder_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: str

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Yorum boş olamaz")
        return cleaned


class ReviewResponse(BaseModel):
    id: int
    workorder_id: int
    customer_id: int
    business_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    service_type: Optional[str] = None
    workorder_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewableWorkOrderResponse(BaseModel):
    workorder_id: int
    service_type: str
    description: Optional[str] = None
    status: str
