"""
History logging — records every appointment state change.
"""

from sqlalchemy.orm import Session

from app.models.history import AppointmentHistory


def log_action(
    db: Session,
    appointment_id: int,
    action: str,
    changed_by: int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> AppointmentHistory:
    """
    Insert a history row.

    Caller is responsible for committing — this function just adds to the
    current transaction so the history write is atomic with the action itself.
    """
    entry = AppointmentHistory(
        appointment_id=appointment_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
    )
    db.add(entry)
    return entry


def get_history(db: Session, appointment_id: int) -> list[AppointmentHistory]:
    """Return history rows for an appointment, oldest first."""
    return (
        db.query(AppointmentHistory)
        .filter(AppointmentHistory.appointment_id == appointment_id)
        .order_by(AppointmentHistory.timestamp.asc())
        .all()
    )