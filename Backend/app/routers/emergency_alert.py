
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.emergency_alert import EmergencyAlert
from app.models.location import UserLocation
from app.models.emergency_contact import EmergencyContact
from app.schemas.emergency_alert import EmergencyAlertResponse
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.core.email_service import send_sos_email


router = APIRouter(
    prefix="/sos",
    tags=["SOS Emergency Alert"]
)


@router.post(
    "/trigger",
    response_model=EmergencyAlertResponse,
    status_code=status.HTTP_201_CREATED
)
async def trigger_sos(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get the user's latest saved location
    latest_location = db.query(UserLocation).filter(
        UserLocation.user_id == user_id
    ).order_by(
        UserLocation.recorded_at.desc()
    ).first()

    if not latest_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please save your location before triggering SOS."
        )

    # Create the SOS alert
    alert = EmergencyAlert(
        user_id=user_id,
        location_id=latest_location.id,
        status="active"
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Get the user's emergency contacts
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).all()

    # Create a Google Maps link using the saved coordinates
    location_link = (
        "https://www.google.com/maps/search/?api=1&query="
        f"{latest_location.latitude},{latest_location.longitude}"
    )

    # Email contacts that have an email address
    for contact in contacts:
        if not contact.email:
            continue

        try:
            await send_sos_email(
                to_email=contact.email,
                user_name=user.full_name,
                location_link=location_link
            )
        except Exception:
            # Keep the SOS alert recorded even if email delivery fails.
            # Log the failure without exposing credentials.
            import logging
            logging.exception(
                "Failed to send SOS email to contact ID %s",
                contact.id
            )

    return alert


@router.put("/resolve/{alert_id}")
def resolve_sos(
    alert_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Find the alert belonging to the logged-in user
    alert = db.query(EmergencyAlert).filter(
        EmergencyAlert.id == alert_id,
        EmergencyAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS alert not found"
        )

    if alert.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This alert is already resolved"
        )

    # Mark the alert as resolved
    alert.status = "resolved"

    db.commit()
    db.refresh(alert)

    return {
        "message": "SOS alert resolved successfully",
        "alert_id": alert.id,
        "status": alert.status
    }
