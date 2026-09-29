# Appointment & Booking Management System

FastAPI + PostgreSQL backend for booking appointments.
Authentication: JWT only.

## Tech Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy + Alembic
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **External API:** WorldTimeAPI (no key required)
- **Testing:** Pytest + httpx

## Setup

### 1. Clone and enter project
```bash
git clone <repo-url>
cd appointment-booking

## Seed the Admin

After running migrations for the first time:

```bash
python -m scripts.seed_admin