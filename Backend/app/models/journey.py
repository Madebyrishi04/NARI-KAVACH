from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.connection import Base


class SafetyJourney(Base):
    __tablename__ = "safety_journeys"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    source_latitude = Column(
        Float,
        nullable=False
    )

    source_longitude = Column(
        Float,
        nullable=False
    )

    destination_latitude = Column(
        Float,
        nullable=False
    )

    destination_longitude = Column(
        Float,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="planned"
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    current_latitude = Column(
        Float,
        nullable=True
    )

    current_longitude = Column(
        Float,
        nullable=True
    )

    last_location_update = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )