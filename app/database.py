"""
Database engine, session factory, and Base class.
All models inherit from `Base`.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Engine — one per process, manages the connection pool.
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # log SQL when DEBUG=True
    pool_pre_ping=True,        # detect dead connections before use
)

# Session factory — call SessionLocal() to get a new DB session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class all models inherit from.
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()