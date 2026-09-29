"""
app/config.py
-------------
Central configuration loader.

Purpose
-------
- Reads ALL application settings from the .env file.
- Exposes them through a single `settings` object.
- Contains NO defaults, NO hardcoded values, NO fallback logic.
  Every value must come from .env — if it's missing, the app
  fails fast at startup with a clear error.

Rule
----
No other file in the project reads os.environ or parses .env.
They all import `settings` from here.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Every field is REQUIRED (uses `Field(...)` with no default).
    That way, if `.env` is missing a value, Pydantic raises a
    ValidationError immediately instead of letting the app run
    with a silent wrong default.
    """

    # ---------- App ----------
    APP_NAME: str = Field(..., description="Human-readable app name")
    APP_VERSION: str = Field(..., description="App version string")
    DEBUG: bool = Field(..., description="Debug mode flag")

    # ---------- Database ----------
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL DSN: postgresql://user:pass@host:port/db",
    )

    # ---------- JWT ----------
    # min_length=16 blocks accidental weak keys like "secret".
    JWT_SECRET_KEY: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = Field(...)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., gt=0)

    # ---------- External API ----------
    EXTERNAL_API_URL: str = Field(...)
    EXTERNAL_API_TIMEOUT: int = Field(..., gt=0)

    # Tell pydantic-settings to load values from the .env file.
    # `extra="ignore"` means unknown keys in .env won't crash the app.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # ---------- Admin seed (used by scripts/seed_admin.py) ----------
    ADMIN_EMAIL: str = Field(..., description="Email for the seeded admin")
    ADMIN_PASSWORD: str = Field(..., min_length=6, description="Password for the seeded admin")


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.

    `lru_cache` ensures the .env file is parsed only once per process,
    no matter how many times `get_settings()` is called.
    """
    return Settings()


# Single shared instance — import this everywhere.
settings = get_settings()