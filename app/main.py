"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.handlers import register_exception_handlers
from app.routes import auth, services, slots, appointments, external

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="Appointment & Booking Management System — JWT auth, PostgreSQL, "
                "concurrency-safe bookings.",
)

# CORS — open for local dev; restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uniform error responses.
register_exception_handlers(app)

# Routers
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(slots.router)
app.include_router(appointments.router)
app.include_router(external.router)


@app.get("/health", tags=["health"])
def health():
    """Simple liveness check."""
    return {"status": "ok", "app": settings.APP_NAME}