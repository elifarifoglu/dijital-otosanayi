from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BusinessResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    address: str
    phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
