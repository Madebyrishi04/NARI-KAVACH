"""
MLDisLSTMTHREAD3: Master Orchestration & Training Runner
Executes complete pipeline:
1. NCRB dataset cleaning & spatio-temporal data synthesis
2. ML Risk Models (Logistic Regression, Random Forest, XGBoost) training & evaluation
3. SHAP Explainability computation & figure export
4. PyTorch LSTM Time-Series Forecaster training & loss plotting
5. Hugging Face DistilBERT Fine-Tuning & Safety Policy Assertion
6. Dynamic Risk Engine & Crowdsourced Recency Decay Test
7. Thread 4 Route Cost Traversal Test
"""

import sys
import time
from pathlib import Path

# Set up path so mldis_lstm is resolvable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mldis_lstm.config import CSV_PATH, NLP_CORPUS_PATH
from mldis_lstm.data_pipeline import (
    load_and_clean_ncrb_dataset, extract_regional_risk_profiles,
    generate_spatio_temporal_dataset, prepare_ml_data
)
from mldis_lstm.ml_risk_models import RiskModelTrainer
from mldis_lstm.explainability import RiskExplainer
from mldis_lstm.lstm_forecasting import LSTMTrainer
from mldis_lstm.nlp_safety import DistilBERTSafetyAssistant
from mldis_lstm.dynamic_risk_engine import DynamicRiskEngine
from mldis_lstm.thread4_route_contract import Thread4RiskContract


def run_full_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("       MLDisLSTMTHREAD3: COMPLETE SUBSYSTEM TRAINING & PIPELINE    ")
    print("=" * 70)

    # 1. NCRB Ingestion & Synthesis
    print("\n>>> STEP 1: Processing Official NCRB Data & Synthesizing Spatio-Temporal Data...")
    raw_df = load_and_clean_ncrb_dataset(CSV_PATH)
    profiles = extract_regional_risk_profiles(raw_df)
    demo_df = generate_spatio_temporal_dataset(n_samples=5000)
    data_bundle = prepare_ml_data(demo_df)

    # 2. ML Risk Models
    print("\n>>> STEP 2: Training & Benchmarking ML Risk Models (LogReg vs RF vs XGBoost)...")
    trainer = RiskModelTrainer(data_bundle=data_bundle)
    ml_results = trainer.train_and_evaluate()
    comp_df = trainer.get_comparison_dataframe()
    print("\n[Model Comparison Table]:")
    print(comp_df.to_string(index=False))

    # 3. Explainable AI with SHAP
    print("\n>>> STEP 3: Computing SHAP TreeExplainer Attributions...")
    explainer = RiskExplainer(
        model=trainer.best_model,
        preprocessor=data_bundle["preprocessor"],
        feature_names=data_bundle["feature_names"]
    )
    explainer.generate_global_explanations(data_bundle["X_test"][:150])

    # 4. PyTorch LSTM Forecaster
    print("\n>>> STEP 4: Training PyTorch LSTM Time-Series Forecaster...")
    lstm_trainer = LSTMTrainer(seq_len=3)
    lstm_metrics = lstm_trainer.train(epochs=35)

    # 5. Hugging Face DistilBERT Fine-Tuning
    print("\n>>> STEP 5: Fine-Tuning Hugging Face DistilBERT NLP Safety Assistant...")
    distilbert_assistant = DistilBERTSafetyAssistant()
    if Path(NLP_CORPUS_PATH).exists():
        distilbert_assistant.fine_tune(corpus_path=NLP_CORPUS_PATH, epochs=2)
    
    # Verify Safety Guardrail
    test_sos = "SOS! HELP ME PLEASE! Someone is attacking me with a knife!"
    nlp_audit = distilbert_assistant.classify_message(test_sos)
    print("\n[DistilBERT Safety Audit]:")
    print(f"  Message:             '{test_sos}'")
    print(f"  Predicted Category:  {nlp_audit['predicted_category']}")
    print(f"  Auto Dispatch Dial:  {nlp_audit['autonomous_emergency_contact_triggered']} (MUST BE FALSE)")
    print(f"  User Confirmation:   {nlp_audit['requires_user_confirmation']} (MUST BE TRUE)")
    assert nlp_audit["autonomous_emergency_contact_triggered"] is False, "Violation: Autonomous contact triggered!"

    # 6. Dynamic Risk Engine
    print("\n>>> STEP 6: Testing Dynamic Risk Engine with Crowdsourced Recency...")
    engine = DynamicRiskEngine()
    engine.model = trainer.best_model
    engine.preprocessor = data_bundle["preprocessor"]
    engine.explainer = explainer
    
    dyn_risk = engine.evaluate_dynamic_risk(
        latitude=28.6139, longitude=77.2090, hour=23, day_of_week=5, month=10,
        dist_police_km=3.5, dist_hospital_km=4.0, street_lighting_score=0.20,
        weather_condition="Clear", zone_type="Isolated",
        historical_crime_rate=0.75, historical_severity_index=0.70
    )
    print(f"Dynamic Risk: Score = {dyn_risk['risk_score']} | Category = {dyn_risk['risk_category']}")

    # 7. Thread 4 Route Cost Multiplier
    print("\n>>> STEP 7: Testing Thread 4 Route Traversal Cost Invariants...")
    edges = [
        {"edge_id": "ROAD_DARK", "length_meters": 450.0, "hour": 23, "street_lighting_score": 0.2, "dist_police_km": 3.5},
        {"edge_id": "ROAD_CORRIDOR", "length_meters": 480.0, "hour": 23, "street_lighting_score": 0.9, "dist_police_km": 0.6}
    ]
    eval_edges = Thread4RiskContract.evaluate_edge_batch(edges, dynamic_risk_engine=engine)
    for ee in eval_edges:
        print(f"  Edge: {ee['edge_id']} | Length: {ee['length_meters']}m | Cost: {ee['traversal_cost']} (x{ee['cost_multiplier']})")

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 70)
    print(f"  MLDisLSTMTHREAD3 PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s! ")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_full_pipeline()
