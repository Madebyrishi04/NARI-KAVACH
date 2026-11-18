"""
MLDisLSTMTHREAD3: Data Cleaning, NCRB Regional Prior Extraction & Spatio-Temporal Dataset Generation.
Anchored to official NCRB records in data/womenonrecord.csv.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

from mldis_lstm.config import (
    CSV_PATH, PROCESSED_DATA_DIR, RANDOM_STATE,
    NUMERICAL_FEATURES, CATEGORICAL_FEATURES, ALL_MODEL_FEATURES
)

OFFENSE_SEVERITY_WEIGHTS = {
    "RAPE": 1.0,
    "MURDER_RAPE": 1.0,
    "RAPE_VICTIMS_AGE": 1.0,
    "POCSO": 0.95,
    "ATTEMPT_RAPE": 0.85,
    "ASSAULT_MODESTY": 0.75,
    "KIDNAPPING": 0.70,
    "DOWRY_DEATH": 0.65,
    "CRUELTY": 0.55,
    "INSULT_MODESTY": 0.40,
    "OTHER": 0.35
}

METRO_CITY_COORDINATES = {
    "Delhi City": {"lat": 28.6139, "lon": 77.2090, "state_ref": "Delhi"},
    "Mumbai (Maharashtra)": {"lat": 19.0760, "lon": 72.8777, "state_ref": "Maharashtra"},
    "Bengaluru (Karnataka)": {"lat": 12.9716, "lon": 77.5946, "state_ref": "Karnataka"},
    "Chennai (Tamil Nadu)": {"lat": 13.0827, "lon": 80.2707, "state_ref": "Tamil Nadu"},
    "Hyderabad (Telangana)": {"lat": 17.3850, "lon": 78.4867, "state_ref": "Telangana"},
    "Kolkata (West Bengal)": {"lat": 22.5726, "lon": 88.3639, "state_ref": "West Bengal"},
    "Pune (Maharashtra)": {"lat": 18.5204, "lon": 73.8567, "state_ref": "Maharashtra"},
    "Jaipur (Rajasthan)": {"lat": 26.9124, "lon": 75.7873, "state_ref": "Rajasthan"}
}


def load_and_clean_ncrb_dataset(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """Loads and cleans official NCRB data, validating 2014-2024 records."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    print(f"[MLDisLSTM DataPipeline] Ingesting official NCRB dataset from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value', 'state', 'year', 'measure'])
    df['year'] = df['year'].astype(int)
    print(f"[MLDisLSTM DataPipeline] Loaded {len(df):,} validated records ({df['year'].min()}-{df['year'].max()}).")
    return df


def extract_regional_risk_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts state & city crime rates and severity indices."""
    rate_df = df[df['measure'] == 'rate'].copy()
    
    def get_severity(crime_code):
        code_str = str(crime_code).upper()
        for key, weight in OFFENSE_SEVERITY_WEIGHTS.items():
            if key in code_str:
                return weight
        return OFFENSE_SEVERITY_WEIGHTS["OTHER"]

    rate_df['severity_weight'] = rate_df['crime_code'].apply(get_severity)
    rate_df['weighted_rate'] = rate_df['value'] * rate_df['severity_weight']
    
    summary = rate_df.groupby('state').agg(
        avg_crime_rate=('value', 'mean'),
        avg_severity_weighted_rate=('weighted_rate', 'mean')
    ).reset_index()
    
    max_rate = summary['avg_crime_rate'].max()
    max_sev = summary['avg_severity_weighted_rate'].max()
    
    summary['norm_crime_rate'] = (summary['avg_crime_rate'] / max_rate).round(4)
    summary['norm_severity_index'] = (summary['avg_severity_weighted_rate'] / max_sev).round(4)
    
    out_path = PROCESSED_DATA_DIR / "ncrb_regional_profiles.csv"
    summary.to_csv(out_path, index=False)
    return summary


def generate_spatio_temporal_dataset(
    n_samples: int = 5000,
    random_state: int = RANDOM_STATE,
    output_path: Path = PROCESSED_DATA_DIR / "demo_spatio_temporal_risk_data.csv"
) -> pd.DataFrame:
    """Generates synthetic micro-location dataset rigorously anchored to NCRB priors."""
    np.random.seed(random_state)
    raw_df = load_and_clean_ncrb_dataset()
    profiles_df = extract_regional_risk_profiles(raw_df).set_index('state')
    
    cities = list(METRO_CITY_COORDINATES.keys())
    records = []
    
    # 24-hour normalized circadian probability distribution
    hour_weights = np.array([
        0.03, 0.02, 0.02, 0.02, 0.03, 0.04,
        0.04, 0.05, 0.06, 0.05, 0.04, 0.04,
        0.04, 0.04, 0.04, 0.04, 0.05, 0.05,
        0.06, 0.07, 0.07, 0.06, 0.05, 0.04
    ])
    hour_weights = hour_weights / hour_weights.sum()

    for _ in range(n_samples):
        city = np.random.choice(cities)
        city_meta = METRO_CITY_COORDINATES[city]
        state_ref = city_meta["state_ref"]
        
        lat = city_meta["lat"] + np.random.normal(0, 0.035)
        lon = city_meta["lon"] + np.random.normal(0, 0.035)
        
        hour = int(np.random.choice(24, p=hour_weights))
        day_of_week = int(np.random.randint(0, 7))
        month = int(np.random.randint(1, 13))
        
        dist_police = float(np.clip(np.random.exponential(2.2), 0.1, 12.0))
        dist_hospital = float(np.clip(np.random.exponential(3.0), 0.2, 15.0))
        
        zone = np.random.choice(["Residential", "Commercial", "Transit_Hub", "Isolated", "Industrial"], p=[0.4, 0.25, 0.15, 0.1, 0.1])
        weather = np.random.choice(["Clear", "Rain", "Fog", "Storm"], p=[0.70, 0.18, 0.08, 0.04])
        
        if hour >= 22 or hour <= 4 or zone in ["Isolated", "Industrial"]:
            lighting = float(np.clip(np.random.beta(2, 5), 0.05, 0.85))
        else:
            lighting = float(np.clip(np.random.beta(6, 2), 0.25, 0.98))
            
        reports = int(np.random.poisson(0.8 if (hour >= 20 or hour <= 4) else 0.3))
        
        if state_ref in profiles_df.index:
            hist_rate = float(profiles_df.loc[state_ref, 'norm_crime_rate'])
            hist_sev = float(profiles_df.loc[state_ref, 'norm_severity_index'])
        else:
            hist_rate = 0.50
            hist_sev = 0.50
            
        time_vuln = 0.85 if (hour >= 23 or hour <= 4) else (0.45 if hour >= 20 else 0.15)
        darkness_penalty = (1.0 - lighting) * 0.75
        infra_penalty = min(dist_police / 5.0, 1.0) * 0.40 + (0.35 if zone == "Isolated" else 0.0)
        crowd_penalty = min(reports * 0.25, 0.80)
        
        raw_risk = (
            hist_rate * 25.0 +
            hist_sev * 15.0 +
            time_vuln * 25.0 +
            darkness_penalty * 20.0 +
            infra_penalty * 15.0 +
            crowd_penalty * 15.0 +
            np.random.normal(0, 4.0)
        )
        raw_risk = float(np.clip(raw_risk, 0.0, 100.0))
        
        # Risk Categories: 0=LOW (<35), 1=MEDIUM (35-68), 2=HIGH (>=68)
        if raw_risk < 35.0:
            label = 0
        elif raw_risk < 68.0:
            label = 1
        else:
            label = 2
            
        records.append({
            "record_type": "SYNTHETIC_MICRO_DEMO",
            "city": city,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "hour": hour,
            "day_of_week": day_of_week,
            "month": month,
            "dist_police_km": round(dist_police, 2),
            "dist_hospital_km": round(dist_hospital, 2),
            "street_lighting_score": round(lighting, 3),
            "recent_reports_count": reports,
            "weather_condition": weather,
            "zone_type": zone,
            "historical_crime_rate": round(hist_rate, 4),
            "historical_severity_index": round(hist_sev, 4),
            "continuous_risk_score": round(raw_risk, 2),
            "risk_label": label
        })
        
    df_spatio = pd.DataFrame(records)
    df_spatio.to_csv(output_path, index=False)
    return df_spatio


def prepare_ml_data(df: pd.DataFrame = None):
    """Splits data into train (70%), val (15%), test (15%) and applies encoders."""
    if df is None:
        data_path = PROCESSED_DATA_DIR / "demo_spatio_temporal_risk_data.csv"
        if not os.path.exists(data_path):
            df = generate_spatio_temporal_dataset()
        else:
            df = pd.read_csv(data_path)
            
    X = df[ALL_MODEL_FEATURES].copy()
    y = df['risk_label'].values
    
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=RANDOM_STATE, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=RANDOM_STATE, stratify=y_train_val
    )
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), NUMERICAL_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES)
        ]
    )
    
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)
    
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = NUMERICAL_FEATURES + cat_feature_names
    
    return {
        "X_train": X_train_proc,
        "X_val": X_val_proc,
        "X_test": X_test_proc,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "preprocessor": preprocessor,
        "feature_names": all_feature_names
    }
