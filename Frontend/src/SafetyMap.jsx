import React, { Component, useCallback, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { HeatLayer } from "leaflet.heat";
import "./SafetyMap.css";

// Ensure global Leaflet instance is available if any plugin expects window.L
if (typeof window !== "undefined") {
  window.L = L;
}

class MapErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("SafetyMap runtime error caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "40px 20px", textAlign: "center", color: "#f87171" }}>
          <h2>Map Layer Loading Issue</h2>
          <p style={{ color: "#a1abc0", marginTop: 8 }}>
            {this.state.error?.message || "An unexpected error occurred while rendering the map view."}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: 16,
              padding: "10px 20px",
              borderRadius: 8,
              background: "#6366f1",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Reset Map View
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const markerColors = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};

function createSeverityIcon(severity) {
  const color =
    markerColors[String(severity || "medium").toLowerCase()] ||
    markerColors.medium;

  return L.divIcon({
    className: "severity-marker-wrapper",
    html: `<div style="
      width: 16px;
      height: 16px;
      background-color: ${color};
      border: 2px solid #ffffff;
      border-radius: 50%;
      box-shadow: 0 0 10px ${color};
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

function HeatmapLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!map || !points || points.length === 0) return;

    let heat = null;
    try {
      if (typeof HeatLayer === "function") {
        heat = new HeatLayer(points, {
          radius: 28,
          blur: 20,
          maxZoom: 17,
          max: 1.0,
          minOpacity: 0.35,
          gradient: {
            0.2: "#3b82f6",
            0.4: "#06b6d4",
            0.6: "#10b981",
            0.8: "#f59e0b",
            1.0: "#ef4444",
          },
        });
        heat.addTo(map);
      } else if (typeof L !== "undefined" && typeof L.heatLayer === "function") {
        heat = L.heatLayer(points, {
          radius: 28,
          blur: 20,
          maxZoom: 17,
          max: 1.0,
          minOpacity: 0.35,
        });
        heat.addTo(map);
      }
    } catch (err) {
      console.warn("Heatmap canvas layer initialization:", err);
    }

    return () => {
      if (heat && map) {
        try {
          map.removeLayer(heat);
        } catch (e) {
          // ignore layer removal errors
        }
      }
    };
  }, [map, points]);

  return null;
}

function getRiskCategoryTheme(cat) {
  const c = String(cat || "low").toUpperCase();
  if (c === "CRITICAL") {
    return {
      border: "#dc2626",
      fill: "#ef4444",
      badgeClass: "badge-critical",
      label: "Critical Risk",
    };
  }
  if (c === "HIGH") {
    return {
      border: "#ea580c",
      fill: "#f97316",
      badgeClass: "badge-high",
      label: "High Risk",
    };
  }
  if (c === "MEDIUM") {
    return {
      border: "#ca8a04",
      fill: "#eab308",
      badgeClass: "badge-medium",
      label: "Medium Risk",
    };
  }
  return {
    border: "#16a34a",
    fill: "#22c55e",
    badgeClass: "badge-low",
    label: "Low Risk",
  };
}

function SafetyMapContent({ token }) {
  // Mode switcher: "incidents" | "heatmap" | "risk_zones"
  const [viewMode, setViewMode] = useState("incidents");

  const [reports, setReports] = useState([]);
  const [riskZones, setRiskZones] = useState([]);
  const [severityCounts, setSeverityCounts] = useState({
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  });
  const [categoryCounts, setCategoryCounts] = useState({});

  const [loading, setLoading] = useState(false);
  const [zonesLoading, setZonesLoading] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState("");
  const [location, setLocation] = useState(null);

  // Filters
  const [radius, setRadius] = useState("5");
  const [typeFilter, setTypeFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("all");
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [timeFilter, setTimeFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [riskLevelFilter, setRiskLevelFilter] = useState("all");

  // New report modal state
  const [showModal, setShowModal] = useState(false);
  const [submittingReport, setSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState("");
  const [newReportType, setNewReportType] = useState("Harassment");
  const [newSeverity, setNewSeverity] = useState("medium");
  const [newDescription, setNewDescription] = useState("");

  const loadReports = useCallback(
    async (
      latitude,
      longitude,
      selectedRadius = radius,
      curType = typeFilter,
      curSev = severityFilter,
      curDate = dateFilter,
      curStart = customStartDate,
      curEnd = customEndDate,
      curTime = timeFilter
    ) => {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          latitude: String(latitude),
          longitude: String(longitude),
          radius_km: String(selectedRadius),
        });

        if (curType && curType !== "all") {
          params.append("report_type", curType);
        }
        if (curSev && curSev !== "all") {
          params.append("severity", curSev);
        }
        if (curDate && curDate !== "all") {
          params.append("date_range", curDate);
          if (curDate === "custom") {
            if (curStart) params.append("start_date", curStart);
            if (curEnd) params.append("end_date", curEnd);
          }
        }
        if (curTime && curTime !== "all") {
          params.append("time_of_day", curTime);
        }

        const response = await fetch(
          `http://127.0.0.1:8000/safety-reports/nearby?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Could not load safety reports.");
        }

        if (Array.isArray(data)) {
          setReports(data);
          const sc = { low: 0, medium: 0, high: 0, critical: 0 };
          data.forEach((r) => {
            const s = (r.severity || "medium").toLowerCase();
            if (sc[s] !== undefined) sc[s] += 1;
          });
          setSeverityCounts(sc);
        } else {
          setReports(data.reports || []);
          if (data.severity_counts) setSeverityCounts(data.severity_counts);
          if (data.category_counts) setCategoryCounts(data.category_counts);
        }
      } catch (err) {
        setError(err.message || "Could not load safety reports.");
        setReports([]);
      } finally {
        setLoading(false);
      }
    },
    [
      token,
      radius,
      typeFilter,
      severityFilter,
      dateFilter,
      customStartDate,
      customEndDate,
      timeFilter,
    ]
  );

  const loadRiskZones = useCallback(
    async (
      latitude,
      longitude,
      selectedRadius = radius,
      curRiskLevel = riskLevelFilter
    ) => {
      setZonesLoading(true);
      try {
        const params = new URLSearchParams({
          latitude: String(latitude),
          longitude: String(longitude),
          radius_km: String(selectedRadius),
        });

        if (curRiskLevel && curRiskLevel !== "all") {
          params.append("risk_level", curRiskLevel);
        }

        const response = await fetch(
          `http://127.0.0.1:8000/safety-reports/risk-zones?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();
        if (response.ok && data.zones) {
          setRiskZones(data.zones);
        } else {
          setRiskZones([]);
        }
      } catch (err) {
        console.error("Risk zones error:", err);
        setRiskZones([]);
      } finally {
        setZonesLoading(false);
      }
    },
    [token, radius, riskLevelFilter]
  );

  const detectLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Your browser does not support location detection.");
      return;
    }

    setLocating(true);
    setError("");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        setLocation({ latitude, longitude });
        setLocating(false);

        await loadReports(latitude, longitude);
        await loadRiskZones(latitude, longitude);
      },
      (err) => {
        setLocating(false);
        if (err.code === 1) {
          setError(
            "Location permission denied. Allow location access in your browser and try again."
          );
        } else if (err.code === 2) {
          setError("Your location is unavailable. Please try again.");
        } else {
          setError("Location request timed out. Please try again.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 0,
      }
    );
  }, [loadReports, loadRiskZones]);

  useEffect(() => {
    detectLocation();
  }, [detectLocation]);

  // Re-fetch reports when query filters change
  useEffect(() => {
    if (location) {
      loadReports(
        location.latitude,
        location.longitude,
        radius,
        typeFilter,
        severityFilter,
        dateFilter,
        customStartDate,
        customEndDate,
        timeFilter
      );
    }
  }, [
    location,
    radius,
    typeFilter,
    severityFilter,
    dateFilter,
    customStartDate,
    customEndDate,
    timeFilter,
    loadReports,
  ]);

  // Re-fetch risk zones when in risk_zones mode or radius/filter changes
  useEffect(() => {
    if (location && viewMode === "risk_zones") {
      loadRiskZones(
        location.latitude,
        location.longitude,
        radius,
        riskLevelFilter
      );
    }
  }, [location, viewMode, radius, riskLevelFilter, loadRiskZones]);

  const handleResetFilters = () => {
    setTypeFilter("all");
    setDateFilter("all");
    setCustomStartDate("");
    setCustomEndDate("");
    setTimeFilter("all");
    setSeverityFilter("all");
    setRiskLevelFilter("all");
    setRadius("5");
  };

  const handleSubmitReport = async (e) => {
    e.preventDefault();
    if (!token) {
      setError("Please log in to submit a safety report.");
      return;
    }
    if (!location) {
      setError("Location needed before submitting report.");
      return;
    }
    setSubmittingReport(true);
    setError("");
    setReportSuccess("");

    try {
      const response = await fetch("http://127.0.0.1:8000/safety-reports/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          report_type: newReportType,
          description: newDescription || "Safety incident reported by user",
          severity: newSeverity,
          latitude: location.latitude,
          longitude: location.longitude,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to submit report");
      }

      setReportSuccess("✅ Safety report logged! Real-time map updated.");
      setShowModal(false);
      setNewDescription("");
      await loadReports(location.latitude, location.longitude);
      if (viewMode === "risk_zones") {
        await loadRiskZones(location.latitude, location.longitude);
      }
    } catch (err) {
      setError(err.message || "Could not submit report.");
    } finally {
      setSubmittingReport(false);
    }
  };

  // Compute heatmap coordinates and weights
  const heatmapPoints = reports
    .map((r) => {
      const lat = Number(r.latitude);
      const lon = Number(r.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;

      const sev = String(r.severity || "medium").toLowerCase();
      let weight = 0.55;
      if (sev === "critical") weight = 1.0;
      else if (sev === "high") weight = 0.8;
      else if (sev === "low") weight = 0.35;

      return [lat, lon, weight];
    })
    .filter(Boolean);

  const defaultIncidentTypes = [
    "Harassment",
    "Suspicious_Activity",
    "Poor_Lighting",
    "Isolated_Area",
    "Unsafe_Road",
    "Theft",
    "Assault",
    "Other",
  ];

  const uniqueReportTypes = Array.from(
    new Set([
      ...defaultIncidentTypes,
      ...reports.map((r) => r.report_type).filter(Boolean),
    ])
  );

  return (
    <div className="safety-map-page">
      <div className="map-heading">
        <div>
          <h2>Safety Map & Intelligence Dashboard</h2>
          <p>
            Real-time crowdsourced incident reports, crime density heatmaps, and
            predictive ML risk zones
          </p>
        </div>

        <span className="map-status">
          {locating
            ? "Detecting GPS..."
            : location
            ? "GPS Active"
            : "Location Needed"}
        </span>
      </div>

      {error && <p className="map-error">{error}</p>}
      {reportSuccess && <p className="map-success-alert">{reportSuccess}</p>}

      {/* Mode Switcher */}
      <div className="map-mode-switcher">
        <button
          type="button"
          className={`mode-btn ${viewMode === "incidents" ? "active" : ""}`}
          onClick={() => setViewMode("incidents")}
        >
          <span className="mode-icon">📍</span>
          <span className="mode-label">Incident Map</span>
          <span className="mode-count">{reports.length}</span>
        </button>

        <button
          type="button"
          className={`mode-btn ${viewMode === "heatmap" ? "active" : ""}`}
          onClick={() => setViewMode("heatmap")}
        >
          <span className="mode-icon">🔥</span>
          <span className="mode-label">Crime Heatmap</span>
        </button>

        <button
          type="button"
          className={`mode-btn ${viewMode === "risk_zones" ? "active" : ""}`}
          onClick={() => setViewMode("risk_zones")}
        >
          <span className="mode-icon">🛡️</span>
          <span className="mode-label">ML Risk Zones</span>
          <span className="mode-badge-ai">AI</span>
        </button>
      </div>

      <div className="safety-map-layout">
        <section className="map-panel">
          <div className="map-toolbar">
            <label className="toolbar-radius-label">
              <span>Search Radius:</span>
              <select
                value={radius}
                onChange={(e) => setRadius(e.target.value)}
              >
                <option value="1">1 km</option>
                <option value="5">5 km</option>
                <option value="10">10 km</option>
                <option value="20">20 km</option>
              </select>
            </label>

            <button
              type="button"
              className="refresh-btn"
              onClick={detectLocation}
              disabled={locating || loading || zonesLoading}
            >
              {locating ? "Detecting..." : "Refresh GPS"}
            </button>

            <button
              type="button"
              className="report-incident-btn"
              onClick={() => setShowModal(true)}
            >
              + Report Incident
            </button>
          </div>

          {/* Mode Context Banners */}
          {viewMode === "heatmap" && (
            <div className="mode-disclaimer-banner heatmap-banner">
              <strong>Notice:</strong> Density is calculated strictly from reported
              safety incidents. An area without heatmap coloration denotes an
              absence of reported incidents, not guaranteed safety.
            </div>
          )}

          {viewMode === "risk_zones" && (
            <div className="mode-disclaimer-banner ml-banner">
              <strong>ML Spatio-Temporal Model:</strong> Sector risk is estimated
              using trained dynamic classifiers incorporating police/hospital
              proximity, diurnal factors, and historical crime patterns.
            </div>
          )}

          {location ? (
            <div className="interactive-map">
              <MapContainer
                key={`${location.latitude}-${location.longitude}-${viewMode}`}
                center={[location.latitude, location.longitude]}
                zoom={viewMode === "risk_zones" ? 13 : 14}
                scrollWheelZoom={true}
                style={{ height: "560px", width: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Search Radius Circle */}
                <Circle
                  center={[location.latitude, location.longitude]}
                  radius={Number(radius) * 1000}
                  pathOptions={{
                    color: "#6366f1",
                    fillColor: "#6366f1",
                    fillOpacity: 0.05,
                    dashArray: "6, 6",
                  }}
                />

                {/* User Location Marker */}
                <Marker position={[location.latitude, location.longitude]}>
                  <Popup>
                    <strong>Your Current Location</strong>
                    <br />
                    Lat: {location.latitude.toFixed(5)}, Lon:{" "}
                    {location.longitude.toFixed(5)}
                  </Popup>
                </Marker>

                {/* MODE 1: Incidents View */}
                {viewMode === "incidents" &&
                  reports.map((report) => {
                    const lat = Number(report.latitude);
                    const lon = Number(report.longitude);
                    if (
                      !Number.isFinite(lat) ||
                      !Number.isFinite(lon) ||
                      lat < -90 ||
                      lat > 90 ||
                      lon < -180 ||
                      lon > 180
                    ) {
                      return null;
                    }

                    const sev = (report.severity || "medium").toLowerCase();
                    const theme = getRiskCategoryTheme(sev);

                    return (
                      <Marker
                        key={report.id}
                        position={[lat, lon]}
                        icon={createSeverityIcon(report.severity)}
                      >
                        <Popup className="incident-popup">
                          <div className="incident-popup-card">
                            <div className="popup-header">
                              <span
                                className={`popup-severity-tag ${theme.badgeClass}`}
                              >
                                {sev.toUpperCase()}
                              </span>
                              <span className="popup-distance">
                                {(
                                  Number(report.distance_meters || 0) / 1000
                                ).toFixed(2)}{" "}
                                km away
                              </span>
                            </div>
                            <h4 className="popup-title">
                              {String(report.report_type || "Safety report")
                                .replaceAll("_", " ")}
                            </h4>
                            <p className="popup-desc">{report.description}</p>
                            {report.created_at && (
                              <div className="popup-time">
                                🕒 {new Date(report.created_at).toLocaleString()}
                              </div>
                            )}
                          </div>
                        </Popup>
                      </Marker>
                    );
                  })}

                {/* MODE 2: Crime Heatmap View */}
                {viewMode === "heatmap" && (
                  <>
                    <HeatmapLayer points={heatmapPoints} />
                    {reports
                      .filter(
                        (r) =>
                          Number.isFinite(Number(r.latitude)) &&
                          Number.isFinite(Number(r.longitude))
                      )
                      .map((report) => {
                        const sev = String(report.severity || "medium").toLowerCase();
                        const heatColor =
                          sev === "critical"
                            ? "#ef4444"
                            : sev === "high"
                            ? "#f97316"
                            : sev === "medium"
                            ? "#eab308"
                            : "#3b82f6";

                        return (
                          <Circle
                            key={`heatmap-halo-${report.id}`}
                            center={[Number(report.latitude), Number(report.longitude)]}
                            radius={sev === "critical" ? 240 : sev === "high" ? 190 : 140}
                            pathOptions={{
                              color: heatColor,
                              fillColor: heatColor,
                              fillOpacity: 0.25,
                              weight: 2,
                            }}
                          >
                            <Popup className="incident-popup">
                              <div className="incident-popup-card">
                                <div className="incident-popup-header">
                                  <span className={`popup-severity-tag tag-${sev}`}>
                                    {sev.toUpperCase()} DENSITY
                                  </span>
                                  <span className="popup-type-tag">
                                    {formatIncidentType(report.incident_type)}
                                  </span>
                                </div>
                                <p className="popup-desc">
                                  {report.description ||
                                    "Crowdsourced safety hazard concentration in this vicinity."}
                                </p>
                                <div className="popup-footer">
                                  <span className="popup-coords">
                                    📍 {Number(report.latitude).toFixed(4)},{" "}
                                    {Number(report.longitude).toFixed(4)}
                                  </span>
                                </div>
                              </div>
                            </Popup>
                          </Circle>
                        );
                      })}
                  </>
                )}

                {/* MODE 3: ML Risk Zones View */}
                {viewMode === "risk_zones" &&
                  riskZones.map((zone) => {
                    const theme = getRiskCategoryTheme(zone.risk_category);
                    return (
                      <Circle
                        key={zone.zone_id}
                        center={[zone.latitude, zone.longitude]}
                        radius={zone.radius_meters}
                        pathOptions={{
                          color: theme.border,
                          fillColor: theme.fill,
                          fillOpacity: 0.22,
                          weight: 2,
                        }}
                      >
                        <Popup className="risk-zone-popup">
                          <div className="zone-popup-card">
                            <div className="zone-popup-header">
                              <h4 className="zone-title">{zone.name}</h4>
                              <span
                                className={`zone-badge ${theme.badgeClass}`}
                              >
                                {zone.risk_category} RISK
                              </span>
                            </div>

                            <div className="zone-score-display">
                              <span className="zone-score-num">
                                {zone.risk_score}
                              </span>
                              <span className="zone-score-max">/ 100</span>
                              <span className="zone-confidence">
                                ({Math.round(zone.confidence * 100)}% Certainty)
                              </span>
                            </div>

                            <div className="zone-meta-grid">
                              <div className="zone-meta-item">
                                <strong>Nearest Police:</strong>
                                <span>
                                  {zone.nearest_police} ({zone.dist_police_km} km)
                                </span>
                              </div>
                              <div className="zone-meta-item">
                                <strong>Nearest Hospital:</strong>
                                <span>
                                  {zone.nearest_hospital} (
                                  {zone.dist_hospital_km} km)
                                </span>
                              </div>
                              <div className="zone-meta-item">
                                <strong>Incidents in Sector:</strong>
                                <span>{zone.incident_count} reports</span>
                              </div>
                            </div>

                            {zone.key_factors && zone.key_factors.length > 0 && (
                              <div className="zone-factors">
                                <strong>Contributing Factors:</strong>
                                <ul>
                                  {zone.key_factors.map((f, i) => (
                                    <li key={i}>{f}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            <div className="zone-disclaimer">
                              Dynamic ML Spatio-temporal evaluation
                            </div>
                          </div>
                        </Popup>
                      </Circle>
                    );
                  })}
              </MapContainer>
            </div>
          ) : (
            <div className="empty-reports map-placeholder">
              {locating
                ? "Detecting your location..."
                : "Allow location access to display the map."}
              {!locating && (
                <button
                  type="button"
                  className="retry-loc-btn"
                  onClick={detectLocation}
                >
                  Try again
                </button>
              )}
            </div>
          )}

          {/* Live Statistics Bar */}
          <div className="safety-stats-bar">
            <div className="stat-item total-stat">
              <span className="stat-label">Reports in {radius} km</span>
              <span className="stat-value">{reports.length}</span>
            </div>
            <div className="stat-divider" />
            <div className="stat-item low-stat">
              <span className="stat-dot low-dot" />
              <span className="stat-label">Low</span>
              <span className="stat-value">{severityCounts.low || 0}</span>
            </div>
            <div className="stat-item medium-stat">
              <span className="stat-dot medium-dot" />
              <span className="stat-label">Medium</span>
              <span className="stat-value">{severityCounts.medium || 0}</span>
            </div>
            <div className="stat-item high-stat">
              <span className="stat-dot high-dot" />
              <span className="stat-label">High</span>
              <span className="stat-value">{severityCounts.high || 0}</span>
            </div>
            <div className="stat-item critical-stat">
              <span className="stat-dot critical-dot" />
              <span className="stat-label">Critical</span>
              <span className="stat-value">{severityCounts.critical || 0}</span>
            </div>
          </div>

          {/* Dynamic Legend */}
          <div className="map-legend-container">
            {viewMode === "incidents" && (
              <div className="severity-legend">
                <span>
                  <i className="legend-dot low-dot" /> Low Severity
                </span>
                <span>
                  <i className="legend-dot medium-dot" /> Medium Caution
                </span>
                <span>
                  <i className="legend-dot high-dot" /> High Threat
                </span>
                <span>
                  <i className="legend-dot critical-dot" /> Critical Danger
                </span>
              </div>
            )}

            {viewMode === "heatmap" && (
              <div className="heatmap-legend">
                <span className="legend-scale-label">Low Density</span>
                <div className="heatmap-gradient-bar" />
                <span className="legend-scale-label">High Density</span>
              </div>
            )}

            {viewMode === "risk_zones" && (
              <div className="risk-zones-legend">
                <span className="legend-tag badge-low">Low (&lt;35)</span>
                <span className="legend-tag badge-medium">Medium (35-64)</span>
                <span className="legend-tag badge-high">High (65-84)</span>
                <span className="legend-tag badge-critical">Critical (85+)</span>
              </div>
            )}
          </div>
        </section>

        {/* Functional Filters Panel */}
        <aside className="filters-panel">
          <div className="filters-header">
            <h3>Filters</h3>
            <button
              type="button"
              className="reset-filters-btn"
              onClick={handleResetFilters}
            >
              Reset Filters
            </button>
          </div>

          {/* 1. Crime Type Filter */}
          <div className="filter-option">
            <label htmlFor="crime-type">
              <span>Crime Type</span>
              <select
                id="crime-type"
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
              >
                <option value="all">All Types</option>
                {uniqueReportTypes.map((type) => (
                  <option key={type} value={type}>
                    {String(type).replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {/* 2. Date Range Filter */}
          <div className="filter-option">
            <label htmlFor="date-range">
              <span>Date Range</span>
              <select
                id="date-range"
                value={dateFilter}
                onChange={(event) => setDateFilter(event.target.value)}
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
                <option value="custom">Custom Date Range</option>
              </select>
            </label>

            {dateFilter === "custom" && (
              <div className="custom-date-inputs">
                <div className="custom-date-field">
                  <small>From:</small>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                  />
                </div>
                <div className="custom-date-field">
                  <small>To:</small>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>

          {/* 3. Time of Day Filter */}
          <div className="filter-option">
            <label htmlFor="time-range">
              <span>Time of Day</span>
              <select
                id="time-range"
                value={timeFilter}
                onChange={(event) => setTimeFilter(event.target.value)}
              >
                <option value="all">All Hours</option>
                <option value="morning">Morning (5 AM - 12 PM)</option>
                <option value="afternoon">Afternoon (12 PM - 5 PM)</option>
                <option value="evening">Evening (5 PM - 9 PM)</option>
                <option value="night">Night (9 PM - 5 AM)</option>
              </select>
            </label>
          </div>

          {/* 4. Severity Filter */}
          <div className="filter-option">
            <label htmlFor="severity">
              <span>Incident Severity</span>
              <select
                id="severity"
                value={severityFilter}
                onChange={(event) => setSeverityFilter(event.target.value)}
              >
                <option value="all">All Severities</option>
                <option value="low">Low Caution</option>
                <option value="medium">Medium</option>
                <option value="high">High Threat</option>
                <option value="critical">Critical Emergency</option>
              </select>
            </label>
          </div>

          {/* 5. Risk Level Filter */}
          <div className="filter-option">
            <label htmlFor="risk-level">
              <span>ML Risk Level</span>
              <select
                id="risk-level"
                value={riskLevelFilter}
                onChange={(event) => setRiskLevelFilter(event.target.value)}
              >
                <option value="all">All Risk Levels</option>
                <option value="low">Low Risk (&lt;35)</option>
                <option value="medium">Medium Risk (35-64)</option>
                <option value="high">High Risk (65-84)</option>
                <option value="critical">Critical Risk (85+)</option>
              </select>
            </label>
            <small className="filter-hint">
              {viewMode === "risk_zones"
                ? "Actively filtering spatial AI risk sectors"
                : "Applies to ML Risk Zones view"}
            </small>
          </div>

          <div className="filter-stats-card">
            <h4>Safety Map Summary</h4>
            <div className="filter-stat-row">
              <span>Active Radius:</span>
              <strong>{radius} km</strong>
            </div>
            <div className="filter-stat-row">
              <span>Matching Incidents:</span>
              <strong>{reports.length}</strong>
            </div>
            {viewMode === "risk_zones" && (
              <div className="filter-stat-row">
                <span>Active AI Sectors:</span>
                <strong>{riskZones.length}</strong>
              </div>
            )}
          </div>

          <p className="filter-note">
            ⚠️ <strong>Safety Disclaimer:</strong> Missing incidents or
            uncolored zones do not guarantee safety. Always stay vigilant and
            use Safe Routing when navigating after dusk.
          </p>
        </aside>
      </div>

      {/* New Incident Report Modal */}
      {showModal && (
        <div
          className="report-modal-backdrop"
          onClick={() => setShowModal(false)}
        >
          <div className="report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Report Safety Issue</h3>
              <button
                type="button"
                className="close-btn"
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmitReport}>
              <div className="form-group">
                <label>Issue Category</label>
                <select
                  value={newReportType}
                  onChange={(e) => setNewReportType(e.target.value)}
                >
                  <option value="Harassment">
                    Harassment (Stalking, Catcalling)
                  </option>
                  <option value="Suspicious_Activity">
                    Suspicious Activity / Loitering
                  </option>
                  <option value="Poor_Lighting">
                    Poor Lighting / Dark Corridor
                  </option>
                  <option value="Isolated_Area">
                    Isolated Area / Desolate Lane
                  </option>
                  <option value="Unsafe_Road">Unsafe Road Infrastructure</option>
                  <option value="Theft">Theft / Snatching</option>
                  <option value="Assault">Physical Threat / Assault</option>
                  <option value="Other">Other Safety Concern</option>
                </select>
              </div>

              <div className="form-group">
                <label>Perceived Severity</label>
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                >
                  <option value="low">Low (Minor caution)</option>
                  <option value="medium">Medium (Suspicious / uneasy)</option>
                  <option value="high">High (Direct threat / harassment)</option>
                  <option value="critical">Critical (Imminent danger)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Description & Notes</label>
                <textarea
                  rows="3"
                  placeholder="Describe what occurred, landmarks, or vehicle details..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  required
                />
              </div>

              <div className="form-coords-hint">
                <span>
                  Location:{" "}
                  {location
                    ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(
                        4
                      )} (Current GPS)`
                    : "Detecting..."}
                </span>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={submittingReport || !location}
                >
                  {submittingReport
                    ? "Logging Report..."
                    : "Submit Safety Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function SafetyMap(props) {
  return (
    <MapErrorBoundary>
      <SafetyMapContent {...props} />
    </MapErrorBoundary>
  );
}

export default SafetyMap;
