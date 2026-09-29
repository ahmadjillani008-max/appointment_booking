"""
Auth routes — register, login, and current-user info.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserOut, Token
from app.services import auth_service
from app.core.security import create_access_token, get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""
    if auth_service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    return auth_service.register_user(db, data)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Verify credentials and return a JWT."""
    user = auth_service.authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=user.id, extra={"role": user.role})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user