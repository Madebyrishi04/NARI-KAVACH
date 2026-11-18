"""
MLDisLSTMTHREAD3: Dynamic Risk Engine with Exponential Recency Decay
Synthesizes ML model inferences with real-time urban context and crowdsourced incident feeds.
"""

import os
import json
import math
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from mldis_lstm.config import (
    MODELS_DIR, DYNAMIC_RISK_CONFIG, RISK_CATEGORIES,
    RISK_THRESHOLDS
)
from mldis_lstm.explainability import RiskExplainer


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


class DynamicRiskEngine:
    """Synthesizes dynamic risk from ML inference, street illumination, and decayed community reports."""
    def __init__(self):
        self.model_path = MODELS_DIR / "best_risk_model.joblib"
        self.preprocessor_path = MODELS_DIR / "risk_preprocessor.joblib"
        self.model = None
        self.preprocessor = None
        self.explainer = None
        self._load()

    def _load(self):
        if self.model_path.exists() and self.preprocessor_path.exists():
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
            try:
                self.explainer = RiskExplainer(model=self.model, preprocessor=self.preprocessor)
            except Exception:
                pass

    def calculate_crowdsource_risk_contribution(
        self, current_lat: float, current_lon: float, reports: list, current_timestamp_iso: str = None
    ) -> tuple[float, list]:
        if not reports:
            return 0.0, []

        now = datetime.now(timezone.utc)
        if current_timestamp_iso:
            try:
                now = datetime.fromisoformat(current_timestamp_iso.replace('Z', '+00:00'))
            except Exception:
                pass

        decay_lambda = DYNAMIC_RISK_CONFIG["decay_lambda"]
        verif_weights = DYNAMIC_RISK_CONFIG["verification_weights"]
        sev_weights = DYNAMIC_RISK_CONFIG["incident_severity_weights"]
        spatial_sigma_km = 1.2

        total_score = 0.0
        audit = []

        for rep in reports:
            rep_lat = rep.get("latitude", current_lat)
            rep_lon = rep.get("longitude", current_lon)
            rep_time_str = rep.get("timestamp")
            incident_type = rep.get("incident_type", "Suspicious_Loitering")
            verif_status = rep.get("verification_status", "unverified")

            dist_km = haversine_distance_km(current_lat, current_lon, rep_lat, rep_lon)
            if dist_km > 5.0:
                continue

            spatial_w = math.exp(-(dist_km ** 2) / (2 * (spatial_sigma_km ** 2)))

            try:
                rep_time = datetime.fromisoformat(rep_time_str.replace('Z', '+00:00'))
                delta_hours = max((now - rep_time).total_seconds() / 3600.0, 0.0)
            except Exception:
                delta_hours = 1.0

            temporal_w = math.exp(-decay_lambda * delta_hours)
            type_w = sev_weights.get(incident_type, 0.50)
            verif_w = verif_weights.get(verif_status, 0.35)

            impact = spatial_w * temporal_w * type_w * verif_w
            total_score += impact * 40.0

            audit.append({
                "incident_type": incident_type,
                "distance_km": round(dist_km, 2),
                "elapsed_hours": round(delta_hours, 2),
                "temporal_decay_factor": round(temporal_w, 3),
                "verification_status": verif_status,
                "individual_impact": round(impact, 3)
            })

        return float(min(total_score, 50.0)), audit

    def evaluate_dynamic_risk(
        self, latitude: float, longitude: float, hour: int, day_of_week: int, month: int,
        dist_police_km: float, dist_hospital_km: float, street_lighting_score: float,
        weather_condition: str = "Clear", zone_type: str = "Residential",
        historical_crime_rate: float = 0.5, historical_severity_index: float = 0.5,
        recent_reports: list = None, timestamp: str = None
    ) -> dict:
        if recent_reports is None:
            recent_reports = []

        now_iso = timestamp if timestamp else datetime.now(timezone.utc).isoformat()
        crowd_score, crowd_audit = self.calculate_crowdsource_risk_contribution(
            latitude, longitude, recent_reports, current_timestamp_iso=now_iso
        )

        feat_dict = {
            "hour": hour, "day_of_week": day_of_week, "month": month,
            "dist_police_km": dist_police_km, "dist_hospital_km": dist_hospital_km,
            "street_lighting_score": street_lighting_score,
            "recent_reports_count": len(recent_reports),
            "historical_crime_rate": historical_crime_rate,
            "historical_severity_index": historical_severity_index,
            "weather_condition": weather_condition, "zone_type": zone_type
        }

        if self.model is not None and self.preprocessor is not None:
            df_in = pd.DataFrame([feat_dict])
            X_p = self.preprocessor.transform(df_in)
            probs = self.model.predict_proba(X_p)[0]
            ml_continuous = float(probs[0] * 15.0 + probs[1] * 50.0 + probs[2] * 95.0)
            confidence = float(np.max(probs))
        else:
            ml_continuous = (historical_crime_rate * 25.0 + (1.0 - street_lighting_score) * 35.0 + min(dist_police_km / 5.0, 1.0) * 20.0)
            confidence = 0.70

        w_model = DYNAMIC_RISK_CONFIG["model_weight"]
        w_crowd = DYNAMIC_RISK_CONFIG["crowd_weight"]
        final_risk = float(np.clip((w_model * ml_continuous) + (w_crowd * (crowd_score * 2.0)), 0.0, 100.0))

        if final_risk < RISK_THRESHOLDS["LOW_MAX"]:
            category = "LOW"
        elif final_risk < RISK_THRESHOLDS["MEDIUM_MAX"]:
            category = "MEDIUM"
        else:
            category = "HIGH"

        norm_risk_thread4 = round(final_risk / 100.0, 4)

        amplifiers, mitigators = [], []
        if self.explainer is not None:
            try:
                xai_out = self.explainer.explain_instance(feat_dict, top_k=3)
                amplifiers = xai_out["top_risk_amplifying_factors"]
                mitigators = xai_out["top_risk_mitigating_factors"]
            except Exception:
                pass

        return {
            "timestamp": now_iso,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "risk_score": round(final_risk, 2),
            "risk_category": category,
            "confidence": round(confidence, 4),
            "normalized_risk_thread4": norm_risk_thread4,
            "components": {
                "ml_model_score": round(ml_continuous, 2),
                "crowdsource_report_score": round(crowd_score, 2),
                "active_reports_analyzed": len(crowd_audit)
            },
            "top_risk_amplifying_factors": amplifiers,
            "top_risk_mitigating_factors": mitigators,
            "crowdsource_recency_audit": crowd_audit
        }
