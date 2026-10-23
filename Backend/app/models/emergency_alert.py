
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    location_id = Column(
        Integer,
        ForeignKey("user_locations.id"),
        nullable=True
    )

    status = Column(String, default="active", nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
