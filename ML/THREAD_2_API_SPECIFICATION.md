# NariShield AI • Inter-Thread Specification
# Thread 3 (ML/DL/XAI) → Thread 2 (Backend, Database & Security) API Specification

**Document Version**: `1.0.0`  
**Status**: `FINAL_APPROVED`  
**Author**: Thread 3 (Machine Learning, Deep Learning & Explainable AI)  
**Consumer**: Thread 2 (Backend & Security Architecture)  
**Protocol**: REST / HTTP JSON  
**Base URL**: `/api/v1/ml`

---

## 1. Overview & Service Responsibility

Thread 3 hosts the intelligence engine for NariShield AI. Thread 2 acts as the orchestration layer: validating user identity, retrieving historical database contexts, passing sanitized payloads to Thread 3 endpoints, and storing prediction logs securely.

### Thread 3 Guarantees:
1. **Deterministic Latency**: Sub-50ms inference for tree models and cached neural embeddings.
2. **Zero Autonomous Dispatch**: The NLP safety classifier will **never** directly invoke emergency telephony or push external SMS to 112/911. It flags severe inputs with `requires_user_confirmation: true`, returning control to Thread 2 & Thread 1 for user interaction.
3. **Reproducibility**: All models are versioned with pre-fitted encoders and fixed seeds.

---

## 2. API Endpoints

### 2.1 Dynamic Risk Evaluation
- **Endpoint**: `POST /api/v1/ml/predict-risk`
- **Purpose**: Computes current composite risk score, risk category, model certainty, SHAP feature attributions, and recency-decayed crowdsourced impacts.

#### Request Body Schema (`application/json`):
```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "hour": 23,
  "day_of_week": 5,
  "month": 10,
  "dist_police_km": 3.8,
  "dist_hospital_km": 4.5,
  "street_lighting_score": 0.20,
  "weather_condition": "Clear",
  "zone_type": "Isolated",
  "historical_crime_rate": 0.75,
  "historical_severity_index": 0.70,
  "recent_reports": [
    {
      "latitude": 28.6145,
      "longitude": 77.2095,
      "incident_type": "Poor_Lighting_Dark",
      "verification_status": "unverified",
      "timestamp": "2026-10-29T11:45:00Z"
    },
    {
      "latitude": 28.6130,
      "longitude": 77.2080,
      "incident_type": "Stalking_Following",
      "verification_status": "community_confirmed",
      "timestamp": "2026-10-29T09:30:00Z"
    }
  ],
  "timestamp": "2026-10-29T12:00:00Z"
}
```

#### Response Body Schema (`200 OK`):
```json
{
  "timestamp": "2026-10-29T12:00:00Z",
  "coordinates": {
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "risk_score": 74.82,
  "risk_category": "HIGH",
  "confidence": 0.8845,
  "normalized_risk_thread4": 0.7482,
  "components": {
    "ml_model_score": 68.40,
    "crowdsource_report_score": 18.25,
    "active_reports_analyzed": 2
  },
  "top_risk_amplifying_factors": [
    {
      "feature": "street_lighting_score",
      "impact_score": 0.285,
      "description": "Inadequate or broken street lighting (Score: 0.20/1.00)"
    },
    {
      "feature": "hour",
      "impact_score": 0.210,
      "description": "Late night travel window (23:00 hrs) with lower pedestrian density"
    },
    {
      "feature": "dist_police_km",
      "impact_score": 0.145,
      "description": "Extended distance to nearest police station (3.8 km)"
    }
  ],
  "top_risk_mitigating_factors": [],
  "crowdsource_recency_audit": [
    {
      "incident_type": "Poor_Lighting_Dark",
      "distance_km": 0.08,
      "elapsed_hours": 0.25,
      "temporal_decay_factor": 0.916,
      "verification_status": "unverified",
      "individual_impact": 0.321
    }
  ],
  "metadata": {
    "version": "1.0.0",
    "historical_data_source": "National Crime Records Bureau (womenonrecord.csv)",
    "recency_half_life_hours": 1.98
  }
}
```

---

### 2.2 NLP Safety Message Classification
- **Endpoint**: `POST /api/v1/ml/nlp-classify`
- **Purpose**: Real-time classification of user messages, emergency voice transcripts, or distress notes into 4 standardized safety categories.

#### Request Body Schema (`application/json`):
```json
{
  "message_text": "HELP ME! A guy has cornered me near the subway exit!",
  "user_id": "usr_99824",
  "session_id": "sess_88192"
}
```

#### Response Body Schema (`200 OK`):
```json
{
  "message_text": "HELP ME! A guy has cornered me near the subway exit!",
  "predicted_category": "Emergency",
  "category_id": 3,
  "confidence": 0.9412,
  "class_probabilities": {
    "Normal": 0.0081,
    "Suspicious": 0.0245,
    "Harassment": 0.0262,
    "Emergency": 0.9412
  },
  "autonomous_emergency_contact_triggered": false,
  "requires_user_confirmation": true,
  "recommended_action": "PROMPT_USER_SOS_EMERGENCY",
  "ui_advisory_message": "Critical emergency threat detected. Tap below to immediately call police / contacts.",
  "safety_policy_statement": "System strictly prohibits autonomous dispatch. User confirmation is mandatory."
}
```

---

### 2.3 Regional Time-Series Forecasting
- **Endpoint**: `GET /api/v1/ml/forecast?region=Delhi%20City&steps=3`
- **Purpose**: Retrieves LSTM multi-year crime rate forecasts for regional risk projection.

#### Response Body Schema (`200 OK`):
```json
{
  "region_or_state": "Delhi City",
  "forecast_horizon_years": 3,
  "projected_crime_rates": [14.82, 14.21, 13.90],
  "projected_risk_trend": "DECREASING",
  "model_mae": 0.0384,
  "model_rmse": 0.0512,
  "baseline_comparison": {
    "lstm_mae": 0.0384,
    "naive_mae": 0.0521,
    "improvement_pct": 26.3
  }
}
```

---

### 2.4 Batch Waypoint Risk (Pass-Through to Route Engine)
- **Endpoint**: `POST /api/v1/ml/batch-waypoint-risk`
- **Purpose**: Evaluates road graph vertices or route waypoints in bulk for route engine integration.
- **Latency Target**: < 30ms for 500 waypoints.

---

## 3. Error Codes & Handling Contract

| HTTP Status | Error Code | Description | Action Required by Thread 2 |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | `INVALID_COORDINATES` | Latitude or longitude out of geographic bounds `[-90, 90]` or `[-180, 180]`. | Reject user input, log validation failure. |
| `400 Bad Request` | `INVALID_FEATURE_RANGE` | Lighting score not in `[0.0, 1.0]`, hour not in `[0, 23]`. | Validate with Pydantic prior to dispatch. |
| `422 Unprocessable`| `EMPTY_TEXT_MESSAGE` | NLP message string is empty or whitespace. | Return validation notice to Thread 1. |
| `500 Server Error` | `MODEL_INFERENCE_ERROR`| Exception during matrix computation or feature encoding. | Fallback to heuristic risk formula; log error. |

---

## 4. Security & Cryptographic Integrity

1. **No Personally Identifiable Information (PII)**:
   - Features passed to Thread 3 must be anonymized coordinates and timestamps. User names, phone numbers, and addresses must never enter the feature vector.
2. **Data Tampering Prevention**:
   - NCRB baseline data checksum is cryptographically verified against SHA-256 hashes recorded in `womenonrecord.csv`.
3. **Crowdsource Report Spam Throttling**:
   - Thread 2 must enforce rate limiting (max 3 reports per user per 30 minutes) to prevent adversarial poisoning of the dynamic risk engine.
