
import { useCallback, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./SafetyMap.css";

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

function SafetyMap({ token }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState("");
  const [location, setLocation] = useState(null);
  const [radius, setRadius] = useState("5");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  // New report modal state
  const [showModal, setShowModal] = useState(false);
  const [submittingReport, setSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState("");
  const [newReportType, setNewReportType] = useState("Harassment");
  const [newSeverity, setNewSeverity] = useState("medium");
  const [newDescription, setNewDescription] = useState("");

  const loadReports = useCallback(
    async (latitude, longitude, selectedRadius = radius) => {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          latitude: String(latitude),
          longitude: String(longitude),
          radius_km: selectedRadius,
        });

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
          throw new Error(
            data.detail || "Could not load safety reports."
          );
        }

        setReports(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || "Could not load safety reports.");
        setReports([]);
      } finally {
        setLoading(false);
      }
    },
    [token, radius]
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
  }, [loadReports]);

  useEffect(() => {
    detectLocation();
  }, [detectLocation]);

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
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          report_type: newReportType,
          description: newDescription || "Safety incident reported by user",
          severity: newSeverity,
          latitude: location.latitude,
          longitude: location.longitude
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to submit report");
      }

      setReportSuccess("✅ Safety report logged! Real-time map updated.");
      setShowModal(false);
      setNewDescription("");
      await loadReports(location.latitude, location.longitude);
    } catch (err) {
      setError(err.message || "Could not submit report.");
    } finally {
      setSubmittingReport(false);
    }
  };

  const handleRadiusChange = (event) => {
    const nextRadius = event.target.value;
    setRadius(nextRadius);

    if (location) {
      loadReports(
        location.latitude,
        location.longitude,
        nextRadius
      );
    }
  };

  const reportTypes = [
    ...new Set(reports.map((report) => report.report_type)),
  ];

  const visibleReports = reports.filter((report) => {
    const matchesSeverity =
      severityFilter === "all" ||
      String(report.severity || "").toLowerCase() === severityFilter;

    const matchesType =
      typeFilter === "all" || report.report_type === typeFilter;

    return matchesSeverity && matchesType;
  });

  return (
    <div className="safety-map-page">
      <div className="map-heading">
        <div>
          <h2>Safety map</h2>
          <p>Crime reports and safety information near you</p>
        </div>

        <span className="map-status">
          {locating
            ? "Finding location..."
            : location
              ? "Location detected"
              : "Location needed"}
        </span>
      </div>

      {error && <p className="map-error">{error}</p>}
      {reportSuccess && <p className="map-success-alert">{reportSuccess}</p>}

      <div className="safety-map-layout">
        <section className="map-panel">
          <div className="map-toolbar">
            <label>
              Search radius
              <select value={radius} onChange={handleRadiusChange}>
                <option value="1">1 km</option>
                <option value="5">5 km</option>
                <option value="10">10 km</option>
                <option value="20">20 km</option>
              </select>
            </label>

            <button
              onClick={detectLocation}
              disabled={locating || loading}
            >
              {locating ? "Detecting..." : "Refresh location"}
            </button>

            <button
              type="button"
              className="report-incident-btn"
              onClick={() => setShowModal(true)}
            >
              + Report Safety Issue
            </button>
          </div>

          {location ? (
            <div className="interactive-map">
              <MapContainer
                key={`${location.latitude}-${location.longitude}`}
                center={[location.latitude, location.longitude]}
                zoom={14}
                scrollWheelZoom={true}
                style={{ height: "600px", width: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Circle
                  center={[location.latitude, location.longitude]}
                  radius={Number(radius) * 1000}
                  pathOptions={{
                    color: "#7887ff",
                    fillColor: "#7887ff",
                    fillOpacity: 0.12,
                  }}
                />

                <Marker
                  position={[
                    location.latitude,
                    location.longitude,
                  ]}
                >
                  <Popup>Your current location</Popup>
                </Marker>

                {visibleReports.map((report) => {
                  const latitude = Number(report.latitude);
                  const longitude = Number(report.longitude);

                  if (
                    !Number.isFinite(latitude) ||
                    !Number.isFinite(longitude) ||
                    latitude < -90 ||
                    latitude > 90 ||
                    longitude < -180 ||
                    longitude > 180
                  ) {
                    return null;
                  }

                  return (
                    <Marker
                      key={report.id}
                      position={[latitude, longitude]}
                      icon={createSeverityIcon(report.severity)}
                    >
                      <Popup>
                        <strong>
                          {String(report.report_type || "Safety report")
                            .replaceAll("_", " ")}
                        </strong>
                        <br />
                        Severity: {report.severity || "Not specified"}
                        <br />
                        {report.description}
                        <br />
                        Distance:{" "}
                        {(
                          Number(report.distance_meters || 0) / 1000
                        ).toFixed(2)}{" "}
                        km
                      </Popup>
                    </Marker>
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
                <button onClick={detectLocation}>Try again</button>
              )}
            </div>
          )}

          <div className="reports-summary">
            <strong>{visibleReports.length}</strong>
            <span>
              {loading
                ? "Loading reports..."
                : "matching nearby reports"}
            </span>
          </div>

          <div className="severity-legend">
            <span><i className="legend-dot low-dot" /> Low</span>
            <span><i className="legend-dot medium-dot" /> Medium</span>
            <span><i className="legend-dot high-dot" /> High</span>
            <span><i className="legend-dot critical-dot" /> Critical</span>
          </div>
        </section>

        <aside className="filters-panel">
          <h3>Filters</h3>

          <div className="filter-option">
            <label htmlFor="crime-type">Crime type</label>
            <select
              id="crime-type"
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
            >
              <option value="all">All types</option>
              {reportTypes.map((type) => (
                <option key={type} value={type}>
                  {String(type).replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-option">
            <label htmlFor="date-range">Date range</label>
            <select id="date-range" disabled>
              <option>All available dates</option>
            </select>
            <small>Date filtering needs a backend date filter.</small>
          </div>

          <div className="filter-option">
            <label htmlFor="time-range">Time of day</label>
            <select id="time-range" disabled>
              <option>All times</option>
            </select>
            <small>Time filtering needs timestamp data.</small>
          </div>

          <div className="filter-option">
            <label htmlFor="severity">Severity</label>
            <select
              id="severity"
              value={severityFilter}
              onChange={(event) => setSeverityFilter(event.target.value)}
            >
              <option value="all">All severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div className="filter-option">
            <label htmlFor="risk-level">Risk level</label>
            <select id="risk-level" disabled>
              <option>Unavailable</option>
            </select>
            <small>
              Risk zones will be added when real risk data is available.
            </small>
          </div>

          <p className="filter-note">
            Showing submitted safety reports only. Missing reports do not
            mean an area is safe.
          </p>
        </aside>
      </div>

      {showModal && (
        <div className="report-modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Report Safety Issue</h3>
              <button type="button" className="close-btn" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmitReport}>
              <div className="form-group">
                <label>Issue Category</label>
                <select value={newReportType} onChange={(e) => setNewReportType(e.target.value)}>
                  <option value="Harassment">Harassment (Stalking, Catcalling)</option>
                  <option value="Suspicious_Activity">Suspicious Activity / Loitering</option>
                  <option value="Poor_Lighting">Poor Lighting / Dark Corridor</option>
                  <option value="Isolated_Area">Isolated Area / Desolate Lane</option>
                  <option value="Unsafe_Road">Unsafe Road Infrastructure</option>
                  <option value="Other">Other Safety Concern</option>
                </select>
              </div>

              <div className="form-group">
                <label>Perceived Severity</label>
                <select value={newSeverity} onChange={(e) => setNewSeverity(e.target.value)}>
                  <option value="low">Low (Minor nuisance, caution)</option>
                  <option value="medium">Medium (Uncomfortable / suspicious)</option>
                  <option value="high">High (Active threat / harassment)</option>
                  <option value="critical">Critical (Imminent danger / emergency)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Description & Notes</label>
                <textarea
                  rows="3"
                  placeholder="Describe what occurred, exact landmarks, or vehicle details..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  required
                />
              </div>

              <div className="form-coords-hint">
                <span>Location: {location ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)} (Current GPS)` : "Detecting..."}</span>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-submit" disabled={submittingReport || !location}>
                  {submittingReport ? "Logging Report..." : "Submit Safety Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default SafetyMap;
