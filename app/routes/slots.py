"""
Slot routes — nested under /services/{service_id}/slots.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.slot import SlotCreate, SlotOut
from app.services import slot_service, service_service
from app.core.security import get_current_user
from app.utils.pagination import paginate

router = APIRouter(prefix="/services/{service_id}/slots", tags=["slots"])


def _get_service_or_404(db: Session, service_id: int):
    """Shared helper — fetch an active service or raise 404."""
    service = service_service.get_service(db, service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("", response_model=SlotOut, status_code=201)
def create_slot(
    service_id: int,
    data: SlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a slot. Owner provider (or admin) only."""
    service = _get_service_or_404(db, service_id)
    try:
        return slot_service.create_slot(db, service, data, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_slots(
    service_id: int,
    db: Session = Depends(get_db),
    available_only: bool = Query(default=True),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
):
    """List slots for a service (public)."""
    _get_service_or_404(db, service_id)
    query = slot_service.build_slot_query(
        db,
        service_id=service_id,
        available_only=available_only,
        date_from=date_from,
        date_to=date_to,
    )
    result = paginate(query, page=page, size=size)
    result["items"] = [SlotOut.model_validate(s) for s in result["items"]]
    return result


@router.get("/{slot_id}", response_model=SlotOut)
def get_slot(service_id: int, slot_id: int, db: Session = Depends(get_db)):
    """Fetch one slot (public)."""
    _get_service_or_404(db, service_id)
    slot = slot_service.get_slot(db, slot_id)
    if not slot or slot.service_id != service_id:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


@router.delete("/{slot_id}", status_code=204)
def delete_slot(
    service_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a slot. Owner provider (or admin) only. Booked slots cannot be deleted."""
    _get_service_or_404(db, service_id)
    slot = slot_service.get_slot(db, slot_id)
    if not slot or slot.service_id != service_id:
        raise HTTPException(status_code=404, detail="Slot not found")
    try:
        slot_service.delete_slot(db, slot, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))