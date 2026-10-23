
from pydantic import BaseModel
from datetime import datetime


class EmergencyAlertResponse(BaseModel):
    id: int
    user_id: int
    location_id: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
