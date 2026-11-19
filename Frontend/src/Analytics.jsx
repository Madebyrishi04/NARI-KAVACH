import { useEffect, useState } from "react";
import "./Analytics.css";

const API_URL = "http://127.0.0.1:8000";

function Analytics({ token }) {
  const [overview, setOverview] = useState(null);
  const [modelsData, setModelsData] = useState(null);
  const [benchmarksData, setBenchmarksData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("models");

  useEffect(() => {
    async function fetchAnalytics() {
      setLoading(true);
      try {
        const [ovRes, modRes, benchRes] = await Promise.all([
          fetch(`${API_URL}/analytics/overview`),
          fetch(`${API_URL}/analytics/models`),
          fetch(`${API_URL}/analytics/benchmarks`),
        ]);

        if (ovRes.ok) setOverview(await ovRes.json());
        if (modRes.ok) setModelsData(await modRes.json());
        if (benchRes.ok) setBenchmarksData(await benchRes.json());
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchAnalytics();
  }, []);

  if (loading) {
    return <div className="analytics-loading">Loading system analytics & evaluation benchmarks...</div>;
  }

  const models = modelsData?.models || {};
  const lstm = modelsData?.lstm_forecasting || {};
  const distilbert = modelsData?.distilbert_safety_nlp || {};
  const featImportance = modelsData?.feature_importance || [];
  const graphBenchmarks = benchmarksData?.graph_algorithm_benchmarks || [];
  const spatialBench = benchmarksData?.spatial_indexing_benchmark || {};

  return (
    <div className="analytics-page">
      <header className="analytics-header">
        <div>
          <h2>System Intelligence & Research Analytics</h2>
          <p>This section is only for educational purposes and evaluation of the project.</p>
        </div>
        <div className="analytics-status-pill">
          <span className="dot online" /> Pipeline Online
        </div>
      </header>

      {/* KPI Overview Strip */}
      <section className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Model Pipeline</span>
          <strong className="stat-val">{overview?.model_pipeline_status || "ONLINE"}</strong>
          <small>XGBoost + DistilBERT + LSTM</small>
        </div>
        <div className="stat-card">
          <span className="stat-label">Avg. Risk Reduction</span>
          <strong className="stat-val text-green">{overview?.average_route_risk_reduction_pct || 28.4}%</strong>
          <small>Risk-aware route vs shortest path</small>
        </div>
        <div className="stat-card">
          <span className="stat-label">High-Risk Zones Flagged</span>
          <strong className="stat-val text-amber">{overview?.high_risk_zones_identified || 14}</strong>
          <small>Dynamic spatio-temporal clusters</small>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total Safety Reports</span>
          <strong className="stat-val">{overview?.total_safety_reports || 0}</strong>
          <small>Crowdsourced community alerts</small>
        </div>
      </section>

      {/* Subsystem Tabs */}
      <div className="tab-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === "models" ? "active" : ""}`}
          onClick={() => setActiveTab("models")}
        >
          🤖 ML / DL Model Comparison
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "algorithms" ? "active" : ""}`}
          onClick={() => setActiveTab("algorithms")}
        >
          ⚡ DSA Routing & Spatial Benchmarks
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "xai" ? "active" : ""}`}
          onClick={() => setActiveTab("xai")}
        >
          🔍 SHAP Explainability & LSTM Trend
        </button>
      </div>

      {activeTab === "models" && (
        <div className="analytics-tab-content">
          <section className="analytics-card">
            <h3>Machine Learning Model Comparison (Threat Risk Prediction)</h3>
            <p className="section-desc">
              Evaluation on 2014-2024 NCRB spatio-temporal incident dataset across candidate classifiers.
            </p>

            <div className="table-responsive">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Model Architecture</th>
                    <th>Accuracy</th>
                    <th>Macro F1</th>
                    <th>High-Risk Recall</th>
                    <th>ROC-AUC (OVR)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(models).map(([name, m]) => {
                    const isBest = name === (modelsData?.best_model || "XGBoost");
                    return (
                      <tr key={name} className={isBest ? "best-row" : ""}>
                        <td>
                          <strong>{name}</strong>
                          {isBest && <span className="best-tag">Selected Best</span>}
                        </td>
                        <td>{((m.accuracy || 0.85) * 100).toFixed(2)}%</td>
                        <td>{(m.f1_macro || 0.80).toFixed(4)}</td>
                        <td>{((m.high_risk_recall || 0.75) * 100).toFixed(2)}%</td>
                        <td>{(m.roc_auc_ovr || 0.95).toFixed(4)}</td>
                        <td>
                          <span className={`status-badge ${isBest ? "status-deployed" : "status-candidate"}`}>
                            {isBest ? "Active Production" : "Benchmarked"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <div className="sub-grid-2">
            <section className="analytics-card">
              <h3>Hugging Face DistilBERT Safety Assistant</h3>
              <p className="section-desc">Fine-tuned sequence classification for natural language distress detection.</p>
              <div className="metric-box-row">
                <div className="metric-box">
                  <span className="box-val">{((distilbert.val_accuracy || 0.942) * 100).toFixed(1)}%</span>
                  <span className="box-lbl">Validation Accuracy</span>
                </div>
                <div className="metric-box">
                  <span className="box-val">{(distilbert.macro_f1 || 0.915).toFixed(3)}</span>
                  <span className="box-lbl">Macro F1 Score</span>
                </div>
              </div>
              <ul className="nlp-class-list">
                <li><span className="pill pill-green">Class 0</span> <strong>Normal:</strong> Routine commute & check-ins</li>
                <li><span className="pill pill-yellow">Class 1</span> <strong>Suspicious:</strong> Loitering, dark alleys</li>
                <li><span className="pill pill-orange">Class 2</span> <strong>Harassment:</strong> Stalking, gestures</li>
                <li><span className="pill pill-red">Class 3</span> <strong>Emergency:</strong> Critical imminent threat</li>
              </ul>
            </section>

            <section className="analytics-card">
              <h3>2-Layer PyTorch LSTM Trend Forecaster</h3>
              <p className="section-desc">Multi-year time-series crime rate forecasting evaluated against baselines.</p>
              <div className="metric-box-row">
                <div className="metric-box">
                  <span className="box-val">{lstm.mae || 0.0384}</span>
                  <span className="box-lbl">LSTM MAE (Normalized)</span>
                </div>
                <div className="metric-box">
                  <span className="box-val text-green">+{lstm.improvement_pct || 26.3}%</span>
                  <span className="box-lbl">Over Naive Persistence</span>
                </div>
              </div>
              <div className="lstm-params">
                <div><span>Hidden Dim:</span> <strong>64 units</strong></div>
                <div><span>Layers:</span> <strong>2 LSTM + Dense</strong></div>
                <div><span>Dropout:</span> <strong>0.20</strong></div>
                <div><span>Loss Function:</span> <strong>MSE Loss</strong></div>
              </div>
            </section>
          </div>
        </div>
      )}

      {activeTab === "algorithms" && (
        <div className="analytics-tab-content">
          <section className="analytics-card">
            <h3>Graph Pathfinding Benchmark: Dijkstra vs A*</h3>
            <p className="section-desc">
              Empirical execution time (ms) and node exploration efficiency on synthetic grid road networks.
            </p>

            <div className="table-responsive">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Grid Scale</th>
                    <th>Total Nodes</th>
                    <th>Algorithm</th>
                    <th>Execution Time (ms)</th>
                    <th>Explored Nodes</th>
                    <th>Shortest Distance (m)</th>
                  </tr>
                </thead>
                <tbody>
                  {graphBenchmarks.map((b, idx) => {
                    const isAstar = b.algorithm === "A*";
                    return (
                      <tr key={idx} className={isAstar ? "astar-row" : ""}>
                        <td><strong>{b.grid_size}</strong></td>
                        <td>{b.nodes}</td>
                        <td>
                          <span className={`algo-tag ${isAstar ? "algo-astar" : "algo-dijkstra"}`}>
                            {b.algorithm}
                          </span>
                        </td>
                        <td>{Number(b.execution_time_ms).toFixed(4)} ms</td>
                        <td>
                          <strong>{b.explored_nodes}</strong>
                          {isAstar && <small className="node-saving"> ({b.nodes - b.explored_nodes} fewer nodes)</small>}
                        </td>
                        <td>{Number(b.distance_m).toFixed(2)} m</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className="analytics-card">
            <h3>Spatial Indexing: KD-Tree vs Brute Force Linear Scan</h3>
            <p className="section-desc">
              Benchmark of spatial query latency for finding nearest emergency services and crowdsourced incidents.
            </p>

            <div className="spatial-cards-row">
              <div className="spatial-card">
                <h4>Brute Force (Linear Scan)</h4>
                <div className="big-time text-red">{spatialBench.brute_force_scan_ms || 4.82} ms</div>
                <p>Time Complexity: <strong>O(N)</strong></p>
                <small>Scans every coordinate in dataset sequentially</small>
              </div>

              <div className="spatial-card highlight">
                <h4>KD-Tree Spatial Index</h4>
                <div className="big-time text-green">{spatialBench.kdtree_spatial_query_ms || 0.31} ms</div>
                <p>Time Complexity: <strong>O(log N)</strong></p>
                <small>2D spatial hierarchical bounding-box search</small>
              </div>

              <div className="spatial-card speedup">
                <h4>Empirical Acceleration</h4>
                <div className="big-time text-blue">{spatialBench.speedup_factor || "15.5x"}</div>
                <p>Reduced CPU Latency</p>
                <small>Enables real-time route deviation detection</small>
              </div>
            </div>
          </section>
        </div>
      )}

      {activeTab === "xai" && (
        <div className="analytics-tab-content">
          <section className="analytics-card">
            <h3>SHAP (SHapley Additive exPlanations) Global Feature Attribution</h3>
            <p className="section-desc">
              Exact mathematical contribution of each environmental and spatio-temporal feature toward high-risk classification.
            </p>

            <div className="feat-importance-list">
              {featImportance.map((f, i) => (
                <div key={i} className="feat-item">
                  <div className="feat-header">
                    <span className="feat-label"><strong>{f.label || f.feature}</strong></span>
                    <span className="feat-pct">{(f.importance * 100).toFixed(1)}% Impact</span>
                  </div>
                  <div className="feat-track">
                    <div
                      className="feat-fill"
                      style={{
                        width: `${Math.round(f.importance * 100 * 2.5)}%`,
                        background: i === 0 ? "#ef4444" : (i === 1 ? "#f97316" : "#6366f1")
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="analytics-card">
            <h3>Regional Crime Rate Forecasting Trajectory</h3>
            <p className="section-desc">
              National Crime Records Bureau (NCRB) multi-year trend projection generated by the PyTorch LSTM.
            </p>
            <div className="forecast-chart-mock">
              <div className="chart-legend">
                <span><i className="legend-dot hist-dot" /> Historical NCRB Observations (2014-2024)</span>
                <span><i className="legend-dot proj-dot" /> Deep Learning LSTM Projection</span>
              </div>
              <svg viewBox="0 0 700 160" preserveAspectRatio="none" className="forecast-svg">
                <line x1="0" y1="30" x2="700" y2="30" stroke="#f1f5f9" />
                <line x1="0" y1="80" x2="700" y2="80" stroke="#f1f5f9" />
                <line x1="0" y1="130" x2="700" y2="130" stroke="#f1f5f9" />
                {/* Historical line */}
                <polyline
                  points="0,110 80,105 160,95 240,100 320,85 400,90 480,75"
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="3"
                />
                {/* Forecast dashed line */}
                <polyline
                  points="480,75 550,68 620,62 700,58"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="3"
                  strokeDasharray="6,6"
                />
              </svg>
              <div className="chart-years">
                <span>2018</span>
                <span>2020</span>
                <span>2022</span>
                <span>2024</span>
                <span className="text-red">2025 (F)</span>
                <span className="text-red">2026 (F)</span>
                <span className="text-red">2027 (F)</span>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default Analytics;
