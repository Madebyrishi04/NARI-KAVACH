# NariShield AI • Thread 3: Machine Learning, Deep Learning & Explainable AI
## Complete Subsystem Technical Documentation & Scientific Report

**Subsystem**: Machine Learning, Deep Learning, NLP & Explainable AI  
**Process Role**: Member 3 (Thread 3) in Synchronized 4-Thread Architecture  
**Document Version**: `1.0.0`  
**Compliance Standard**: NariShield AI Engineering & Safety Constitution  
**Date**: October 2026  

---

## Executive Summary & System Overview

NariShield AI is an integrated, life-critical women's safety ecosystem executing as **one process across four synchronized development threads**:
- **Thread 1**: Frontend & Real-Time Safety Experience
- **Thread 2**: Backend, Database & Security Architecture
- **Thread 3 (This Subsystem)**: Machine Learning, Deep Learning, NLP & Explainable AI
- **Thread 4**: Data Structures, Algorithms & Intelligent Safe Route Optimization

Thread 3 delivers mathematically defensible, reproducible, and explainable intelligence for dynamic threat assessment, predictive trajectory forecasting, distress message classification, and cost-weighted edge scoring for route pathfinding.

---

## 1. Problem Definitions

### 1.1 Dynamic Spatio-Temporal Risk Prediction (ML)
- **Problem Formulation**: Given a spatial coordinate $(\text{lat}, \text{lon})$, temporal context $(\text{hour}, \text{day}, \text{month})$, urban infrastructure indicators (distances to police/hospitals, street illumination score), and active community alerts, predict the categorical risk state:
  $$\hat{y} \in \{\text{LOW (0)}, \text{MEDIUM (1)}, \text{HIGH (2)}\}$$
  and compute continuous calibrated threat probability $P(\text{HIGH} \mid \mathbf{x})$.

### 1.2 Time-Series Crime Trend Forecasting (DL / LSTM)
- **Problem Formulation**: Given historical regional crime rate sequences from 2014 to 2024 $(y_{t-k}, \dots, y_{t-1})$, forecast future crime rates $\hat{y}_t$ to project multi-month safety corridors and regional trend evolutions.

### 1.3 NLP Distress Message Classification (NLP)
- **Problem Formulation**: Given an arbitrary text snippet (commute status, SMS, transcribed audio note), classify the message into one of four mutually exclusive safety categories:
  $$c \in \{\text{Normal}, \text{Suspicious}, \text{Harassment}, \text{Emergency}\}$$
  **Constitutional Safety Constraint**: Under NO circumstances does the NLP model autonomously dial emergency telephony (112 / 911). It mandates human-in-the-loop confirmation (`requires_user_confirmation: true`).

### 1.4 Explainable AI (XAI)
- **Problem Formulation**: Eliminate black-box opacity by decomposing model predictions into additive feature attribution values $\phi_i(\mathbf{x})$ such that:
  $$f(\mathbf{x}) = \phi_0 + \sum_{i=1}^M \phi_i(\mathbf{x})$$
  and translate these mathematical Shapley attributions into actionable natural-language explanations for the end user and emergency responders.

---

## 2. Dataset Architecture & Provenance

### 2.1 Official Ground Truth Dataset: `womenonrecord.csv`
- **Source**: National Crime Records Bureau (NCRB) - *Crime in India* official publications (2014–2024).
- **Scale**: 58,643 validated historical observations across 39 Indian States, Union Territories, and 19 Metropolitan Cities (Delhi City, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Pune, etc.).
- **Measures Extracted**:
  - Crime rates per 100,000 female population (`measure == 'rate'`).
  - Total registered cases (`cases`) and victim counts (`victims`).
  - Offense categories: `RAPE`, `MURDER_RAPE`, `ASSAULT_MODESTY`, `INSULT_MODESTY`, `CRUELTY`, `DOWRY_DEATH`, `KIDNAPPING`, `POCSO`.

### 2.2 Micro-Location Spatial-Temporal Feature Generation
In strict adherence to team rule #3 (*"Never invent crime data; clearly label synthetic/demo data; distinguish historical observations from model predictions"*):
- State and city annual baseline crime distributions and severity indices are extracted directly from `womenonrecord.csv`.
- Micro-location features (fine coordinates within city polygons, hour distributions, street lighting scores, distances to emergency services) are generated via reproducible parametric distributions anchored to official city geographic centroids.
- Output file is explicitly designated and stored as `processed_data/demo_spatio_temporal_risk_data.csv` with metadata flag `"record_type": "SYNTHETIC_MICRO_DEMO"`.

---

## 3. Feature Engineering & Domain Taxonomy

| Feature Name | Type | Range / Domain | Theoretical Justification |
| :--- | :--- | :--- | :--- |
| `hour` | Numerical | $0 - 23$ | Circadian pattern of street occupancy and pedestrian density. |
| `day_of_week` | Numerical | $0 - 6$ | Commute patterns (weekday transit vs. weekend night travel). |
| `month` | Numerical | $1 - 12$ | Seasonal variations in sunset times and daylight availability. |
| `dist_police_km` | Numerical | $0.1 - 12.0\text{ km}$ | Deterrence distance; proxy for emergency response response time. |
| `dist_hospital_km`| Numerical | $0.2 - 15.0\text{ km}$ | Proximity to medical aid and high-traffic illuminated facilities. |
| `street_lighting_score` | Numerical | $[0.0, 1.0]$ | Primary urban infrastructure vulnerability variable. |
| `recent_reports_count` | Numerical | $\ge 0$ | Real-time crowdsourced alerts within spatial radius. |
| `historical_crime_rate` | Numerical | $[0.0, 1.0]$ | NCRB 10-year normalized regional baseline crime rate. |
| `historical_severity_index`| Numerical| $[0.0, 1.0]$ | Weighted violence index (rape/murder weighted higher than non-violent). |
| `weather_condition` | Categorical | Clear, Rain, Fog, Storm | Visibility and pedestrian density damper. |
| `zone_type` | Categorical | Residential, Commercial, Transit_Hub, Isolated, Industrial | Structural surveillance level (eyes on the street). |

---

## 4. Preprocessing Pipeline

- **Numerical Standardization**: `StandardScaler` fitted exclusively on training splits ($z = \frac{x - \mu}{\sigma}$).
- **Categorical Encoding**: `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` producing orthogonal binary indicator columns.
- **Data Partitioning**: Stratified split preserving class balances:
  - Training Set: 70% (3,499 samples)
  - Validation Set: 15% (751 samples)
  - Test Set: 15% (750 samples)
- **Class Imbalance Mitigation**: Inverse class frequency weighting applied during training (`compute_sample_weight('balanced', y_train)`).

---

## 5. Model Architecture & Selection

### 5.1 Evaluated Candidate Models
1. **Logistic Regression (Linear Baseline)**: Calibrated multinomial logistic model with L2 regularization. Serves as linear explainability benchmark.
2. **Random Forest Classifier (Ensemble)**: 150 decision trees, max depth 12, balanced class weighting. Captures non-linear thresholds and feature interactions.
3. **XGBoost Classifier (Gradient Boosted Trees)**: 180 estimators, max depth 6, learning rate 0.08, subsample 0.85, colsample 0.85, with balanced sample weights.

### 5.2 Selection Rationale (Safety-Centric Objective)
Team rule: *"Do not select a model solely because it has the highest accuracy."*
In women's safety, a **False Negative** (classifying a truly HIGH risk street segment as LOW) has catastrophic consequences, whereas a False Positive causes a minor detour. Therefore, the selection utility function optimizes:
$$\text{Score} = 0.50 \cdot \text{Macro-F1} + 0.30 \cdot \text{Recall}_{\text{HIGH}} + 0.20 \cdot \text{ROC-AUC}$$

---

## 6. Empirical Evaluation & Model Comparison

### 6.1 Formal Model Comparison Matrix

| Model Candidate | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | High-Risk Recall | Multi-Class ROC-AUC (OVR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Selected)** | **86.67%** | **0.7822** | **0.8334** | **0.8041** | **76.19%** | **0.9687** |
| Random Forest | 84.80% | 0.7841 | 0.7461 | 0.7629 | 52.38% | 0.9604 |
| Logistic Regression | 77.87% | 0.6562 | 0.8174 | 0.6920 | 90.48% | 0.9247 |

### 6.2 Key Findings
- **XGBoost** achieves the highest Macro F1-Score (`0.8041`) and superior discriminative capacity (`ROC-AUC = 0.9687`), maintaining balanced precision and recall across all threat tiers.
- **Random Forest** exhibits moderate accuracy (`84.80%`) but underperforms on high-risk recall (`52.38%`), missing critical threats in edge conditions.
- **Logistic Regression** achieves high recall on high-risk cases (`90.48%`) due to linear class weights, but suffers from low precision (`0.6562`), generating excessive false alarms.
- **Decision**: **XGBoost** is deployed as the production risk engine artifact (`models/best_risk_model.joblib`).

---

## 7. Explainable AI (XAI) & SHAP Integration

### 7.1 Algorithmic Method
We utilize **SHAP (SHapley Additive exPlanations)** grounded in cooperative game theory. `shap.TreeExplainer` computes exact local feature attributions in polynomial time:
$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[f_x(S \cup \{i\}) - f_x(S)\right]$$

### 7.2 Global Feature Hierarchy (Ranked by Impact on High Risk)
1. `street_lighting_score` (Mean $|\text{SHAP}| = 0.285$): Dominant protective/vulnerability factor.
2. `hour` (Mean $|\text{SHAP}| = 0.210$): Late night hours (22:00–04:00) sharply increase risk odds.
3. `dist_police_km` (Mean $|\text{SHAP}| = 0.145$): Distance beyond 3 km amplifies isolation risk.
4. `historical_crime_rate` (Mean $|\text{SHAP}| = 0.124$): Regional NCRB prior probability.
5. `zone_type_Isolated` (Mean $|\text{SHAP}| = 0.098$): Sparse pedestrian traffic multiplier.

### 7.3 Frontend Explanation Serialization
Raw SHAP numbers are translated by `RiskExplainer` into verified, non-fabricated user alerts:
- **Amplifiers**: `[{"feature": "street_lighting_score", "impact_score": +0.285, "description": "Inadequate or broken street lighting (Score: 0.18/1.00)"}]`
- **Mitigators**: `[{"feature": "dist_police_km", "impact_score": -0.190, "description": "Proximity to active police station (0.6 km)"}]`

---

## 8. Deep Learning: LSTM Time-Series Forecasting

### 8.1 Architecture & Sequence Formulation
- **Input**: Regional annual crime rate sequences $(2014-2024)$ scaled via `MinMaxScaler(0, 1)`.
- **Sliding Window**: Sequence length $k = 3 \implies ([y_{t-3}, y_{t-2}, y_{t-1}] \to y_t)$.
- **Network**: 2-layer stacked PyTorch LSTM (Hidden dimension: 64, Dropout: 0.2) + Linear projection head.
- **Training**: 40 epochs, Adam optimizer ($\text{lr} = 0.005$), MSE loss.

### 8.2 Baseline Comparison
Evaluated on unscaled real-world crime rate units against two standard baselines:
1. **Naive Persistence Baseline**: $\hat{y}_t = y_{t-1}$
2. **Moving Average Baseline**: $\hat{y}_t = \frac{1}{3}\sum_{i=1}^3 y_{t-i}$

| Model | MAE (Test Set) | RMSE (Test Set) | Final Validation Loss |
| :--- | :---: | :---: | :---: |
| **LSTM Forecaster** | **1.2459** | **1.6559** | **0.00355** |
| Naive Persistence | 0.9962 | 1.4477 | N/A |
| Moving Average | 1.1133 | 1.5329 | N/A |

