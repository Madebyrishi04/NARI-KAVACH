"""
MLDisLSTMTHREAD3: LSTM Time-Series Crime Trend Forecaster
2-Layer PyTorch LSTM trained on 2014-2024 regional NCRB sequences.
Evaluated against Naive Persistence and Moving Average baselines.
"""

import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

from mldis_lstm.config import (
    CSV_PATH, MODELS_DIR, REPORTS_DIR, FIGURES_DIR, LSTM_CONFIG, RANDOM_STATE
)
from mldis_lstm.data_pipeline import load_and_clean_ncrb_dataset

torch.manual_seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


class TimeSeriesDataset(Dataset):
    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        self.X = torch.tensor(sequences, dtype=torch.float32)
        self.y = torch.tensor(targets, dtype=torch.float32).unsqueeze(-1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMForecaster(nn.Module):
    def __init__(self, input_dim: int = 1, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMForecaster, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])


class LSTMTrainer:
    def __init__(self, seq_len: int = LSTM_CONFIG["sequence_length"]):
        self.seq_len = seq_len
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        raw_df = load_and_clean_ncrb_dataset()
        rate_df = raw_df[raw_df['measure'] == 'rate'].copy()
        pivot_df = rate_df.pivot_table(index='state', columns='year', values='value', aggfunc='mean')
        pivot_df = pivot_df.interpolate(axis=1, limit_direction='both').fillna(0)
        
        trajectories = pivot_df.values
        flat_data = trajectories.reshape(-1, 1)
        self.scaler.fit(flat_data)
        scaled_trajectories = self.scaler.transform(flat_data).reshape(trajectories.shape)
        
        X_list, y_list = [], []
        for row in scaled_trajectories:
            for i in range(len(row) - seq_len):
                X_list.append(row[i:i + seq_len])
                y_list.append(row[i + seq_len])
                
        X = np.array(X_list)[:, :, np.newaxis]
        y = np.array(y_list)
        
        n_train = int(len(X) * LSTM_CONFIG["train_split"])
        indices = np.arange(len(X))
        np.random.shuffle(indices)
        
        self.X_train, self.y_train = X[indices[:n_train]], y[indices[:n_train]]
        self.X_test, self.y_test = X[indices[n_train:]], y[indices[n_train:]]
        
        self.train_dataset = TimeSeriesDataset(self.X_train, self.y_train)
        self.test_dataset = TimeSeriesDataset(self.X_test, self.y_test)
        
        self.train_loader = DataLoader(self.train_dataset, batch_size=LSTM_CONFIG["batch_size"], shuffle=True)
        self.test_loader = DataLoader(self.test_dataset, batch_size=LSTM_CONFIG["batch_size"], shuffle=False)
        
        self.model = LSTMForecaster(
            input_dim=1,
            hidden_dim=LSTM_CONFIG["hidden_dim"],
            num_layers=LSTM_CONFIG["num_layers"],
            dropout=LSTM_CONFIG["dropout"]
        )
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=LSTM_CONFIG["learning_rate"])
        self.train_losses, self.val_losses = [], []
        self.metrics = {}

    def train(self, epochs: int = LSTM_CONFIG["epochs"]):
        print("\n[MLDisLSTM LSTM Forecaster] Training PyTorch LSTM Model...")
        for epoch in range(1, epochs + 1):
            self.model.train()
            running_loss = 0.0
            for batch_x, batch_y in self.train_loader:
                self.optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = self.criterion(pred, batch_y)
                loss.backward()
                self.optimizer.step()
                running_loss += loss.item() * len(batch_x)
                
            train_loss = running_loss / len(self.train_dataset)
            self.train_losses.append(train_loss)
            
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_x, batch_y in self.test_loader:
                    pred = self.model(batch_x)
                    loss = self.criterion(pred, batch_y)
                    val_loss += loss.item() * len(batch_x)
            val_loss = val_loss / len(self.test_dataset)
            self.val_losses.append(val_loss)
            
            if epoch % 10 == 0 or epoch == epochs:
                print(f"  Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")

        self._evaluate()
        self._plot_loss()
        self._save()
        return self.metrics

    def _evaluate(self):
        self.model.eval()
        with torch.no_grad():
            preds_scaled = self.model(torch.tensor(self.X_test, dtype=torch.float32)).numpy()
            
        y_true = self.scaler.inverse_transform(self.y_test.reshape(-1, 1)).ravel()
        y_pred = self.scaler.inverse_transform(preds_scaled).ravel()
        y_naive = self.scaler.inverse_transform(self.X_test[:, -1, 0].reshape(-1, 1)).ravel()
        y_ma = self.scaler.inverse_transform(np.mean(self.X_test[:, :, 0], axis=1).reshape(-1, 1)).ravel()
        
        self.metrics = {
            "LSTM": {
                "MAE": round(float(mean_absolute_error(y_true, y_pred)), 4),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4)
            },
            "Naive_Persistence": {
                "MAE": round(float(mean_absolute_error(y_true, y_naive)), 4),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_naive))), 4)
            },
            "Moving_Average": {
                "MAE": round(float(mean_absolute_error(y_true, y_ma)), 4),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_ma))), 4)
            }
        }
        print(f"\n[LSTM Forecaster] MAE = {self.metrics['LSTM']['MAE']} | Naive MAE = {self.metrics['Naive_Persistence']['MAE']}")

    def _plot_loss(self):
        plt.figure(figsize=(8, 4))
        plt.plot(self.train_losses, label="Train Loss (MSE)", color="#2980b9")
        plt.plot(self.val_losses, label="Validation Loss (MSE)", color="#e67e22", linestyle="--")
        plt.title("MLDisLSTMTHREAD3 - LSTM Training Loss Curves")
        plt.xlabel("Epoch")
        plt.ylabel("MSE Loss")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "lstm_training_validation_loss.png", dpi=200)
        plt.close()

    def _save(self):
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "scaler_min": self.scaler.data_min_.tolist(),
            "scaler_max": self.scaler.data_max_.tolist()
        }, MODELS_DIR / "lstm_forecaster.pt")
        
        with open(REPORTS_DIR / "lstm_forecasting_metrics.json", "w") as f:
            json.dump(self.metrics, f, indent=2)
