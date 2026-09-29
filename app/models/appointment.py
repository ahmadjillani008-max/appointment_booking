"""
Appointment model — a user's booking of a slot.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # unique=True guarantees one slot can only ever have one appointment.
    slot_id = Column(Integer, ForeignKey("slots.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(String, nullable=False, default="confirmed")  # confirmed | completed | cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="appointments")
    slot = relationship("Slot", back_populates="appointment")
    history = relationship("AppointmentHistory", back_populates="appointment", cascade="all, delete-orphan")