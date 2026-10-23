
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.emergency_alert import EmergencyAlert
from app.schemas.emergency_alert import EmergencyAlertResponse
from app.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/sos",
    tags=["SOS Alert History"]
)


@router.get(
    "/history",
    response_model=list[EmergencyAlertResponse]
)
def get_alert_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    alerts = db.query(EmergencyAlert).filter(
        EmergencyAlert.user_id == user_id
    ).order_by(
        EmergencyAlert.created_at.desc()
    ).all()

    return alerts
