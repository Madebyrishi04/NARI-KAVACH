"""
MLDisLSTMTHREAD3: ML Risk Prediction Models & Rigorous Model Evaluation
Trains Logistic Regression, Random Forest, and XGBoost with balanced sample weights.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from sklearn.utils.class_weight import compute_sample_weight

from mldis_lstm.config import (
    MODELS_DIR, REPORTS_DIR, FIGURES_DIR, RANDOM_STATE, RISK_CATEGORIES
)
from mldis_lstm.data_pipeline import prepare_ml_data


class RiskModelTrainer:
    """Trains, benchmarks, and saves the best risk prediction model."""
    def __init__(self, data_bundle: dict = None):
        if data_bundle is None:
            self.data = prepare_ml_data()
        else:
            self.data = data_bundle
            
        self.X_train = self.data["X_train"]
        self.X_val = self.data["X_val"]
        self.X_test = self.data["X_test"]
        self.y_train = self.data["y_train"]
        self.y_val = self.data["y_val"]
        self.y_test = self.data["y_test"]
        self.feature_names = self.data["feature_names"]
        self.preprocessor = self.data["preprocessor"]
        
        self.sample_weights = compute_sample_weight("balanced", self.y_train)
        
        self.models = {
            "Logistic_Regression": LogisticRegression(
                max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
            ),
            "Random_Forest": RandomForestClassifier(
                n_estimators=150, max_depth=12, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
            ),
            "XGBoost": XGBClassifier(
                n_estimators=180, max_depth=6, learning_rate=0.08, eval_metric="mlogloss", random_state=RANDOM_STATE, n_jobs=-1
            )
        }
        self.results = {}
        self.best_model_name = None
        self.best_model = None

    def train_and_evaluate(self):
        print("\n[MLDisLSTM Risk Models] Training Candidate Models...")
        for name, model in self.models.items():
            print(f"  -> Fitting {name}...")
            if name == "XGBoost":
                model.fit(self.X_train, self.y_train, sample_weight=self.sample_weights)
            else:
                model.fit(self.X_train, self.y_train)
                
            y_pred = model.predict(self.X_test)
            y_prob = model.predict_proba(self.X_test)
            
            acc = accuracy_score(self.y_test, y_pred)
            p_macro = precision_score(self.y_test, y_pred, average="macro", zero_division=0)
            r_macro = recall_score(self.y_test, y_pred, average="macro", zero_division=0)
            f1_macro = f1_score(self.y_test, y_pred, average="macro", zero_division=0)
            hr_recall = recall_score(self.y_test, y_pred, labels=[2], average="macro", zero_division=0)
            roc = roc_auc_score(self.y_test, y_prob, multi_class="ovr", average="macro")
            cm = confusion_matrix(self.y_test, y_pred)
            
            self.results[name] = {
                "accuracy": round(float(acc), 4),
                "precision_macro": round(float(p_macro), 4),
                "recall_macro": round(float(r_macro), 4),
                "f1_macro": round(float(f1_macro), 4),
                "high_risk_recall": round(float(hr_recall), 4),
                "roc_auc_ovr": round(float(roc), 4),
                "confusion_matrix": cm.tolist()
            }
            self._save_confusion_matrix(cm, name)

        # Safety-centric utility score (emphasizes Macro-F1 and High-Risk Recall)
        def score(m):
            return 0.5 * m["f1_macro"] + 0.3 * m["high_risk_recall"] + 0.2 * m["roc_auc_ovr"]
            
        self.best_model_name = max(self.results.keys(), key=lambda k: score(self.results[k]))
        self.best_model = self.models[self.best_model_name]
        print(f"\n[MLDisLSTM Risk Models] Best Selected Model: {self.best_model_name}")
        self.save_artifacts()
        return self.results

    def _save_confusion_matrix(self, cm: np.ndarray, model_name: str):
        plt.figure(figsize=(6, 5))
        class_labels = [RISK_CATEGORIES[i] for i in range(len(cm))]
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_labels, yticklabels=class_labels)
        plt.title(f"Confusion Matrix - {model_name}")
        plt.xlabel("Predicted Label")
        plt.ylabel("True Label")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"confusion_matrix_{model_name.lower()}.png", dpi=200)
        plt.close()

    def get_comparison_dataframe(self) -> pd.DataFrame:
        rows = [{"Model": k, **v} for k, v in self.results.items()]
        return pd.DataFrame(rows).sort_values(by="f1_macro", ascending=False)

    def save_artifacts(self):
        joblib.dump(self.best_model, MODELS_DIR / "best_risk_model.joblib")
        joblib.dump(self.preprocessor, MODELS_DIR / "risk_preprocessor.joblib")
        
        with open(MODELS_DIR / "risk_feature_names.json", "w") as f:
            json.dump({
                "feature_names": self.feature_names,
                "best_model_name": self.best_model_name,
                "categories": RISK_CATEGORIES
            }, f, indent=2)
            
        with open(REPORTS_DIR / "ml_model_metrics.json", "w") as f:
            json.dump({
                "model_results": self.results,
                "best_model": self.best_model_name,
                "selection_criteria": "Balanced Macro-F1 + High-Risk Recall"
            }, f, indent=2)
            
        comp_df = self.get_comparison_dataframe()
        with open(REPORTS_DIR / "model_comparison_table.md", "w") as f:
            f.write("# MLDisLSTMTHREAD3 - Model Comparison\n\n")
            try:
                f.write(comp_df.to_markdown(index=False))
            except Exception:
                f.write("```\n" + comp_df.to_string(index=False) + "\n```")
            f.write(f"\n\n**Selected Model**: `{self.best_model_name}`\n")
