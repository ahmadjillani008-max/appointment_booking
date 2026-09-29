"""
Seed script — creates the first admin user if missing.
Run: python -m scripts.seed_admin
"""

from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password


def main():
    db = SessionLocal()
    try:
        existing = (
            db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        )
        if existing:
            print(f"Admin already exists: {existing.email} (role={existing.role})")
            return

        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Admin",
            role="admin",
        )
        db.add(admin)
        db.commit()
        print(f"Created admin: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()