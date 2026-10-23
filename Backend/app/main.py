from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.connection import Base, engine

# Models
from app.models.user import User
from app.models.emergency_contact import EmergencyContact
from app.models.location import UserLocation
from app.models.emergency_alert import EmergencyAlert
from app.models.safety_report import SafetyReport
from app.models.journey import SafetyJourney
from app.models.password_reset import PasswordResetToken

# Routers
from app.routers.auth import router as auth_router
from app.routers.login import router as login_router
from app.routers.password_reset import router as password_reset_router 
from app.routers.profile import router as profile_router
from app.routers.emergency import router as emergency_router
from app.routers.location import router as location_router
from app.routers.emergency_alert import router as emergency_alert_router
from app.routers.alert_history import router as alert_history_router
from app.routers.safety_report import router as safety_report_router
from app.routers.journey import router as journey_router
from app.routers.destination import router as destination_router

from app.core.dependencies import get_current_user_id


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Personal Safety API",
    description="Backend for our safety application",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router)
app.include_router(login_router)
app.include_router(password_reset_router)
app.include_router(profile_router)
app.include_router(emergency_router)
app.include_router(location_router)
app.include_router(emergency_alert_router)
app.include_router(alert_history_router)
app.include_router(safety_report_router)
app.include_router(journey_router)
app.include_router(destination_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Personal Safety App!",
        "status": "Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/test-db")
def test_database():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "message": "PostgreSQL connected successfully!"
        }

    except Exception as e:
        return {
            "error": str(e)
        }


@app.get("/protected")
def protected_route(
    user_id: int = Depends(get_current_user_id)
):
    return {
        "message": "You are authenticated!",
        "user_id": user_id
    }