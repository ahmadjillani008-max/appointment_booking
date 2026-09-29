"""
Appointment routes — book, list, get, reschedule, cancel, status, history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentReschedule,
    AppointmentStatusUpdate,
)
from app.schemas.history import HistoryOut
from app.services import appointment_service as appt
from app.services import history_service
from app.core.security import get_current_user
from app.utils.pagination import paginate

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book a slot. Any authenticated user. Concurrency-safe."""
    try:
        return appt.book_slot(db, data, current_user)
    except appt.BookingConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except appt.BookingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: str | None = Query(default=None, pattern="^(confirmed|completed|cancelled)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    """List my appointments. Admins see all."""
    user_filter = None if current_user.role == "admin" else current_user.id
    query = appt.build_appointment_query(db, user_id=user_filter, status=status)
    result = paginate(query, page=page, size=size)
    result["items"] = [AppointmentOut.model_validate(a) for a in result["items"]]
    return result


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one appointment. Owner, owning provider, or admin only."""
    appointment = appt.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    is_owner = appointment.user_id == current_user.id
    is_admin = current_user.role == "admin"
    is_provider = (
        current_user.role == "provider"
        and appointment.slot.service.provider_id == current_user.id
    )

    if not (is_owner or is_admin or is_provider):
        raise HTTPException(status_code=403, detail="Not allowed to view this appointment")

    return appointment


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: int,
    data: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move an appointment to a different slot. Owner or admin only."""
    appointment = appt.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to reschedule this appointment")

    try:
        return appt.reschedule_appointment(db, appointment, data.new_slot_id, current_user)
    except appt.BookingConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except appt.BookingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an appointment and free its slot. Owner or admin only."""
    appointment = appt.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to cancel this appointment")

    try:
        return appt.cancel_appointment(db, appointment, current_user)
    except appt.BookingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change status. Owning provider or admin only."""
    appointment = appt.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    try:
        return appt.update_status(db, appointment, data.status, current_user)
    except appt.BookingError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{appointment_id}/history", response_model=list[HistoryOut])
def get_appointment_history(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View the audit trail. Same access rules as GET /appointments/{id}."""
    appointment = appt.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    is_owner = appointment.user_id == current_user.id
    is_admin = current_user.role == "admin"
    is_provider = (
        current_user.role == "provider"
        and appointment.slot.service.provider_id == current_user.id
    )

    if not (is_owner or is_admin or is_provider):
        raise HTTPException(status_code=403, detail="Not allowed to view this history")

    return history_service.get_history(db, appointment_id)