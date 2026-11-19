import { useState } from "react";
import "./NLPAssistant.css";

const API_URL = "http://127.0.0.1:8000";

const PRESET_MESSAGES = [
  {
    label: "🚨 Critical Emergency",
    text: "Help! Someone is attacking me and threatening me with a weapon. I need immediate assistance."
  },
  {
    label: "👁️ Suspicious Activity",
    text: "I have noticed someone following me for several streets. They keep changing direction whenever I do, and I feel unsafe."
  },
  {
    label: "🛑 Harassment Alert",
    text: "A group of people are verbally harassing me, making inappropriate comments and blocking my way."
  },
  {
    label: "✅ Normal Commute",
    text: "I have reached home safely after college. Everything went normally."
  }
];

function NLPAssistant({ token, onTriggerEmergency }) {
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [sosStatus, setSosStatus] = useState("");

  const handleClassify = async (messageToClassify) => {
    const text = (messageToClassify || inputText).trim();
    if (!text) {
      setError("Please enter a message to classify.");
      return;
    }

    setLoading(true);
    setResult(null); // Clear stale results immediately so old data is not shown
    setError("");
    setSosStatus("");

    try {
      const response = await fetch(`${API_URL}/api/v1/ml/nlp-classify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message_text: text })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Classification failed");
      }
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to analyze message");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSOS = async () => {
    if (!token) {
      setError("Please log in to trigger an SOS alert.");
      return;
    }

    setSosStatus("Triggering verified SOS...");
    try {
      const response = await fetch(`${API_URL}/sos/trigger`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          latitude: 28.6139,
          longitude: 77.2090
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "SOS dispatch failed");
      }
      setSosStatus("✅ User-confirmed SOS broadcasted to trusted contacts & emergency log!");
      if (onTriggerEmergency) {
        onTriggerEmergency();
      }
    } catch (err) {
      setSosStatus(`❌ Error triggering SOS: ${err.message}`);
    }
  };

  return (
    <div className="nlp-assistant-page">
      <header className="nlp-header">
        <div className="nlp-header-title">
          <h1 className="nlp-title">
            AI Safety Assistant
          </h1>
        </div>
        <div className="nlp-badge" aria-label="Shield Transformer Active">
          <span>Shield Transformer Active</span>
          <span className="nlp-status-dot" aria-hidden="true" />
        </div>
      </header>

      <div className="nlp-guardrail-notice">
        <strong>⚖️ Constitutional Safety Policy:</strong>
        <span>
          {" "}This AI will <u>never</u> autonomously dial emergency numbers or broadcast alerts without your explicit confirmation. Tap below to confirm any emergency action.
        </span>
      </div>

      <div className="nlp-layout">
        <section className="nlp-input-card">
          <h3>Analyze Message or Audio Transcript</h3>
          <p className="nlp-hint">Type a message or select a benchmark emergency scenario:</p>

          <div className="preset-chips">
            {PRESET_MESSAGES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                className="preset-chip"
                onClick={() => {
                  setInputText(preset.text);
                  handleClassify(preset.text);
                }}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <textarea
            className="nlp-textarea"
            rows="4"
            placeholder="e.g. Help me! Someone is following me down the dark alley..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />

          <div className="nlp-btn-row">
            <button
              type="button"
              className="nlp-submit-btn"
              onClick={() => handleClassify()}
              disabled={loading || !inputText.trim()}
            >
              {loading ? "Analyzing Intent..." : "⚡ Classify Safety Message"}
            </button>
            {inputText && (
              <button
                type="button"
                className="nlp-clear-btn"
                onClick={() => {
                  setInputText("");
                  setResult(null);
                  setError("");
                  setSosStatus("");
                }}
              >
                Clear
              </button>
            )}
          </div>

          {error && <div className="nlp-error-msg">{error}</div>}
        </section>

        {loading && (
          <section className="nlp-result-card nlp-loading-card">
            <div className="nlp-analyzing-spinner">
              <span className="nlp-spinner-icon">⚡</span>
              <h3>DistilBERT Safety Analysis in Progress...</h3>
              <p className="nlp-hint">
                Evaluating threat category, contextual severity, and probability distribution.
              </p>
            </div>
          </section>
        )}

        {!loading && result && (
          <section className="nlp-result-card">
            <div className="result-header">
              <div>
                <span className="result-label">Predicted Threat Level</span>
                <h3 className={`category-tag cat-${result.predicted_category.toLowerCase()}`}>
                  {result.predicted_category.toUpperCase()}
                </h3>
              </div>
              <div className="confidence-pill">
                <span>Certainty:</span>
                <strong>{(result.confidence * 100).toFixed(1)}%</strong>
              </div>
            </div>

            <div className="advisory-box">
              <strong>Advisory:</strong>
              <p>{result.ui_advisory_message}</p>
            </div>

            <div className="prob-breakdown">
              <h4>Class Probability Distribution</h4>
              {Object.entries(result.class_probabilities || {}).map(([className, prob]) => (
                <div key={className} className="prob-row">
                  <span className="prob-name">{className}</span>
                  <div className="prob-track">
                    <div
                      className={`prob-fill cat-${className.toLowerCase()}`}
                      style={{ width: `${Math.round(prob * 100)}%` }}
                    />
                  </div>
                  <span className="prob-pct">{(prob * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>

            {result.requires_user_confirmation && (
              <div className="confirmation-action-box">
                <div className="confirm-icon">⚠️</div>
                <div className="confirm-content">
                  <strong>User Action Confirmation Required</strong>
                  <p>Threat detected. Tap the button below to confirm and broadcast your SOS alert.</p>
                  <button
                    type="button"
                    className="sos-confirm-btn"
                    onClick={handleConfirmSOS}
                  >
                    🚨 Yes, Trigger SOS Alert Now
                  </button>
                </div>
              </div>
            )}

            {sosStatus && <div className="sos-status-alert">{sosStatus}</div>}

            <div className="nlp-meta-footer">
              <span>Architecture: {result.model_architecture}</span>
              <span>Autonomous Dispatch: {String(result.autonomous_emergency_contact_triggered)}</span>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default NLPAssistant;
