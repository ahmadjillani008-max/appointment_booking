"""
Slot schemas — create, response, and availability filter shapes.
"""

from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class SlotCreate(BaseModel):
    """Body for POST /services/{service_id}/slots."""

    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def check_times(self):
        """Enforce start_time < end_time."""
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class SlotOut(BaseModel):
    """Slot returned in responses."""

    id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    is_booked: bool
    created_at: datetime

    model_config = {"from_attributes": True}