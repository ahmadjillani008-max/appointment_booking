"""
Appointment schemas — create, response, and list shapes.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    """Body for POST /appointments."""

    slot_id: int = Field(..., gt=0)
    notes: str | None = Field(default=None, max_length=500)


class AppointmentOut(BaseModel):
    """Appointment returned in responses."""

    id: int
    user_id: int
    slot_id: int
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    
    
class AppointmentReschedule(BaseModel):
    """Body for PATCH /appointments/{id}/reschedule."""

    new_slot_id: int = Field(..., gt=0)


class AppointmentStatusUpdate(BaseModel):
    """Body for PATCH /appointments/{id}/status."""

    status: str = Field(..., pattern="^(confirmed|completed|cancelled)$")