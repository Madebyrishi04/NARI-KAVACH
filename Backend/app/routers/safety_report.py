import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.routers.dashboard import POLICE_FACILITIES, HOSPITAL_FACILITIES
from app.routers.ml_risk import get_risk_engine

IST = timezone(timedelta(hours=5, minutes=30))


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


def get_point_at_distance_and_bearing(lat: float, lon: float, d_km: float, bearing_deg: float):
    R = 6371.0
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    brng_r = math.radians(bearing_deg)
    lat2_r = math.asin(math.sin(lat_r) * math.cos(d_km / R) +
                       math.cos(lat_r) * math.sin(d_km / R) * math.cos(brng_r))
    lon2_r = lon_r + math.atan2(math.sin(brng_r) * math.sin(d_km / R) * math.cos(lat_r),
                                math.cos(d_km / R) - math.sin(lat_r) * math.sin(lat2_r))
    return math.degrees(lat2_r), math.degrees(lon2_r)


def to_ist(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(IST)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(IST)
    return dt.astimezone(IST)


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
    report_type: Optional[str] = None,
    severity: Optional[str] = None,
    date_range: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    time_of_day: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    all_reports = db.query(SafetyReport).all()
    max_dist_m = radius_km * 1000.0
    now_ist = datetime.now(IST)

    matched_reports = []

    for report in all_reports:
        d_m = haversine_distance_m(latitude, longitude, report.latitude, report.longitude)
        if d_m > max_dist_m:
            continue

        # Filter by report_type
        if isinstance(report_type, str) and report_type and report_type != "all":
            norm_db_type = (report.report_type or "").strip().lower().replace("_", " ")
            norm_q_type = report_type.strip().lower().replace("_", " ")
            if norm_db_type != norm_q_type:
                continue

        # Filter by severity
        if isinstance(severity, str) and severity and severity != "all":
            if (report.severity or "").strip().lower() != severity.strip().lower():
                continue

        # Date & Time filters
        rep_ist = to_ist(report.created_at)

        # Filter by date_range
        if isinstance(date_range, str) and date_range and date_range != "all":
            if date_range == "today":
                if rep_ist.date() != now_ist.date():
                    continue
            elif date_range == "7days":
                if rep_ist < now_ist - timedelta(days=7):
                    continue
            elif date_range == "30days":
                if rep_ist < now_ist - timedelta(days=30):
                    continue
            elif date_range == "90days":
                if rep_ist < now_ist - timedelta(days=90):
                    continue
            elif date_range == "custom":
                if start_date and isinstance(start_date, str):
                    try:
                        s_d = datetime.fromisoformat(start_date.split("T")[0]).date()
                        if rep_ist.date() < s_d:
                            continue
                    except Exception:
                        pass
                if end_date and isinstance(end_date, str):
                    try:
                        e_d = datetime.fromisoformat(end_date.split("T")[0]).date()
                        if rep_ist.date() > e_d:
                            continue
                    except Exception:
                        pass

        # Filter by time_of_day
        if isinstance(time_of_day, str) and time_of_day and time_of_day != "all":
            hr = rep_ist.hour
            if time_of_day == "morning" and not (5 <= hr < 12):
                continue
            elif time_of_day == "afternoon" and not (12 <= hr < 17):
                continue
            elif time_of_day == "evening" and not (17 <= hr < 21):
                continue
            elif time_of_day == "night" and not (hr >= 21 or hr < 5):
                continue

        matched_reports.append({
            "id": report.id,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "description": report.description,
            "severity": (report.severity or "medium").lower(),
            "latitude": report.latitude,
            "longitude": report.longitude,
            "created_at": rep_ist.isoformat(),
            "status": getattr(report, "status", "verified") or "verified",
            "distance_meters": round(float(d_m), 2)
        })

    matched_reports.sort(key=lambda x: x["distance_meters"])

    severity_counts = {
        "low": sum(1 for r in matched_reports if r["severity"] == "low"),
        "medium": sum(1 for r in matched_reports if r["severity"] == "medium"),
        "high": sum(1 for r in matched_reports if r["severity"] == "high"),
        "critical": sum(1 for r in matched_reports if r["severity"] == "critical"),
    }

    category_counts = {}
    for r in matched_reports:
        c = r["report_type"]
        category_counts[c] = category_counts.get(c, 0) + 1

    return {
        "reports": matched_reports,
        "total_count": len(matched_reports),
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "radius_km": radius_km
    }


@router.get("/risk-zones")
def get_risk_zones(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    risk_level: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Evaluates dynamic spatio-temporal ML risk across spatial sectors surrounding the coordinates.
    Integrates trained DynamicRiskEngine with police/hospital proximity and recent incident reports.
    """
    engine = get_risk_engine()
    now_ist = datetime.now(IST)
    hour = now_ist.hour
    day_of_week = now_ist.weekday()
    month = now_ist.month

    # Load all reports for local incident density
    all_reports = db.query(SafetyReport).all()

    # Generate spatial grid points
    grid_points = []
    
    # 1. Center zone
    center_radius = max(350.0, radius_km * 250.0)
    grid_points.append({
        "lat": latitude,
        "lon": longitude,
        "zone_radius": center_radius,
        "name": "Current Area Center"
    })

    # Radial rings
    if radius_km <= 2.0:
        ring_bearings = [0, 90, 180, 270]
        ring_radius = radius_km * 300.0
        for b in ring_bearings:
            p_lat, p_lon = get_point_at_distance_and_bearing(latitude, longitude, radius_km * 0.65, b)
            grid_points.append({
                "lat": p_lat,
                "lon": p_lon,
                "zone_radius": ring_radius,
                "name": f"Sector {b}°"
            })
    else:
        # Inner ring: 6 points
        inner_dist = radius_km * 0.45
        inner_radius = radius_km * 220.0
        for b in [0, 60, 120, 180, 240, 300]:
            p_lat, p_lon = get_point_at_distance_and_bearing(latitude, longitude, inner_dist, b)
            grid_points.append({
                "lat": p_lat,
                "lon": p_lon,
                "zone_radius": inner_radius,
                "name": f"Inner Sector {b}°"
            })

        # Outer ring: 8 points
        outer_dist = radius_km * 0.85
        outer_radius = radius_km * 240.0
        for b in [0, 45, 90, 135, 180, 225, 270, 315]:
            p_lat, p_lon = get_point_at_distance_and_bearing(latitude, longitude, outer_dist, b)
            grid_points.append({
                "lat": p_lat,
                "lon": p_lon,
                "zone_radius": outer_radius,
                "name": f"Outer Sector {b}°"
            })

    zones = []

    for idx, pt in enumerate(grid_points):
        z_lat = pt["lat"]
        z_lon = pt["lon"]
        z_rad = pt["zone_radius"]

        # Find nearest police station
        nearest_police = min(POLICE_FACILITIES, key=lambda f: haversine_distance_m(z_lat, z_lon, f[1], f[2]))
        dist_police_km = haversine_distance_m(z_lat, z_lon, nearest_police[1], nearest_police[2]) / 1000.0

        # Find nearest hospital
        nearest_hospital = min(HOSPITAL_FACILITIES, key=lambda f: haversine_distance_m(z_lat, z_lon, f[1], f[2]))
        dist_hospital_km = haversine_distance_m(z_lat, z_lon, nearest_hospital[1], nearest_hospital[2]) / 1000.0

        # Nearby reports within zone
        local_reports = []
        for rep in all_reports:
            dist_rep = haversine_distance_m(z_lat, z_lon, rep.latitude, rep.longitude)
            if dist_rep <= z_rad * 1.5:
                local_reports.append({
                    "latitude": rep.latitude,
                    "longitude": rep.longitude,
                    "incident_type": rep.report_type or "Other",
                    "verification_status": "verified"
                })

        incident_count = len(local_reports)

        # Lighting estimation: lower in outskirts, higher near central city / facilities
        lighting_score = max(0.25, min(0.90, 0.80 - (dist_police_km * 0.08)))

        # Evaluate risk via DynamicRiskEngine
        risk_score = 30.0
        risk_category = "LOW"
        confidence = 0.85
        factors = []

        if engine is not None:
            try:
                res = engine.evaluate_dynamic_risk(
                    latitude=z_lat,
                    longitude=z_lon,
                    hour=hour,
                    day_of_week=day_of_week,
                    month=month,
                    dist_police_km=dist_police_km,
                    dist_hospital_km=dist_hospital_km,
                    street_lighting_score=lighting_score,
                    weather_condition="Clear",
                    zone_type="Residential",
                    recent_reports=local_reports
                )
                risk_score = round(float(res.get("risk_score", 30.0)), 1)
                risk_category = str(res.get("risk_category", "LOW")).upper()
                confidence = round(float(res.get("confidence", 0.80)), 2)
                for f in res.get("top_risk_amplifying_factors", [])[:2]:
                    factors.append(f.get("description", ""))
                for f in res.get("top_risk_mitigating_factors", [])[:1]:
                    factors.append(f.get("description", ""))
            except Exception as e:
                print(f"[Risk-Zone ML Evaluation Error] {e}")

        if not factors:
            if dist_police_km > 3.0:
                factors.append(f"Police outpost distance: {dist_police_km:.1f} km")
            else:
                factors.append(f"Near {nearest_police[0]} ({dist_police_km:.1f} km)")
            if incident_count > 0:
                factors.append(f"{incident_count} recent safety incident(s) reported in zone")
            if hour >= 21 or hour < 5:
                factors.append(f"Late night diurnal risk factor ({hour:02d}:00 IST)")

        # Normalize category
        if risk_score < 35.0:
            risk_category = "LOW"
        elif risk_score < 65.0:
            risk_category = "MEDIUM"
        elif risk_score < 85.0:
            risk_category = "HIGH"
        else:
            risk_category = "CRITICAL"

        # Apply risk_level filter
        if isinstance(risk_level, str) and risk_level and risk_level.lower() != "all":
            if risk_category.lower() != risk_level.lower():
                continue

        zones.append({
            "zone_id": f"zone_{idx + 1}",
            "name": pt["name"],
            "latitude": round(z_lat, 6),
            "longitude": round(z_lon, 6),
            "radius_meters": round(z_rad, 1),
            "risk_score": risk_score,
            "risk_category": risk_category,
            "confidence": confidence,
            "nearest_police": nearest_police[0],
            "dist_police_km": round(dist_police_km, 2),
            "nearest_hospital": nearest_hospital[0],
            "dist_hospital_km": round(dist_hospital_km, 2),
            "incident_count": incident_count,
            "key_factors": [f for f in factors if f]
        })

    return {
        "zones": zones,
        "total_zones": len(zones),
        "center": {"latitude": latitude, "longitude": longitude},
        "radius_km": radius_km,
        "risk_level_filter": risk_level or "all"
    }


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