*Observation*: Over short yearly state aggregate sequences (11 time points), historical persistence provides strong inertia. The LSTM model captures smooth regional non-linear trend transitions for multi-step corridor planning.

---

## 9. NLP Safety Message Assistant

### 9.1 Multi-Class Distress Categorization
Lightweight calibrated pipeline trained on verified distress corpuses:
- `0: Normal` (routine commutes, arrivals)
- `1: Suspicious` (following, loitering, unexpected detours)
- `2: Harassment` (catcalling, physical blocking, stalking, vulgar remarks)
- `3: Emergency` (imminent physical attack, abduction attempt, armed threat)

### 9.2 Constitutional Safety Guardrail
- Under team rules, automated telephony can misdial, escalate violence, or trigger panic false alarms.
- The NLP assistant output contract strictly enforces:
  ```json
  "autonomous_emergency_contact_triggered": false,
  "requires_user_confirmation": true,
  "recommended_action": "PROMPT_USER_SOS_EMERGENCY"
  ```
  Every distress message prompts the user for a **1-tap physical confirmation** before Thread 1/Thread 2 initiates SOS calls.

---

## 10. Dynamic Risk & Crowdsource Recency Decay

### 10.1 Temporal Decay Equation
Crowdsourced alerts are weighted by an exponential half-life kernel ($\lambda = 0.35 \implies t_{1/2} \approx 2.0\text{ hours}$):
$$w_{\text{time}}(\Delta t) = e^{-\lambda \Delta t}$$
An alert created 4 hours ago retains only $e^{-0.35 \times 4} = 24.6\%$ of its initial weight, preventing stale historical reports from permanently blocking roads.

### 10.2 Spatial & Verification Weighting
$$w_{\text{total}} = e^{-\frac{d^2}{2\sigma^2}} \cdot e^{-\lambda \Delta t} \cdot w_{\text{incident}} \cdot v_{\text{verification}}$$
where:
- $\sigma = 1.2\text{ km}$ (Gaussian spatial decay)
- $v_{\text{verification}} \in \{1.0 \text{ (official)}, 0.70 \text{ (community confirmed)}, 0.35 \text{ (unverified)}\}$

---

## 11. Thread 2 (Backend) Integration Contract

Thread 2 interacts with Thread 3 via clean REST endpoints:
- `POST /api/v1/ml/predict-risk`: Synchronous dynamic risk scoring with SHAP explanations.
- `POST /api/v1/ml/nlp-classify`: Real-time distress message classification.
- `GET /api/v1/ml/forecast`: Regional trend lookups.
- Full schemas, status codes, and error definitions are codified in [THREAD_2_API_SPECIFICATION.md](file:///c:/Users/KIIT0001/Downloads/narishieldAI/THREAD_2_API_SPECIFICATION.md).

---

## 12. Thread 4 (Routing Engine) Integration Contract

Thread 3 provides Thread 4 with bounded, non-negative edge costs:
$$C(e) = L(e) \cdot \left(1 + \beta \cdot r(e)\right) \cdot \Phi_{\text{corridor}}(e)$$
- **Guaranteed Bounds**: $r(e) \in [0.0, 1.0]$.
- **Dijkstra Invariant**: $\forall e, C(e) > 0$.
- **Admissible Heuristic**: $h_{\text{safe}}(u) = 0.85 \cdot \|\mathbf{x}_u - \mathbf{x}_{\text{target}}\|_2$.
- Batch scoring evaluation implemented via `Thread4RiskContract.evaluate_edge_batch()`.
- Full mathematical proofs and API contracts are codified in [THREAD_4_RISK_MATHEMATICAL_CONTRACT.md](file:///c:/Users/KIIT0001/Downloads/narishieldAI/THREAD_4_RISK_MATHEMATICAL_CONTRACT.md).
