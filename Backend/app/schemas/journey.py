from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class JourneyCreate(BaseModel):
    source_latitude: float = Field(
        ge=-90,
        le=90
    )

    source_longitude: float = Field(
        ge=-180,
        le=180
    )

    destination_latitude: float = Field(
        ge=-90,
        le=90
    )

    destination_longitude: float = Field(
        ge=-180,
        le=180
    )


class JourneyResponse(BaseModel):
    id: int
    user_id: int

    source_latitude: float
    source_longitude: float

    destination_latitude: float
    destination_longitude: float

    status: str

    started_at: datetime | None
    completed_at: datetime | None

    current_latitude: float | None
    current_longitude: float | None
    last_location_update: datetime | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )