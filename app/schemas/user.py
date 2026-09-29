"""
User schemas — request bodies and responses for auth routes.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    full_name: str = Field(..., min_length=1, max_length=100)
    # role is optional; defaults to "user". Providers can set "provider" on signup.
    role: str = Field(default="user", pattern="^(user|provider)$")


class UserLogin(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """User info returned in responses (never includes password)."""

    id: int
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Response for POST /auth/login."""

    access_token: str
    token_type: str = "bearer"