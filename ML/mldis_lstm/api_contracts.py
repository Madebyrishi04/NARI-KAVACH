"""
MLDisLSTMTHREAD3: Pydantic API Contracts for Thread 2 Backend & Thread 4 Route Engine
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class CrowdsourceReportItem(BaseModel):
    latitude: float
    longitude: float
    incident_type: str
    verification_status: str
    timestamp: str


class RiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    month: int = Field(..., ge=1, le=12)
    dist_police_km: float = Field(..., ge=0.0)
    dist_hospital_km: float = Field(..., ge=0.0)
    street_lighting_score: float = Field(..., ge=0.0, le=1.0)
    weather_condition: Optional[str] = "Clear"
    zone_type: Optional[str] = "Residential"
    historical_crime_rate: Optional[float] = 0.50
    historical_severity_index: Optional[float] = 0.50
    recent_reports: Optional[List[CrowdsourceReportItem]] = []
    timestamp: Optional[str] = None


class RiskPredictionResponse(BaseModel):
    timestamp: str
    coordinates: Coordinate
    risk_score: float
    risk_category: str
    confidence: float
    normalized_risk_thread4: float
    components: Dict[str, Any]
    top_risk_amplifying_factors: List[Dict[str, Any]]
    top_risk_mitigating_factors: List[Dict[str, Any]]
    crowdsource_recency_audit: List[Dict[str, Any]]


class NLPClassificationRequest(BaseModel):
    message_text: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class NLPClassificationResponse(BaseModel):
    message_text: str
    predicted_category: str
    category_id: int
    confidence: float
    class_probabilities: Dict[str, float]
    autonomous_emergency_contact_triggered: bool = False
    requires_user_confirmation: bool
    recommended_action: str
    ui_advisory_message: str
    model_architecture: str = "DistilBertForSequenceClassification"
