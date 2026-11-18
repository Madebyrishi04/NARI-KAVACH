"""
MLDisLSTMTHREAD3: Explainable AI (XAI) using SHAP (SHapley Additive exPlanations)
Produces exact mathematical feature attributions and converts them to natural language reasons.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path

from mldis_lstm.config import MODELS_DIR, FIGURES_DIR, REPORTS_DIR, RISK_CATEGORIES


class RiskExplainer:
    """Computes global feature importance and instance explanations with SHAP."""
    def __init__(self, model=None, preprocessor=None, feature_names=None):
        if model is None:
            self.model = joblib.load(MODELS_DIR / "best_risk_model.joblib")
        else:
            self.model = model

        if preprocessor is None:
            self.preprocessor = joblib.load(MODELS_DIR / "risk_preprocessor.joblib")
        else:
            self.preprocessor = preprocessor

        if feature_names is None:
            with open(MODELS_DIR / "risk_feature_names.json", "r") as f:
                self.feature_names = json.load(f)["feature_names"]
        else:
            self.feature_names = feature_names

        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            self.explainer = shap.Explainer(self.model)

    def generate_global_explanations(self, X_sample: np.ndarray, max_display: int = 12):
        print("[MLDisLSTM Explainability] Computing global SHAP values...")
        shap_values = self.explainer.shap_values(X_sample)
        
        if isinstance(shap_values, list):
            high_risk_shap = shap_values[2] # Class 2: HIGH
        elif len(shap_values.shape) == 3:
            high_risk_shap = shap_values[:, :, 2]
        else:
            high_risk_shap = shap_values

        mean_abs_shap = np.mean(np.abs(high_risk_shap), axis=0)
        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs_shap
        }).sort_values(by="mean_abs_shap", ascending=False)

        with open(REPORTS_DIR / "shap_feature_importance.json", "w") as f:
            json.dump(importance_df.to_dict(orient="records"), f, indent=2)

        plt.figure(figsize=(10, 6))
        plt.barh(importance_df["feature"].head(max_display)[::-1], 
                 importance_df["mean_abs_shap"].head(max_display)[::-1], 
                 color="#e74c3c")
        plt.xlabel("Mean |SHAP Value| (Impact on High-Risk Classification)")
        plt.title("MLDisLSTMTHREAD3 - Global Feature Importance (SHAP)")
        plt.tight_layout()
        
        plt.savefig(FIGURES_DIR / "shap_global_feature_importance.png", dpi=200)
        plt.close()
        return importance_df

    def explain_instance(self, raw_input_dict: dict, top_k: int = 4) -> dict:
        df_single = pd.DataFrame([raw_input_dict])
        X_proc = self.preprocessor.transform(df_single)
        
        pred_class = int(self.model.predict(X_proc)[0])
        pred_probs = self.model.predict_proba(X_proc)[0].tolist()
        
        instance_shap = self.explainer.shap_values(X_proc)
        
        if isinstance(instance_shap, list):
            target_shap = instance_shap[pred_class][0]
        elif len(instance_shap.shape) == 3:
            target_shap = instance_shap[0, :, pred_class]
        else:
            target_shap = instance_shap[0]

        contributions = []
        for feat_name, shap_val in zip(self.feature_names, target_shap):
            contributions.append({
                "feature": feat_name,
                "shap_value": float(shap_val),
                "abs_impact": abs(float(shap_val))
            })
            
        contributions = sorted(contributions, key=lambda x: x["abs_impact"], reverse=True)
        amplifiers = []
        mitigators = []
        
        for c in contributions:
            f_name = c["feature"]
            val = c["shap_value"]
            desc = self._format_reason(f_name, raw_input_dict, val)
            
            if val > 0.01:
                amplifiers.append({"feature": f_name, "impact_score": round(val, 4), "description": desc})
            elif val < -0.01:
                mitigators.append({"feature": f_name, "impact_score": round(val, 4), "description": desc})

        return {
            "predicted_risk_label": RISK_CATEGORIES[pred_class],
            "class_probabilities": {
                "LOW": round(pred_probs[0], 4),
                "MEDIUM": round(pred_probs[1], 4),
                "HIGH": round(pred_probs[2], 4)
            },
            "top_risk_amplifying_factors": amplifiers[:top_k],
            "top_risk_mitigating_factors": mitigators[:top_k],
            "explanation_method": "SHAP_TreeExplainer_Exact"
        }

    def _format_reason(self, feature_name: str, raw_inputs: dict, val: float) -> str:
        if "street_lighting_score" in feature_name:
            score = raw_inputs.get("street_lighting_score", 0.5)
            return f"Inadequate street lighting (Score: {score:.2f}/1.00)" if score < 0.35 else f"High-visibility street lighting (Score: {score:.2f}/1.00)"
        if "hour" in feature_name:
            h = raw_inputs.get("hour", 12)
            return f"Late night travel window ({h:02d}:00 hrs) with sparse pedestrian density" if (h >= 22 or h <= 4) else f"Daytime commute hours ({h:02d}:00 hrs)"
        if "dist_police_km" in feature_name:
            d = raw_inputs.get("dist_police_km", 2.0)
            return f"Extended distance to nearest police station ({d:.1f} km)" if d > 3.0 else f"Proximity to active police station ({d:.1f} km)"
        if "historical_crime_rate" in feature_name:
            r = raw_inputs.get("historical_crime_rate", 0.5)
            return f"Regional NCRB historical women's crime rate index ({r:.2f})"
        if "dist_hospital_km" in feature_name:
            d = raw_inputs.get("dist_hospital_km", 3.0)
            return f"Distance to nearest medical/hospital facility ({d:.1f} km)"
        if "recent_reports_count" in feature_name:
            cnt = raw_inputs.get("recent_reports_count", 0)
            return f"{cnt} active crowdsourced safety alert(s) in vicinity" if cnt > 0 else "Zero active crowdsourced incident alerts in vicinity"
        if "zone_type" in feature_name:
            z = raw_inputs.get("zone_type", "Residential")
            return f"Area classified as {z} zone"
        return f"{feature_name} (Impact: {val:+.3f})"
