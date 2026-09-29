"""
External API — WorldTimeAPI integration with graceful fallback.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def get_current_utc_time() -> tuple[datetime, str]:
    """
    Return (utc_datetime, source).

    source is "worldtimeapi" on success, "local" on fallback.
    Never raises — if the external call fails, returns local UTC.
    """
    try:
        response = httpx.get(
            settings.EXTERNAL_API_URL,
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        # WorldTimeAPI returns ISO 8601 with offset, e.g. "2026-09-24T07:02:03.123456+00:00"
        dt_str = data.get("datetime")
        if not dt_str:
            raise ValueError("Missing 'datetime' in external response")

        # Strip the offset and treat as naive UTC — matches our DB columns.
        dt = datetime.fromisoformat(dt_str)
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt, "worldtimeapi"

    except Exception as e:
        logger.warning("External time API failed (%s). Falling back to local UTC.", e)
        return datetime.now(timezone.utc).replace(tzinfo=None), "local"


def get_external_health() -> dict:
    """
    Probe the external API and report status. Used by /external/health.
    Never raises.
    """
    try:
        response = httpx.get(
            settings.EXTERNAL_API_URL,
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        return {
            "reachable": response.status_code == 200,
            "status_code": response.status_code,
            "url": settings.EXTERNAL_API_URL,
        }
    except Exception as e:
        return {
            "reachable": False,
            "error": str(e),
            "url": settings.EXTERNAL_API_URL,
        }