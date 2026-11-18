"""
MLDisLSTMTHREAD3: Central Configuration Module
Defines paths, seeds, hyperparameters, and domain constants for all ML/DL/NLP/XAI modules.
"""

from pathlib import Path

# Base Paths (Self-Contained inside MLDisLSTMTHREAD3)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "womenonrecord.csv"
NLP_CORPUS_PATH = DATA_DIR / "safety_nlp_corpus.csv"
POI_PATH = DATA_DIR / "delhi_safety_poi.csv"
CROWD_REPORTS_PATH = DATA_DIR / "sample_crowdsourced_reports.csv"

PROCESSED_DATA_DIR = BASE_DIR / "processed_data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Ensure all runtime output directories exist
for directory in [DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Global Reproducibility Seed
RANDOM_STATE = 42

# Risk Categories & Decision Thresholds
RISK_CATEGORIES = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH"
}

RISK_THRESHOLDS = {
    "LOW_MAX": 35.0,
    "MEDIUM_MAX": 68.0,
    "HIGH_MAX": 100.0
}

# NLP Safety Categories
NLP_CLASSES = {
    0: "Normal",
    1: "Suspicious",
    2: "Harassment",
    3: "Emergency"
}

# Spatio-Temporal Prediction Features
NUMERICAL_FEATURES = [
    "hour",
    "day_of_week",
    "month",
    "dist_police_km",
    "dist_hospital_km",
    "street_lighting_score",   # 0.0 (pitch dark) to 1.0 (well lit)
    "recent_reports_count",    # Active crowdsourced alerts count
    "historical_crime_rate",   # Extracted from NCRB womenonrecord.csv
    "historical_severity_index"# Violent vs non-violent weighted crime severity
]

CATEGORICAL_FEATURES = [
    "weather_condition",       # Clear, Rain, Fog, Storm
    "zone_type"                # Residential, Commercial, Transit_Hub, Isolated, Industrial
]

ALL_MODEL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

# Dynamic Risk & Crowdsource Recency Decay
DYNAMIC_RISK_CONFIG = {
    "decay_lambda": 0.35,      # Half-life = ln(2)/0.35 ~ 1.98 hours
    "model_weight": 0.65,      # Weight of ML model output
    "crowd_weight": 0.35,      # Weight of active crowdsourced reports
    "verification_weights": {
        "verified_official": 1.0,
        "community_confirmed": 0.70,
        "unverified": 0.35
    },
    "incident_severity_weights": {
        "SOS_Distress": 1.0,
        "Harassment_Physical": 0.85,
        "Stalking_Following": 0.70,
        "Poor_Lighting_Dark": 0.40,
        "Verbal_Abuse": 0.50,
        "Suspicious_Loitering": 0.45
    }
}

# LSTM Time-Series Forecasting Configuration
LSTM_CONFIG = {
    "sequence_length": 3,      # Window of 3 historical years to predict next
    "hidden_dim": 64,
    "num_layers": 2,
    "dropout": 0.2,
    "learning_rate": 0.005,
    "batch_size": 16,
    "epochs": 40,
    "train_split": 0.8
}

# Hugging Face DistilBERT Configuration
DISTILBERT_CONFIG = {
    "model_name": "distilbert-base-uncased",
    "max_length": 128,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "epochs": 3,
    "num_labels": 4
}

# Thread 4 Route Traversal Cost Configuration
THREAD4_ROUTING_CONFIG = {
    "beta_risk_penalty": 2.5,  # Cost = Length * (1 + beta * normalized_risk)
    "safe_corridor_bonus": 0.15 # 15% discount for well-lit corridor near police
}
