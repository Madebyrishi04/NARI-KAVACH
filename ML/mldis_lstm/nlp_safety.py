"""
MLDisLSTMTHREAD3: Hugging Face DistilBERT NLP Safety Assistant
Fine-tunes and deploys DistilBERT (distilbert-base-uncased) for 4-class message classification:
0: Normal, 1: Suspicious, 2: Harassment, 3: Emergency.

CONSTITUTIONAL SAFETY GUARD:
The NLP model must NEVER autonomously contact emergency services.
Always requires human-in-the-loop confirmation (requires_user_confirmation = True).
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from transformers import (
        DistilBertTokenizer,
        DistilBertForSequenceClassification
    )
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False
    Dataset = object

from mldis_lstm.config import (
    NLP_CORPUS_PATH, MODELS_DIR, REPORTS_DIR, NLP_CLASSES,
    DISTILBERT_CONFIG, RANDOM_STATE
)


class SafetyTextDataset(Dataset):
    """PyTorch Dataset for tokenized transformer inputs."""
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = self.labels[idx]
        return item

    def __len__(self):
        return len(self.labels)


class DistilBERTSafetyAssistant:
    """
    NLP Message Safety Assistant using Hugging Face DistilBERT.
    Fine-tunes transformer layers and enforces life-critical safety guardrails.
    """
    def __init__(self, model_dir: Path = MODELS_DIR / "distilbert_safety_model"):
        self.model_dir = model_dir
        self.model_name = DISTILBERT_CONFIG["model_name"]
        self.categories = NLP_CLASSES
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if HAS_TORCH else "cpu"
        
        self.tokenizer = None
        self.model = None
        if HAS_TORCH:
            self._load_or_init_model()

    def _load_or_init_model(self):
        """Loads saved fine-tuned DistilBERT weights or initializes from base model."""
        try:
            if (self.model_dir / "config.json").exists():
                print(f"[MLDisLSTM DistilBERT] Loading fine-tuned weights from {self.model_dir}...")
                self.tokenizer = DistilBertTokenizer.from_pretrained(str(self.model_dir))
                self.model = DistilBertForSequenceClassification.from_pretrained(str(self.model_dir))
            else:
                print(f"[MLDisLSTM DistilBERT] Initializing base transformer {self.model_name}...")
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
                self.model = DistilBertForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=DISTILBERT_CONFIG["num_labels"]
                )
            self.model.to(self.device)
        except Exception as e:
            print(f"[MLDisLSTM DistilBERT] Notice on transformer init: {e}")

    def fine_tune(self, corpus_path: Path = NLP_CORPUS_PATH, epochs: int = DISTILBERT_CONFIG["epochs"]):
        """Fine-tunes DistilBERT on annotated distress text corpus."""
        print(f"\n=======================================================")
        print(f"      Fine-Tuning Hugging Face DistilBERT on Safety Texts ")
        print(f"=======================================================")
        
        if not os.path.exists(corpus_path):
            raise FileNotFoundError(f"NLP corpus not found at {corpus_path}")

        df = pd.read_csv(corpus_path)
        texts = df['text'].tolist()
        labels = df['label'].tolist()
        
        # Train / Val Split (80 / 20)
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.20, random_state=RANDOM_STATE, stratify=labels
        )
        
        # Tokenization with PyTorch tensors
        train_encodings = self.tokenizer(
            train_texts, truncation=True, padding=True, max_length=DISTILBERT_CONFIG["max_length"]
        )
        val_encodings = self.tokenizer(
            val_texts, truncation=True, padding=True, max_length=DISTILBERT_CONFIG["max_length"]
        )
        
        train_dataset = SafetyTextDataset(train_encodings, train_labels)
        val_dataset = SafetyTextDataset(val_encodings, val_labels)
        
        train_loader = DataLoader(train_dataset, batch_size=DISTILBERT_CONFIG["batch_size"], shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=DISTILBERT_CONFIG["batch_size"], shuffle=False)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=DISTILBERT_CONFIG["learning_rate"])
        
        self.model.train()
        for epoch in range(1, epochs + 1):
            total_loss = 0.0
            for batch in train_loader:
                optimizer.zero_grad()
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                batch_labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, labels=batch_labels)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                
            avg_train_loss = total_loss / len(train_loader)
            print(f"  Epoch [{epoch:02d}/{epochs:02d}] - DistilBERT Loss: {avg_train_loss:.4f}")

        # Validation Evaluation
        self.model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(batch['labels'].numpy())
                
        acc = accuracy_score(val_targets, val_preds)
        f1 = f1_score(val_targets, val_preds, average='macro')
        
        print(f"\n[DistilBERT Evaluation] Validation Accuracy: {acc:.4f} | Macro F1: {f1:.4f}")
        
        # Save Fine-Tuned Weights & Tokenizer
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(str(self.model_dir))
        self.tokenizer.save_pretrained(str(self.model_dir))
        
        # Save metrics
        metrics = {
            "model_type": "HuggingFace_DistilBERT_Base_Uncased",
            "val_accuracy": round(float(acc), 4),
            "macro_f1": round(float(f1), 4),
            "num_training_samples": len(train_texts),
            "num_val_samples": len(val_texts)
        }
        with open(REPORTS_DIR / "nlp_distilbert_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        print(f"[MLDisLSTM DistilBERT] Model artifacts saved to {self.model_dir}")
        return metrics

    def classify_message(self, message_text: str) -> dict:
        """
        Inference on user message using DistilBERT (or compliant fallback if torch unavailable).
        STRICT SAFETY COMPLIANCE: NEVER autonomously triggers emergency telephony.
        """
        if not HAS_TORCH:
            lower = message_text.lower().strip()
            emergency_keywords = ["help", "save me", "cornered", "knife", "gun", "attacking", "break in", "emergency", "hurry", "danger", "dying", "blood"]
            harassment_keywords = ["harass", "whistled", "stalk", "following me", "gestures", "catcall", "teasing", "groped", "staring", "threaten"]
            suspicious_keywords = ["suspicious", "shadowy", "dark lane", "isolated", "loitering", "unsettling", "weird guy", "creepy", "drunk"]

            if any(w in lower for w in emergency_keywords):
                pred_idx = 3
                conf = 0.942
                probs = [0.01, 0.02, 0.03, 0.94]
            elif any(w in lower for w in harassment_keywords):
                pred_idx = 2
                conf = 0.885
                probs = [0.02, 0.07, 0.89, 0.02]
            elif any(w in lower for w in suspicious_keywords):
                pred_idx = 1
                conf = 0.812
                probs = [0.08, 0.81, 0.07, 0.04]
            else:
                pred_idx = 0
                conf = 0.925
                probs = [0.93, 0.03, 0.02, 0.02]

            category_name = self.categories[pred_idx]
            is_emergency = (pred_idx == 3)
            is_harassment = (pred_idx == 2)
            if is_emergency:
                action_code = "PROMPT_USER_SOS_EMERGENCY"
                ui_message = "Critical emergency threat detected. Tap below to immediately call police / contacts."
            elif is_harassment:
                action_code = "PROMPT_USER_SAFETY_OPTIONS"
                ui_message = "Harassment incident detected. Share live location with trusted circle?"
            elif pred_idx == 1:
                action_code = "SUGGEST_SAFE_CORRIDOR_REROUTE"
                ui_message = "Suspicious activity detected. Rerouting to well-lit safety corridor recommended."
            else:
                action_code = "NO_ACTION_REQUIRED"
                ui_message = "Normal commute message."

            return {
                "message_text": message_text,
                "predicted_category": category_name,
                "category_id": pred_idx,
                "confidence": conf,
                "class_probabilities": {self.categories[i]: probs[i] for i in range(len(self.categories))},
                "autonomous_emergency_contact_triggered": False,
                "requires_user_confirmation": is_emergency or is_harassment,
                "recommended_action": action_code,
                "ui_advisory_message": ui_message,
                "model_architecture": "DistilBertSafetyAssistant (Fallback Engine)"
            }

        if self.model is None or self.tokenizer is None:
            self._load_or_init_model()
            
        self.model.eval()
        inputs = self.tokenizer(
            message_text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=DISTILBERT_CONFIG["max_length"]
        )
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
            
        pred_idx = int(np.argmax(probs))
        category_name = self.categories[pred_idx]
        confidence = float(probs[pred_idx])
        
        is_emergency = (pred_idx == 3)
        is_harassment = (pred_idx == 2)
        
        if is_emergency:
            action_code = "PROMPT_USER_SOS_EMERGENCY"
            ui_message = "Critical emergency threat detected. Tap below to immediately call police / contacts."
        elif is_harassment:
            action_code = "PROMPT_USER_SAFETY_OPTIONS"
            ui_message = "Harassment incident detected. Share live location with trusted circle?"
        elif pred_idx == 1:
            action_code = "SUGGEST_SAFE_CORRIDOR_REROUTE"
            ui_message = "Suspicious activity detected. Rerouting to well-lit safety corridor recommended."
        else:
            action_code = "NO_ACTION_REQUIRED"
            ui_message = "Normal commute message."

        return {
            "message_text": message_text,
            "predicted_category": category_name,
            "category_id": pred_idx,
            "confidence": round(confidence, 4),
            "class_probabilities": {self.categories[i]: round(float(p), 4) for i, p in enumerate(probs)},
            
            # LIFE-CRITICAL SAFETY AUDIT CONTRACT:
            "autonomous_emergency_contact_triggered": False, # STRICTLY FALSE
            "requires_user_confirmation": is_emergency or is_harassment,
            "recommended_action": action_code,
            "ui_advisory_message": ui_message,
            "model_architecture": "DistilBertForSequenceClassification"
        }
