import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class WorkOrderStatus(str, enum.Enum):
    received = "received"
    inspection = "inspection"
    repair = "repair"
    ready_for_delivery = "ready_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class WorkOrder(Base):
    __tablename__ = "workorders"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    estimated_price = Column(Numeric(10, 2), nullable=False)
    actual_price = Column(Numeric(10, 2), nullable=True)
    status = Column(Enum(WorkOrderStatus, name="workorder_status"), nullable=False, default=WorkOrderStatus.received)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vehicle = relationship("Vehicle", back_populates="workorders")
    business = relationship("Business", back_populates="workorders")
    customer = relationship("User", back_populates="workorders")
