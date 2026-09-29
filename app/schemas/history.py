"""
AppointmentHistory schemas.
"""

from datetime import datetime
from pydantic import BaseModel


class HistoryOut(BaseModel):
    """One history row."""

    id: int
    appointment_id: int
    action: str
    old_value: str | None
    new_value: str | None
    changed_by: int | None
    timestamp: datetime

    model_config = {"from_attributes": True}