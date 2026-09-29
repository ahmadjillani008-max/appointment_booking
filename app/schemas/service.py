"""
Service schemas — create, update, and response shapes.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    """Body for POST /services."""

    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(..., gt=0, le=1440)   # 1 min .. 24h
    price: Decimal = Field(..., ge=0)


class ServiceUpdate(BaseModel):
    """Body for PATCH /services/{id}. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    price: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ServiceOut(BaseModel):
    """Service returned in responses."""

    id: int
    provider_id: int
    name: str
    description: str | None
    duration_minutes: int
    price: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}