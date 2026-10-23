
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.location import UserLocation
from app.schemas.location import LocationCreate, LocationResponse
from app.core.dependencies import get_current_user_id


router = APIRouter(
    prefix="/locations",
    tags=["Location Tracking"]
)


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED
)
def save_location(
    location_data: LocationCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_location = UserLocation(
        user_id=user_id,
        latitude=location_data.latitude,
        longitude=location_data.longitude
    )

    db.add(new_location)
    db.commit()
    db.refresh(new_location)

    return new_location

@router.get("/latest", response_model=LocationResponse)
def get_latest_location(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    location = db.query(UserLocation).filter(
        UserLocation.user_id == user_id
    ).order_by(
        UserLocation.recorded_at.desc()
    ).first()

    if not location:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="No location found"
        )

    return location
