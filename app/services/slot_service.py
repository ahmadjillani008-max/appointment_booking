"""
Slot business logic — create, list, delete, with validation and ownership.
"""

from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Query, Session

from app.models.service import Service
from app.models.slot import Slot
from app.models.user import User
from app.schemas.slot import SlotCreate
from app.services import external_api


def _overlap_exists(db: Session, service_id: int, start: datetime, end: datetime) -> bool:
    """True if any existing slot for this service overlaps [start, end)."""
    return db.query(Slot).filter(
        Slot.service_id == service_id,
        # overlap: existing.start < new.end AND existing.end > new.start
        and_(Slot.start_time < end, Slot.end_time > start),
    ).first() is not None


def create_slot(
    db: Session, service: Service, data: SlotCreate, current_user: User
) -> Slot:
    """Create a slot for a service. Only owner (or admin) may call this."""
    if service.provider_id != current_user.id and current_user.role != "admin":
        raise PermissionError("Not allowed to add slots to this service")

    if not service.is_active:
        raise ValueError("Cannot add slots to an inactive service")

    # Validate against real-world UTC (falls back to local if WorldTimeAPI is down).
    now_utc, _source = external_api.get_current_utc_time()
    if data.start_time < now_utc:
        raise ValueError("Cannot create a slot in the past")

    if _overlap_exists(db, service.id, data.start_time, data.end_time):
        raise ValueError("Slot overlaps with an existing slot for this service")

    slot = Slot(
        service_id=service.id,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def build_slot_query(
    db: Session,
    service_id: int,
    available_only: bool = False,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Query:
    """Filter slots for a service."""
    query = db.query(Slot).filter(Slot.service_id == service_id)

    if available_only:
        query = query.filter(Slot.is_booked.is_(False))

    if date_from is not None:
        query = query.filter(Slot.start_time >= date_from)

    if date_to is not None:
        query = query.filter(Slot.start_time <= date_to)

    return query.order_by(Slot.start_time.asc())


def get_slot(db: Session, slot_id: int) -> Slot | None:
    """Fetch a slot by id."""
    return db.query(Slot).filter(Slot.id == slot_id).first()


def delete_slot(db: Session, slot: Slot, current_user: User) -> None:
    """Delete a slot. Owner (or admin) only. Cannot delete booked slots."""
    if slot.service.provider_id != current_user.id and current_user.role != "admin":
        raise PermissionError("Not allowed to delete this slot")

    if slot.is_booked:
        raise ValueError("Cannot delete a booked slot")

    db.delete(slot)
    db.commit()