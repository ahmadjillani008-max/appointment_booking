"""
Appointment business logic — concurrency-safe booking, reschedule, cancel, status.
"""

from sqlalchemy.orm import Query, Session

from app.models.appointment import Appointment
from app.models.slot import Slot
from app.models.user import User
from app.schemas.appointment import AppointmentCreate
from app.services import history_service


class BookingConflict(Exception):
    """Slot already taken."""


class BookingError(Exception):
    """Other booking problems (missing, past, invalid transition, etc.)."""


def book_slot(db: Session, data: AppointmentCreate, current_user: User) -> Appointment:
    """Create a booking with a row-level lock on the slot."""
    try:
        slot = (
            db.query(Slot)
            .filter(Slot.id == data.slot_id)
            .with_for_update()
            .first()
        )
        if slot is None:
            raise BookingError("Slot not found")
        if slot.is_booked:
            raise BookingConflict("Slot is already booked")

        appointment = Appointment(
            user_id=current_user.id,
            slot_id=slot.id,
            status="confirmed",
            notes=data.notes,
        )
        db.add(appointment)
        slot.is_booked = True

        db.flush()   # assign appointment.id before logging
        history_service.log_action(
            db,
            appointment_id=appointment.id,
            action="created",
            changed_by=current_user.id,
            new_value=f"slot_id={slot.id}",
        )

        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def reschedule_appointment(
    db: Session, appointment: Appointment, new_slot_id: int, current_user: User
) -> Appointment:
    """Move an appointment to a different slot. Locks both rows in id order."""
    if appointment.user_id != current_user.id and current_user.role != "admin":
        raise BookingError("Not allowed to reschedule this appointment")
    if appointment.status in ("cancelled", "completed"):
        raise BookingError(f"Cannot reschedule a {appointment.status} appointment")
    if appointment.slot_id == new_slot_id:
        raise BookingError("New slot is the same as the current slot")

    try:
        # Lock both slots in ascending id order to avoid deadlocks.
        ids = sorted([appointment.slot_id, new_slot_id])
        locked = (
            db.query(Slot)
            .filter(Slot.id.in_(ids))
            .order_by(Slot.id.asc())
            .with_for_update()
            .all()
        )
        slots_by_id = {s.id: s for s in locked}

        old_slot = slots_by_id.get(appointment.slot_id)
        new_slot = slots_by_id.get(new_slot_id)

        if new_slot is None:
            raise BookingError("New slot not found")
        if new_slot.is_booked:
            raise BookingConflict("New slot is already booked")

        old_slot_id = appointment.slot_id
        old_slot.is_booked = False
        new_slot.is_booked = True
        appointment.slot_id = new_slot.id

        history_service.log_action(
            db,
            appointment_id=appointment.id,
            action="rescheduled",
            changed_by=current_user.id,
            old_value=f"slot_id={old_slot_id}",
            new_value=f"slot_id={new_slot.id}",
        )

        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def cancel_appointment(
    db: Session, appointment: Appointment, current_user: User
) -> Appointment:
    """Cancel appointment and free its slot."""
    if appointment.user_id != current_user.id and current_user.role != "admin":
        raise BookingError("Not allowed to cancel this appointment")
    if appointment.status == "cancelled":
        raise BookingError("Appointment is already cancelled")
    if appointment.status == "completed":
        raise BookingError("Cannot cancel a completed appointment")

    try:
        slot = (
            db.query(Slot)
            .filter(Slot.id == appointment.slot_id)
            .with_for_update()
            .first()
        )

        appointment.status = "cancelled"
        if slot is not None:
            slot.is_booked = False

        history_service.log_action(
            db,
            appointment_id=appointment.id,
            action="cancelled",
            changed_by=current_user.id,
            old_value="status=confirmed",
            new_value="status=cancelled",
        )

        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def update_status(
    db: Session, appointment: Appointment, new_status: str, current_user: User
) -> Appointment:
    """Change status. Owning provider or admin. Transition rules enforced."""
    is_admin = current_user.role == "admin"
    is_owning_provider = (
        current_user.role == "provider"
        and appointment.slot.service.provider_id == current_user.id
    )
    if not (is_admin or is_owning_provider):
        raise BookingError("Not allowed to change status of this appointment")

    allowed = {
        "confirmed": {"completed"},
        "cancelled": set(),
        "completed": set(),
    }
    if new_status not in allowed.get(appointment.status, set()):
        raise BookingError(
            f"Cannot change status from {appointment.status} to {new_status}"
        )

    old_status = appointment.status
    appointment.status = new_status

    history_service.log_action(
        db,
        appointment_id=appointment.id,
        action="status_changed",
        changed_by=current_user.id,
        old_value=f"status={old_status}",
        new_value=f"status={new_status}",
    )

    db.commit()
    db.refresh(appointment)
    return appointment


def build_appointment_query(
    db: Session,
    user_id: int | None = None,
    status: str | None = None,
) -> Query:
    """Filter appointments. user_id=None for admin."""
    query = db.query(Appointment)
    if user_id is not None:
        query = query.filter(Appointment.user_id == user_id)
    if status is not None:
        query = query.filter(Appointment.status == status)
    return query.order_by(Appointment.created_at.desc())


def get_appointment(db: Session, appointment_id: int) -> Appointment | None:
    """Fetch an appointment by id."""
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()