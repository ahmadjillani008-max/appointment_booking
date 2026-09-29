"""
Pagination helper — slices any SQLAlchemy query and returns metadata.
"""

from typing import Any
from sqlalchemy.orm import Query


def paginate(query: Query, page: int, size: int) -> dict[str, Any]:
    """
    Slice a query into a page.

    Returns:
        {
            "items": [...],
            "total": <total rows>,
            "page": <current page>,
            "size": <page size>,
            "pages": <total pages>
        }
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 10
    if size > 100:
        size = 100  # cap to avoid abuse

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    pages = (total + size - 1) // size  # ceil division

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }