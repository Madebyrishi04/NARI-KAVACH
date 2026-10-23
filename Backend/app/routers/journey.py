from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.journey import SafetyJourney
from app.schemas.journey import JourneyCreate, JourneyResponse
from app.core.dependencies import get_current_user_id


router = APIRouter(
    prefix="/journeys",
    tags=["Safety Journey"]
)


@router.post(
    "/",
    response_model=JourneyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_journey(
    journey_data: JourneyCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_journey = SafetyJourney(
        user_id=user_id,
        source_latitude=journey_data.source_latitude,
        source_longitude=journey_data.source_longitude,
        destination_latitude=journey_data.destination_latitude,
        destination_longitude=journey_data.destination_longitude,
        status="planned"
    )

    db.add(new_journey)
    db.commit()
    db.refresh(new_journey)

    return new_journey


@router.get(
    "/",
    response_model=list[JourneyResponse]
)
def get_my_journeys(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    journeys = (
        db.query(SafetyJourney)
        .filter(SafetyJourney.user_id == user_id)
        .order_by(SafetyJourney.created_at.desc())
        .all()
    )

    return journeys


@router.put("/{journey_id}/start")
def start_journey(
    journey_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    journey = (
        db.query(SafetyJourney)
        .filter(
            SafetyJourney.id == journey_id,
            SafetyJourney.user_id == user_id
        )
        .first()
    )

    if not journey:
        raise HTTPException(
            status_code=404,
            detail="Journey not found"
        )

    if journey.status != "planned":
        raise HTTPException(
            status_code=400,
            detail="Journey has already been started or completed"
        )

    journey.status = "active"
    journey.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(journey)

    return {
        "message": "Journey started successfully",
        "journey_id": journey.id,
        "status": journey.status,
        "started_at": journey.started_at
    }

@router.put("/{journey_id}/complete")
def complete_journey(
    journey_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    journey = (
        db.query(SafetyJourney)
        .filter(
            SafetyJourney.id == journey_id,
            SafetyJourney.user_id == user_id
        )
        .first()
    )

    if not journey:
        raise HTTPException(
            status_code=404,
            detail="Journey not found"
        )

    if journey.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Only an active journey can be completed"
        )

    journey.status = "completed"
    journey.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(journey)

    return {
        "message": "Journey completed successfully",
        "journey_id": journey.id,
        "status": journey.status,
        "completed_at": journey.completed_at
    }
@router.put("/{journey_id}/location")
def update_journey_location(
    journey_id: int,
    latitude: float,
    longitude: float,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    journey = (
        db.query(SafetyJourney)
        .filter(
            SafetyJourney.id == journey_id,
            SafetyJourney.user_id == user_id
        )
        .first()
    )

    if not journey:
        raise HTTPException(
            status_code=404,
            detail="Journey not found"
        )

    if journey.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Current location can only be updated for an active journey"
        )

    journey.current_latitude = latitude
    journey.current_longitude = longitude
    journey.last_location_update = datetime.now(timezone.utc)

    db.commit()
    db.refresh(journey)

    return {
        "message": "Journey location updated successfully",
        "journey_id": journey.id,
        "current_latitude": journey.current_latitude,
        "current_longitude": journey.current_longitude,
        "last_location_update": journey.last_location_update
    }


@router.get("/{journey_id}/location")
def get_journey_location(
    journey_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    journey = (
        db.query(SafetyJourney)
        .filter(
            SafetyJourney.id == journey_id,
            SafetyJourney.user_id == user_id
        )
        .first()
    )

    if not journey:
        raise HTTPException(
            status_code=404,
            detail="Journey not found"
        )

    if journey.current_latitude is None or journey.current_longitude is None:
        raise HTTPException(
            status_code=404,
            detail="Current location not available"
        )

    return {
        "journey_id": journey.id,
        "status": journey.status,
        "current_latitude": journey.current_latitude,
        "current_longitude": journey.current_longitude,
        "last_location_update": journey.last_location_update
    }