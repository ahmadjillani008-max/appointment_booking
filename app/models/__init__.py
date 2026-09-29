"""
Imports every model so Alembic autogenerate can detect all tables.
"""

from app.models.user import User
from app.models.service import Service
from app.models.slot import Slot
from app.models.appointment import Appointment
from app.models.history import AppointmentHistory

__all__ = ["User", "Service", "Slot", "Appointment", "AppointmentHistory"]