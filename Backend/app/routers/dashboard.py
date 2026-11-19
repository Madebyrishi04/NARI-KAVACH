"""
Router for Live & Dynamic Personal Safety Dashboard.
Aggregates real-time risk scores, diurnal predictive forecasting,
nearest emergency facilities, active journeys, and user activities.
"""

import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.emergency_contact import EmergencyContact
from app.models.emergency_alert import EmergencyAlert
from app.models.safety_report import SafetyReport
from app.models.journey import SafetyJourney
from app.models.location import UserLocation

router = APIRouter(
    prefix="/dashboard",
    tags=["Live Dashboard"]
)

# Verified Emergency Facilities (Bhubaneswar and Major Hubs)
POLICE_FACILITIES = [
    ("Infocity Police Station", 20.3524, 85.8082),
    ("Chandrasekharpur Police Station", 20.3275, 85.8195),
    ("Nayapalli Police Station", 20.2970, 85.8170),
    ("Saheed Nagar Police Station", 20.2880, 85.8450),
    ("Capital Police Station", 20.2685, 85.8385),
    ("Khandagiri Police Station", 20.2600, 85.7865),
    ("Parliament Street Police Station", 28.6256, 77.2144),
    ("Connaught Place Police Station", 28.6328, 77.2197),
    ("Hauz Khas Police Station", 28.5494, 77.2001),
]

