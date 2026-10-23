from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement

from app.database.connection import get_db
from app.models.safety_report import SafetyReport
from app.schemas.safety_report import (
    SafetyReportCreate,
    SafetyReportResponse
)
from app.core.dependencies import get_current_user_id


router = APIRouter(
    prefix="/safety-reports",
    tags=["Safety Reports"]
)


@router.post(
    "/",
    response_model=SafetyReportResponse,
    status_code=status.HTTP_201_CREATED
)
def create_safety_report(
    report_data: SafetyReportCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_report = SafetyReport(
        user_id=user_id,
        report_type=report_data.report_type,
        description=report_data.description,
        severity=report_data.severity,
        latitude=report_data.latitude,
        longitude=report_data.longitude,
        location=WKTElement(
            f"POINT({report_data.longitude} {report_data.latitude})",
            srid=4326
        )
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


@router.get(
    "/",
    response_model=list[SafetyReportResponse]
)
def get_safety_reports(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    reports = (
        db.query(SafetyReport)
        .filter(SafetyReport.user_id == user_id)
        .order_by(SafetyReport.created_at.desc())
        .all()
    )

    return reports


@router.get("/nearby")
def get_nearby_safety_reports(
    latitude: float,
    longitude: float,
    radius_km: float = 1.0,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user_point = func.ST_SetSRID(
        func.ST_MakePoint(longitude, latitude),
        4326
    ).cast(
        Geography(
            geometry_type="POINT",
            srid=4326
        )
    )

    distance = func.ST_Distance(
        SafetyReport.location,
        user_point
    )

    reports = (
        db.query(
            SafetyReport,
            distance.label("distance_meters")
        )
        .filter(
            SafetyReport.location.isnot(None),
            func.ST_DWithin(
                SafetyReport.location,
                user_point,
                radius_km * 1000
            )
        )
        .order_by(distance)
        .all()
    )

    result = []

    for report, distance_meters in reports:
        result.append({
            "id": report.id,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "description": report.description,
            "severity": report.severity,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "distance_meters": round(float(distance_meters), 2)
        })

    return result

@router.get(
    "/{report_id}",
    response_model=SafetyReportResponse
)
def get_safety_report(
    report_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    report = (
        db.query(SafetyReport)
        .filter(
            SafetyReport.id == report_id,
            SafetyReport.user_id == user_id
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Safety report not found"
        )

    return report