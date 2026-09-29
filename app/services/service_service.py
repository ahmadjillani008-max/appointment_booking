"""
Service business logic — CRUD with ownership checks.
"""

from sqlalchemy.orm import Query, Session

from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceUpdate


def create_service(db: Session, data: ServiceCreate, provider: User) -> Service:
    """Create a service owned by `provider`."""
    service = Service(
        provider_id=provider.id,
        name=data.name,
        description=data.description,
        duration_minutes=data.duration_minutes,
        price=data.price,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def build_service_query(
    db: Session,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    provider_id: int | None = None,
    active_only: bool = True,
    sort: str = "created_at",
    order: str = "desc",
) -> Query:
    """Build a filtered/sorted query for listing services."""
    query = db.query(Service)

    if active_only:
        query = query.filter(Service.is_active.is_(True))

    if search:
        like = f"%{search}%"
        query = query.filter(Service.name.ilike(like))

    if min_price is not None:
        query = query.filter(Service.price >= min_price)

    if max_price is not None:
        query = query.filter(Service.price <= max_price)

    if provider_id is not None:
        query = query.filter(Service.provider_id == provider_id)

    # Sorting — whitelist columns to prevent SQL injection.
    sortable = {
        "created_at": Service.created_at,
        "price": Service.price,
        "name": Service.name,
    }
    col = sortable.get(sort, Service.created_at)
    query = query.order_by(col.desc() if order == "desc" else col.asc())

    return query


def get_service(db: Session, service_id: int) -> Service | None:
    """Fetch a service by id."""
    return db.query(Service).filter(Service.id == service_id).first()


def update_service(
    db: Session, service: Service, data: ServiceUpdate, current_user: User
) -> Service:
    """Apply a partial update. Only the owner (or admin) may call this."""
    if service.provider_id != current_user.id and current_user.role != "admin":
        raise PermissionError("Not allowed to modify this service")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service: Service, current_user: User) -> None:
    """Soft-delete: mark inactive. Only owner or admin."""
    if service.provider_id != current_user.id and current_user.role != "admin":
        raise PermissionError("Not allowed to delete this service")
    service.is_active = False
    db.commit()