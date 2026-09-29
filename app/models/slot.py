"""
Slot model — bookable time windows for a service.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # A service cannot have two slots starting at the exact same time.
    __table_args__ = (
        UniqueConstraint("service_id", "start_time", name="uq_service_start_time"),
    )

    # Relationships
    service = relationship("Service", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)