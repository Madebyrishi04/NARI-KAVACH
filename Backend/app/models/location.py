from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geography

from app.database.connection import Base


class UserLocation(Base):
    __tablename__ = "user_locations"

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

    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )