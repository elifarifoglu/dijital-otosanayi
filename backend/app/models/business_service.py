from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base


class BusinessService(Base):
    __tablename__ = "business_services"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "service_id",
            name="uq_business_services_business_service",
        ),
        CheckConstraint(
            "minimum_price > 0",
            name="ck_business_services_minimum_price_positive",
        ),
        Index(
            "ix_business_services_business_active",
            "business_id",
            "is_active",
        ),
        Index(
            "ix_business_services_service_active",
            "service_id",
            "is_active",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    minimum_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    business = relationship("Business", back_populates="service_offerings")
    service = relationship("Service", back_populates="business_services")