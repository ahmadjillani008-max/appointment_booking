"""
Service routes — create, list, get, update, soft-delete.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceOut
from app.services import service_service
from app.core.security import get_current_user, require_provider
from app.utils.pagination import paginate

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceOut, status_code=201)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    provider: User = Depends(require_provider),
):
    """Create a service. Providers only."""
    return service_service.create_service(db, data, provider)


@router.get("")
def list_services(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="Substring match on name"),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    provider_id: int | None = Query(default=None),
    sort: str = Query(default="created_at", pattern="^(created_at|price|name)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    """List active services with search, filter, sort, pagination."""
    query = service_service.build_service_query(
        db,
        search=search,
        min_price=min_price,
        max_price=max_price,
        provider_id=provider_id,
        sort=sort,
        order=order,
    )
    result = paginate(query, page=page, size=size)
    result["items"] = [ServiceOut.model_validate(s) for s in result["items"]]
    return result


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Fetch one service by id."""
    service = service_service.get_service(db, service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partial update. Owner or admin only."""
    service = service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        return service_service.update_service(db, service, data, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a service. Owner or admin only."""
    service = service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        service_service.delete_service(db, service, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))