HOSPITAL_FACILITIES = [
    ("KIMS Super Speciality Hospital", 20.3520, 85.8175),
    ("Care Hospital Chandrasekharpur", 20.3160, 85.8210),
    ("Apollo Hospital Bhubaneswar", 20.3060, 85.8350),
    ("Capital Hospital Bhubaneswar", 20.2630, 85.8240),
    ("AIIMS Bhubaneswar", 20.2285, 85.7765),
    ("AIIMS Delhi Hospital", 28.5672, 77.2100),
    ("Safdarjung Hospital", 28.5700, 77.2070),
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _find_nearest(lat: float, lon: float, facilities: List[tuple]) -> Dict[str, Any]:
    nearest = min(facilities, key=lambda f: _haversine_km(lat, lon, f[1], f[2]))
    dist = _haversine_km(lat, lon, nearest[1], nearest[2])
    dist_str = f"{int(round(dist * 1000))} m" if dist < 1.0 else f"{dist:.1f} km"
    return {
        "name": nearest[0],
        "latitude": nearest[1],
        "longitude": nearest[2],
        "distance_km": round(dist, 2),
        "distance": dist_str
    }


def _calculate_dynamic_risk(lat: float, lon: float, hour: int, incident_count: int, dist_police_km: float) -> Dict[str, Any]:
    """Computes genuine multi-factor dynamic risk score for current time & location."""
    # 1. Diurnal base risk by hour
    if 6 <= hour <= 11:
        base = 14.0 + (hour - 6) * 1.5
    elif 12 <= hour <= 16:
        base = 18.0 + (hour - 12) * 1.8
    elif 17 <= hour <= 20:
        base = 28.0 + (hour - 17) * 4.5
    elif 21 <= hour <= 23:
        base = 45.0 + (hour - 21) * 7.5
    else:  # 00:00 to 05:00
        base = 65.0 - (hour * 4.0) if hour <= 4 else 38.0

    # 2. Police proximity adjustment (-10% if < 1.5km, +15% if > 3km)
    if dist_police_km < 1.5:
        base -= 5.0
    elif dist_police_km > 3.0:
        base += 8.0

    # 3. Local incident density adjustment
    base += min(25.0, incident_count * 6.0)

    score = int(round(min(100.0, max(5.0, base))))
    if score < 35:
        level = "LOW"
        color = "low"
        desc = "Daytime visibility with low historical incident density."
    elif score < 70:
        level = "MEDIUM"
        color = "medium"
        desc = "Moderate activity area. Exercise standard situational awareness."
    else:
        level = "HIGH"
        color = "high"
        desc = "Heightened risk window. Recommended to stay in well-lit public corridors."

    return {
        "score": score,
        "level": level,
        "color": color,
        "description": desc
    }


def _generate_prediction_curve(curr_hour: int, current_risk_score: int) -> Dict[str, Any]:
    """Generates next 5-hour predictive risk timeline and responsive SVG points."""
    steps = 5
    labels = []
    scores = []
    points = []

    ratio = max(0.5, current_risk_score / 25.0)

    for i in range(steps):
        h = (curr_hour + i) % 24
        if 6 <= h <= 11:
            hr = 14.0 + (h - 6) * 1.5
        elif 12 <= h <= 16:
            hr = 18.0 + (h - 12) * 1.8
        elif 17 <= h <= 20:
            hr = 28.0 + (h - 17) * 4.5
        elif 21 <= h <= 23:
            hr = 45.0 + (h - 21) * 7.5
        else:
            hr = 65.0 - (h * 4.0) if h <= 4 else 38.0

        val = int(round(min(100.0, max(5.0, hr * ratio))))
        am_pm = "am" if h < 12 else "pm"
        disp_h = 12 if h % 12 == 0 else h % 12
        labels.append(f"{disp_h}{am_pm}")
        scores.append(val)

        x = int(round((i / (steps - 1)) * 700))
        y = int(round(155 - (val / 100.0) * 125))
        points.append(f"{x},{y}")

    peak_idx = scores.index(max(scores))
    trend = "INCREASING" if scores[-1] > scores[0] else ("DECREASING" if scores[-1] < scores[0] else "STABLE")

    return {
        "labels": labels,
        "scores": scores,
        "svg_points": " ".join(points),
        "peak_hour": labels[peak_idx],
        "trend": trend
    }


@router.get("/live")
def get_live_dashboard(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Live, dynamic dashboard feed returning real-time risk status, 5-hour diurnal
    predictive forecast, nearby emergency facilities, live routes, and recent activity.
    """
    # 1. User Profile
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.full_name if user else "Safety User"

    # 2. Determine User Coordinates
    if latitude is not None and longitude is not None:
        curr_lat, curr_lon = float(latitude), float(longitude)
    else:
        latest_loc = db.query(UserLocation).filter(
            UserLocation.user_id == user_id
        ).order_by(UserLocation.recorded_at.desc()).first()
        if latest_loc:
            curr_lat, curr_lon = float(latest_loc.latitude), float(latest_loc.longitude)
        else:
            # Operational center default: KIIT Campus 6, Bhubaneswar
            curr_lat, curr_lon = 20.354563, 85.816109

    # 3. Nearby Facilities
    nearest_police = _find_nearest(curr_lat, curr_lon, POLICE_FACILITIES)
    nearest_hospital = _find_nearest(curr_lat, curr_lon, HOSPITAL_FACILITIES)

    # 4. Count Local Incidents (within 2 km)
    local_incidents = 0
    try:
        reports = db.query(SafetyReport).all()
        for r in reports:
            if hasattr(r, "latitude") and hasattr(r, "longitude") and r.latitude and r.longitude:
                if _haversine_km(curr_lat, curr_lon, float(r.latitude), float(r.longitude)) <= 2.0:
                    local_incidents += 1
    except Exception:
        local_incidents = 0

    # 5. Dynamic Risk & 5-Hour Forecast
    now = datetime.now()
    current_hour = now.hour
    risk_info = _calculate_dynamic_risk(
        curr_lat, curr_lon, current_hour, local_incidents, nearest_police["distance_km"]
    )
    prediction_info = _generate_prediction_curve(current_hour, risk_info["score"])

    # 6. Trusted Contacts Count
    try:
        trusted_count = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).count()
    except Exception:
        trusted_count = 0

    # 7. Recommended Live Route (check active journey or provide default corridor)
    active_journey = db.query(SafetyJourney).filter(
        SafetyJourney.user_id == user_id,
        SafetyJourney.status == "active"
    ).order_by(SafetyJourney.started_at.desc()).first()

    if active_journey:
        rec_route = {
            "title": "Active Safety Journey",
            "source": f"{active_journey.source_latitude:.4f}, {active_journey.source_longitude:.4f}",
            "destination": f"{active_journey.destination_latitude:.4f}, {active_journey.destination_longitude:.4f}",
            "distance": "In Progress",
            "duration": "Live Monitored",
            "risk_score": risk_info["score"],
            "risk_level": risk_info["level"],
            "color": risk_info["color"],
            "is_active": True,
            "journey_id": active_journey.id
        }
    else:
        rec_route = {
            "title": "KIIT Campus 6 → Patia Chowk",
            "source": "KIIT Campus 6 (Bhubaneswar)",
            "destination": "Patia Chowk",
            "distance": "1.4 km",
            "duration": "3 min",
            "risk_score": min(risk_info["score"], 22),
            "risk_level": "LOW",
            "color": "low",
            "is_active": False
        }

    # 8. Recent Activity Stream
    activities = []
    try:
        alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.user_id == user_id
        ).order_by(EmergencyAlert.triggered_at.desc()).limit(3).all()
        for a in alerts:
            t = a.triggered_at.isoformat() if a.triggered_at else now.isoformat()
            activities.append({
                "id": f"sos-{a.id}",
                "title": "🚨 SOS Alert Recorded",
                "description": f"Status: {a.status or 'Recorded'}",
                "time": t,
                "type": "sos"
            })
    except Exception:
        pass

    try:
        user_reports = db.query(SafetyReport).filter(
            SafetyReport.user_id == user_id
        ).order_by(SafetyReport.created_at.desc()).limit(3).all()
        for rep in user_reports:
            t = rep.created_at.isoformat() if rep.created_at else now.isoformat()
            activities.append({
                "id": f"report-{rep.id}",
                "title": "📝 Safety Report Submitted",
                "description": rep.description or "Community safety observation logged.",
                "time": t,
                "type": "report"
            })
    except Exception:
        pass

    activities.sort(key=lambda x: x["time"], reverse=True)

    return {
        "user_name": user_name,
        "coordinates": {"latitude": curr_lat, "longitude": curr_lon},
        "current_risk": risk_info,
        "prediction": prediction_info,
        "recommended_route": rec_route,
        "nearby_services": {
            "police_station": nearest_police,
            "hospital": nearest_hospital,
            "trusted_contacts_count": trusted_count
        },
        "recent_activity": activities[:4],
        "timestamp": now.isoformat()
    }
