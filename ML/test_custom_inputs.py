"""
MLDisLSTMTHREAD3: Custom Inputs Demonstration Script
Runs diverse real-world location scenarios, crowdsource recency decay, and DistilBERT messages.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mldis_lstm.dynamic_risk_engine import DynamicRiskEngine
from mldis_lstm.nlp_safety import DistilBERTSafetyAssistant


def run_custom_demo():
    engine = DynamicRiskEngine()
    nlp = DistilBERTSafetyAssistant()
    now = datetime.now(timezone.utc)

    print("=" * 70)
    print("      MLDisLSTMTHREAD3: CUSTOM SCENARIOS & DISTILBERT DEMO       ")
    print("=" * 70)

    # Custom Spatio-temporal inputs
    scenarios = [
        {
            "name": "Scenario 1: Busy Metro Transit Hub at Rush Hour (Safe)",
            "params": {
                "latitude": 28.6328, "longitude": 77.2197, "hour": 18, "day_of_week": 2, "month": 10,
                "dist_police_km": 0.3, "dist_hospital_km": 1.1, "street_lighting_score": 0.95,
                "weather_condition": "Clear", "zone_type": "Transit_Hub",
                "historical_crime_rate": 0.45, "historical_severity_index": 0.40
            }
        },
        {
            "name": "Scenario 2: Suburban Residential Road at Night (Medium Risk)",
            "params": {
                "latitude": 19.1136, "longitude": 72.8697, "hour": 21, "day_of_week": 4, "month": 10,
                "dist_police_km": 2.2, "dist_hospital_km": 3.0, "street_lighting_score": 0.50,
                "weather_condition": "Clear", "zone_type": "Residential",
                "historical_crime_rate": 0.55, "historical_severity_index": 0.50
            }
        },
        {
            "name": "Scenario 3: Dark Isolated Outskirts Under Heavy Fog at 2 AM (High Risk)",
            "params": {
                "latitude": 28.5355, "longitude": 77.3910, "hour": 2, "day_of_week": 6, "month": 12,
                "dist_police_km": 6.5, "dist_hospital_km": 8.0, "street_lighting_score": 0.10,
                "weather_condition": "Fog", "zone_type": "Isolated",
                "historical_crime_rate": 0.78, "historical_severity_index": 0.72
            }
        },
        {
            "name": "Scenario 4: Active Threat Zone with Fresh Community Alert (12 mins ago)",
            "params": {
                "latitude": 12.9716, "longitude": 77.5946, "hour": 23, "day_of_week": 5, "month": 10,
                "dist_police_km": 3.5, "dist_hospital_km": 4.0, "street_lighting_score": 0.25,
                "weather_condition": "Clear", "zone_type": "Commercial",
                "historical_crime_rate": 0.65, "historical_severity_index": 0.60,
                "recent_reports": [{
                    "latitude": 12.9718, "longitude": 77.5948, "incident_type": "Harassment_Physical",
                    "verification_status": "community_confirmed", "timestamp": (now - timedelta(minutes=12)).isoformat()
                }]
            }
        }
    ]

    print("\n--- PART A: SPATIO-TEMPORAL RISK SCENARIOS ---")
    for s in scenarios:
        res = engine.evaluate_dynamic_risk(**s["params"])
        print(f"\n[+] {s['name']}")
        print(f"    - Risk Score:         {res['risk_score']} / 100")
        print(f"    - Threat Category:     {res['risk_category']}")
        print(f"    - Thread 4 Norm Risk:  {res['normalized_risk_thread4']}")
        if res["top_risk_amplifying_factors"]:
            print(f"    - Top Risk Factor:     {res['top_risk_amplifying_factors'][0]['description']}")

    print("\n\n" + "=" * 70)
    print("--- PART B: DISTILBERT SAFETY MESSAGE TESTS ---")
    print("=" * 70)

    messages = [
        "Just reached my PG hostel, locked the gate, going to sleep now.",
        "A man has been walking behind me for 4 blocks and matching my speed.",
        "Two guys on a motorcycle are whistling and shouting abusive words at me.",
        "SOS! He is trying to break open my car door! SEND HELP IMMEDIATELY!"
    ]
    for msg in messages:
        out = nlp.classify_message(msg)
        print(f"\n[Message]: \"{msg}\"")
        print(f"  -> Predicted:          {out['predicted_category']} (Conf: {out['confidence']:.2%})")
        print(f"  -> Auto 911 Dial:      {out['autonomous_emergency_contact_triggered']} (Guaranteed FALSE)")
        print(f"  -> User Confirm Needed:{out['requires_user_confirmation']}")
        print(f"  -> Recommended Action: {out['recommended_action']}")


if __name__ == "__main__":
    run_custom_demo()
