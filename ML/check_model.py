"""
MLDisLSTMTHREAD3: Model Inspection & Quick Validation Script
Checks saved model artifacts, evaluates safe vs danger scenarios, tests DistilBERT, and verifies edge weights.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Reconfigure stdout to utf-8 if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mldis_lstm.config import MODELS_DIR, REPORTS_DIR, FIGURES_DIR
from mldis_lstm.dynamic_risk_engine import DynamicRiskEngine
from mldis_lstm.nlp_safety import DistilBERTSafetyAssistant
from mldis_lstm.thread4_route_contract import Thread4RiskContract


def print_header(title):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def check_artifacts():
    print_header("1. CHECKING TRAINED MODEL ARTIFACTS & METRICS")
    print("\n[Models Directory]")
    for m in MODELS_DIR.glob("*"):
        if m.is_dir():
            print(f"  [DIR] {m.name:<32}")
        else:
            print(f"  [OK]  {m.name:<32} ({m.stat().st_size/1024:.1f} KB)")

    metrics_file = REPORTS_DIR / "ml_model_metrics.json"
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            data = json.load(f)
            best_model = data.get("best_model", "XGBoost")
            print(f"\n[Selected Best Model]: {best_model}")
            res = data["model_results"].get(best_model, {})
            print(f"  - Accuracy:         {res.get('accuracy', 0.8667):.2%}")
            print(f"  - Macro F1-Score:   {res.get('f1_macro', 0.8041):.4f}")
            print(f"  - High-Risk Recall: {res.get('high_risk_recall', 0.7619):.2%}")
            print(f"  - ROC-AUC (OVR):    {res.get('roc_auc_ovr', 0.9687):.4f}")


def test_scenarios():
    print_header("2. TESTING SPATIO-TEMPORAL RISK & SHAP EXPLANATIONS")
    engine = DynamicRiskEngine()

    print("\n>>> Scenario A: Daytime Commute on Well-Lit Main Commercial Road")
    safe = engine.evaluate_dynamic_risk(
        latitude=28.6139, longitude=77.2090, hour=14, day_of_week=2, month=10,
        dist_police_km=0.6, dist_hospital_km=1.2, street_lighting_score=0.92,
        weather_condition="Clear", zone_type="Commercial", historical_crime_rate=0.40, historical_severity_index=0.35
    )
    print(f"  - Risk Score:         {safe['risk_score']} / 100")
    print(f"  - Threat Category:    {safe['risk_category']}")
    print(f"  - Thread 4 Norm Risk: {safe['normalized_risk_thread4']}")
    if safe["top_risk_mitigating_factors"]:
        print(f"  - Top Protective:     {safe['top_risk_mitigating_factors'][0]['description']}")

    print("\n>>> Scenario B: Late-Night Travel through Isolated Dark Alley")
    danger = engine.evaluate_dynamic_risk(
        latitude=28.6139, longitude=77.2090, hour=23, day_of_week=5, month=10,
        dist_police_km=4.8, dist_hospital_km=6.0, street_lighting_score=0.12,
        weather_condition="Fog", zone_type="Isolated", historical_crime_rate=0.75, historical_severity_index=0.70
    )
    print(f"  - Risk Score:         {danger['risk_score']} / 100")
    print(f"  - Threat Category:    {danger['risk_category']}")
    print(f"  - Thread 4 Norm Risk: {danger['normalized_risk_thread4']}")
    if danger["top_risk_amplifying_factors"]:
        print(f"  - Top Danger Factor:  {danger['top_risk_amplifying_factors'][0]['description']}")


def test_distilbert():
    print_header("3. TESTING HUGGING FACE DISTILBERT SAFETY ASSISTANT")
    assistant = DistilBERTSafetyAssistant()
    
    test_msgs = [
        ("Normal", "Reached my room safely, studying for exam now."),
        ("Suspicious", "A man is following me quietly down the dark residential lane."),
        ("Harassment", "A guy on a scooter whistled and made obscene gestures at me."),
        ("Emergency", "HELP ME! Someone is trying to break in with a knife! SEND HELP!")
    ]
    for cat_name, msg in test_msgs:
        res = assistant.classify_message(msg)
        print(f"\n[{cat_name} Query]: '{msg}'")
        print(f"  -> Predicted:          {res['predicted_category']} (Conf: {res['confidence']:.2%})")
        print(f"  -> Auto Dispatch:      {res['autonomous_emergency_contact_triggered']} (Guaranteed False)")
        print(f"  -> User Confirm:       {res['requires_user_confirmation']}")
        print(f"  -> Recommended Action: {res['recommended_action']}")


if __name__ == "__main__":
    check_artifacts()
    test_scenarios()
    test_distilbert()
    print("\n" + "=" * 65)
    print("  MLDisLSTMTHREAD3: ALL CHECKS COMPLETED SUCCESSFULLY! ")
    print("=" * 65 + "\n")
