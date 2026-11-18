from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement

from app.database.connection import get_db, IS_SQLITE
from app.models.safety_report import SafetyReport
from app.schemas.safety_report import (
    SafetyReportCreate,
    SafetyReportResponse
)
from app.core.dependencies import get_current_user_id
import math


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


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
    loc_val = (
        f"POINT({report_data.longitude} {report_data.latitude})"
        if IS_SQLITE
        else WKTElement(
            f"POINT({report_data.longitude} {report_data.latitude})",
            srid=4326
        )
    )

    new_report = SafetyReport(
        user_id=user_id,
        report_type=report_data.report_type,
        description=report_data.description,
        severity=report_data.severity,
        latitude=report_data.latitude,
        longitude=report_data.longitude,
        location=loc_val
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
        .order_by(SafetyReport.created_at.desc())
        .all()
    )

    return reports


@router.get("/nearby")
def get_nearby_safety_reports(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if IS_SQLITE:
        all_reports = db.query(SafetyReport).all()
        result = []
        max_dist_m = radius_km * 1000.0

        for report in all_reports:
            d_m = haversine_distance_m(latitude, longitude, report.latitude, report.longitude)
            if d_m <= max_dist_m:
                result.append({
                    "id": report.id,
                    "user_id": report.user_id,
                    "report_type": report.report_type,
                    "description": report.description,
                    "severity": report.severity,
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                    "distance_meters": round(float(d_m), 2)
                })

        result.sort(key=lambda x: x["distance_meters"])
        return result

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