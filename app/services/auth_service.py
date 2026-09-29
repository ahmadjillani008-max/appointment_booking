"""
Auth business logic — register new users, verify credentials.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password
from app.schemas.user import UserRegister


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by email, or None."""
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, data: UserRegister) -> User:
    """Create a new user. Assumes email uniqueness was checked by caller."""
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if email exists AND password matches. Else None."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user