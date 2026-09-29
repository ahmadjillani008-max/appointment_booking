"""
External API routes — time and health checks.
"""

from fastapi import APIRouter

from app.services import external_api

router = APIRouter(prefix="/external", tags=["external"])


@router.get("/time")
def external_time():
    """Return current UTC time from WorldTimeAPI (falls back to local on failure)."""
    dt, source = external_api.get_current_utc_time()
    return {
        "utc_time": dt.isoformat(),
        "source": source,   # "worldtimeapi" or "local"
    }


@router.get("/health")
def external_health():
    """Check whether WorldTimeAPI is reachable."""
    return external_api.get_external_health()