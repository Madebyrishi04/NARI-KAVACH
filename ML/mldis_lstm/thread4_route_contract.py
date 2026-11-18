"""
MLDisLSTMTHREAD3: Thread 4 Route Optimization Mathematical Contract
Guarantees bounded normalized risk and calculates safe graph traversal edge costs.
"""

import math
import numpy as np
from typing import List, Dict, Any

from mldis_lstm.config import THREAD4_ROUTING_CONFIG


class Thread4RiskContract:
    @staticmethod
    def normalize_risk_score(raw_risk_score: float) -> float:
        """Guarantees strict normalization into [0.0, 1.0]."""
        return round(float(np.clip(raw_risk_score / 100.0, 0.0, 1.0)), 4)

    @staticmethod
    def calculate_edge_cost(
        length_meters: float,
        normalized_risk: float,
        beta: float = THREAD4_ROUTING_CONFIG["beta_risk_penalty"],
        street_lighting_score: float = 0.5,
        dist_police_km: float = 2.0
    ) -> float:
        """
        Cost(e) = Length(e) * (1 + beta * NormalizedRisk(e)) * CorridorModifier
        Invariant: Cost(e) > 0 for all edges (No negative cycles).
        """
        if length_meters <= 0:
            raise ValueError("Edge length must be strictly positive.")

        cost = length_meters * (1.0 + (beta * normalized_risk))
        if street_lighting_score >= 0.80 and dist_police_km <= 1.0:
            cost *= (1.0 - THREAD4_ROUTING_CONFIG["safe_corridor_bonus"])
        return round(cost, 2)

    @staticmethod
    def evaluate_edge_batch(
        edges: List[Dict[str, Any]],
        dynamic_risk_engine = None,
        beta: float = THREAD4_ROUTING_CONFIG["beta_risk_penalty"]
    ) -> List[Dict[str, Any]]:
        results = []
        for e in edges:
            length = e.get("length_meters", 100.0)
            lighting = e.get("street_lighting_score", 0.5)
            police = e.get("dist_police_km", 2.0)
            
            if dynamic_risk_engine is not None:
                risk_eval = dynamic_risk_engine.evaluate_dynamic_risk(
                    latitude=e.get("midpoint_lat", 28.6139),
                    longitude=e.get("midpoint_lon", 77.2090),
                    hour=e.get("hour", 21),
                    day_of_week=e.get("day_of_week", 5),
                    month=e.get("month", 10),
                    dist_police_km=police,
                    dist_hospital_km=e.get("dist_hospital_km", 3.0),
                    street_lighting_score=lighting,
                    weather_condition=e.get("weather_condition", "Clear"),
                    zone_type=e.get("zone_type", "Residential"),
                    recent_reports=e.get("recent_reports", [])
                )
                raw_score = risk_eval["risk_score"]
                norm_risk = Thread4RiskContract.normalize_risk_score(raw_score)
                cat = risk_eval["risk_category"]
            else:
                norm_risk = float(np.clip((1.0 - lighting) * 0.6 + min(police / 5.0, 1.0) * 0.4, 0.0, 1.0))
                raw_score = norm_risk * 100.0
                cat = "HIGH" if norm_risk > 0.65 else ("MEDIUM" if norm_risk > 0.35 else "LOW")

            cost = Thread4RiskContract.calculate_edge_cost(
                length_meters=length,
                normalized_risk=norm_risk,
                beta=beta,
                street_lighting_score=lighting,
                dist_police_km=police
            )

            results.append({
                "edge_id": e.get("edge_id"),
                "length_meters": length,
                "raw_risk_score": round(raw_score, 2),
                "normalized_risk": norm_risk,
                "risk_category": cat,
                "traversal_cost": cost,
                "cost_multiplier": round(cost / length, 3)
            })
        return results
