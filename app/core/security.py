"""
Security — password hashing, JWT create/verify, and auth dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

# bcrypt is intentionally slow — that's the point.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Reads `Authorization: Bearer <token>` header.
bearer_scheme = HTTPBearer(auto_error=False)


# ---------- Passwords ----------

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------- JWT ----------

def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """Create a signed JWT with `sub` = user id and optional extra claims."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode & verify a JWT. Returns the payload, or None if invalid/expired."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None


# ---------- Dependencies ----------

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT, load the user, or raise 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def require_provider(current_user: User = Depends(get_current_user)) -> User:
    """Allow only providers or admins."""
    if current_user.role not in ("provider", "admin"):
        raise HTTPException(status_code=403, detail="Provider access required")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only admins."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user