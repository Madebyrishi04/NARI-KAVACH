from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geography

from app.database.connection import Base


class SafetyReport(Base):
    __tablename__ = "safety_reports"

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

    report_type = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False,
        default="medium"
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    location = Column(
        Geography(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )