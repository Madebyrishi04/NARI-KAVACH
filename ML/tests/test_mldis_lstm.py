"""
MLDisLSTMTHREAD3 Unit Tests
Verifies normalization bounds, edge traversal cost invariants, and DistilBERT safety guardrails.
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure mldis_lstm package is resolvable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mldis_lstm.thread4_route_contract import Thread4RiskContract
from mldis_lstm.dynamic_risk_engine import DynamicRiskEngine, haversine_distance_km
from mldis_lstm.nlp_safety import DistilBERTSafetyAssistant


class TestMLDisLSTM(unittest.TestCase):

    def test_risk_normalization_bounds(self):
        """Verifies normalized risk is strictly bounded within [0.0, 1.0]."""
        test_values = [-25.0, 0.0, 35.0, 68.0, 100.0, 150.0]
        for v in test_values:
            norm = Thread4RiskContract.normalize_risk_score(v)
            self.assertGreaterEqual(norm, 0.0)
            self.assertLessEqual(norm, 1.0)

    def test_edge_cost_invariants(self):
        """Verifies traversal costs are strictly positive and honor corridor discounts."""
        length = 400.0
        low_cost = Thread4RiskContract.calculate_edge_cost(length, normalized_risk=0.1)
        high_cost = Thread4RiskContract.calculate_edge_cost(length, normalized_risk=0.8)
        self.assertGreater(low_cost, length)
        self.assertGreater(high_cost, low_cost)
        
        corridor_cost = Thread4RiskContract.calculate_edge_cost(
            length, normalized_risk=0.1, street_lighting_score=0.9, dist_police_km=0.5
        )
        self.assertLess(corridor_cost, low_cost)

    def test_haversine_distance(self):
        """Verifies spatial distance accuracy."""
        dist = haversine_distance_km(28.6315, 77.2167, 28.6129, 77.2295)
        self.assertAlmostEqual(dist, 2.4, delta=0.5)

    def test_recency_decay(self):
        """Verifies older reports decay exponentially."""
        engine = DynamicRiskEngine()
        now = datetime.now(timezone.utc)
        rep_fresh = [{"latitude": 28.6, "longitude": 77.2, "incident_type": "SOS_Distress", "verification_status": "verified_official", "timestamp": (now - timedelta(minutes=10)).isoformat()}]
        rep_stale = [{"latitude": 28.6, "longitude": 77.2, "incident_type": "SOS_Distress", "verification_status": "verified_official", "timestamp": (now - timedelta(hours=6)).isoformat()}]
        
        score_f, _ = engine.calculate_crowdsource_risk_contribution(28.6, 77.2, rep_fresh, now.isoformat())
        score_s, _ = engine.calculate_crowdsource_risk_contribution(28.6, 77.2, rep_stale, now.isoformat())
        self.assertGreater(score_f, score_s)

    def test_distilbert_safety_guardrails(self):
        """CRITICAL: Asserts autonomous contact is NEVER triggered."""
        assistant = DistilBERTSafetyAssistant()
        res = assistant.classify_message("HELP ME! Someone is attacking me with a knife!")
        self.assertFalse(res["autonomous_emergency_contact_triggered"])
        self.assertIn("requires_user_confirmation", res)


if __name__ == "__main__":
    unittest.main()
