import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./SafeRoute.css";

function MapBoundsUpdater({ coordinates }) {
  const map = useMap();
  useEffect(() => {
    if (coordinates && coordinates.length > 1) {
      try {
        const bounds = L.latLngBounds(coordinates);
        map.fitBounds(bounds, { padding: [40, 40] });
      } catch (e) {
        console.warn("Could not fit map bounds:", e);
      }
    }
  }, [coordinates, map]);
  return null;
}

const API_URL = "http://127.0.0.1:8000";

const originIcon = L.divIcon({
  className: "custom-map-icon",
  html: `<div style="background:#22c55e;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 0 10px #22c55e;"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const destIcon = L.divIcon({
  className: "custom-map-icon",
  html: `<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 0 10px #ef4444;"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const userIcon = L.divIcon({
  className: "custom-map-icon",
  html: `<div style="background:#3b82f6;width:18px;height:18px;border-radius:50%;border:3px solid white;box-shadow:0 0 12px #3b82f6;"></div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11]
});

const ORIGIN_PRESETS = [
  { name: "KIIT Campus 6 (Bhubaneswar)", latitude: 20.354563, longitude: 85.816109 },
  { name: "Patia Chowk", latitude: 20.360120, longitude: 85.823450 },
  { name: "Infocity / DLF Cybercity", latitude: 20.345800, longitude: 85.808900 },
  { name: "Jayadev Vihar Overbridge", latitude: 20.298000, longitude: 85.823000 }
];

const DESTINATION_PRESETS = [
  { name: "Bhubaneswar Railway Station", display_name: "Bhubaneswar Railway Station, Master Canteen, Khordha, Odisha", latitude: 20.2667774, longitude: 85.8435592 },
  { name: "Esplanade One Mall", display_name: "Esplanade One Mall, Rasulgarh, Bhubaneswar, Odisha", latitude: 20.296500, longitude: 85.864000 },
  { name: "Master Canteen Square", display_name: "Master Canteen Square, Janpath, Bhubaneswar, Odisha", latitude: 20.270000, longitude: 85.844000 },
  { name: "AIIMS Bhubaneswar", display_name: "AIIMS Hospital, Sijua, Patrapada, Bhubaneswar, Odisha", latitude: 20.228500, longitude: 85.776500 }
];

function SafeRoute({ token }) {
  const [selectedRouteId, setSelectedRouteId] = useState("S");
  const [destinationQuery, setDestinationQuery] = useState("");
  const [destinations, setDestinations] = useState([]);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [originName, setOriginName] = useState("KIIT Campus 6 (Bhubaneswar)");
  const [currentCoords, setCurrentCoords] = useState({ latitude: 20.354563, longitude: 85.816109 });

  const [searching, setSearching] = useState(false);
  const [computingRoutes, setComputingRoutes] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [comparedRoutes, setComparedRoutes] = useState([]);
  const [activeJourney, setActiveJourney] = useState(null);
  const [deviationAlert, setDeviationAlert] = useState(null);

  // Attempt to get user GPS coordinates on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCurrentCoords({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude
          });
          setOriginName("My Live Location (GPS)");
        },
        () => {
          // Default fallback to project operations hub: KIIT Bhubaneswar
          setCurrentCoords({ latitude: 20.354563, longitude: 85.816109 });
          setOriginName("KIIT Campus 6 (Bhubaneswar)");
        },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    }
  }, []);

  const handleUseGps = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return;
    }
    setError("");
    setMessage("Fetching live GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
        setCurrentCoords(coords);
        setOriginName("My Live Location (GPS)");
        setMessage("GPS location acquired.");
        if (selectedDestination) {
          calculateRoutesFor(coords, selectedDestination);
        }
      },
      (err) => {
        setError("Could not retrieve GPS location. Keeping current origin.");
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const handleSelectOriginPreset = (preset) => {
    const coords = { latitude: preset.latitude, longitude: preset.longitude };
    setCurrentCoords(coords);
    setOriginName(preset.name);
    setError("");
    if (selectedDestination) {
      calculateRoutesFor(coords, selectedDestination);
    }
  };

  const searchDestinations = async () => {
    setError("");
    setMessage("");
    setDestinations([]);
    setSelectedDestination(null);

    const query = destinationQuery.trim();
    if (query.length < 2) {
      setError("Please type at least 2 characters for destination search.");
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(
        `${API_URL}/destinations/search?q=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not search for this destination.");
      }
      setDestinations(data);
      if (data.length === 0) {
        setMessage("No places found matching your query. Try a city or landmark name.");
      }
    } catch (err) {
      setError(err.message || "Destination search failed.");
    } finally {
      setSearching(false);
    }
  };

  const calculateRoutesFor = async (sourceCoords, dest) => {
    setError("");
    setMessage("");
    setComputingRoutes(true);

    try {
      const response = await fetch(`${API_URL}/routes/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_latitude: sourceCoords.latitude,
          source_longitude: sourceCoords.longitude,
          destination_latitude: dest.latitude,
          destination_longitude: dest.longitude
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Route optimization failed.");
      }

      if (data.routes && data.routes.length > 0) {
        setComparedRoutes(data.routes);
        setSelectedRouteId(data.recommended_route_id || data.routes[0].id);
        setMessage("3 routes successfully calculated and ranked by DSA route engine: Safest, Balanced, and Fastest.");
      } else {
        setComparedRoutes([]);
        setError("No navigable road path found between the selected origin and destination. Please choose locations within the city network.");
      }
    } catch (err) {
      setError(err.message || "Could not calculate routes.");
      setComparedRoutes([]);
    } finally {
      setComputingRoutes(false);
    }
  };

  const handleSelectDestination = (dest) => {
    setSelectedDestination(dest);
    calculateRoutesFor(currentCoords, dest);
  };

  const selectedRouteObj = comparedRoutes.find((r) => r.id === selectedRouteId) || comparedRoutes[0];

  const startJourney = async () => {
    if (!token) {
      setError("Please log in before starting a journey.");
      return;
    }
    if (!selectedDestination) {
      setError("Please select a destination first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const createRes = await fetch(`${API_URL}/journeys/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          source_latitude: currentCoords.latitude,
          source_longitude: currentCoords.longitude,
          destination_latitude: selectedDestination.latitude,
          destination_longitude: selectedDestination.longitude
        })
      });
      const created = await createRes.json();
      if (!createRes.ok) throw new Error(created.detail || "Could not create safety journey.");

      const startRes = await fetch(`${API_URL}/journeys/${created.id}/start`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      const started = await startRes.json();
      if (!startRes.ok) throw new Error(started.detail || "Could not start safety journey.");

      setActiveJourney({
        id: created.id,
        status: "active",
        planned_path: selectedRouteObj ? selectedRouteObj.path_coordinates : [],
        destination: selectedDestination
      });
      setMessage("🛡️ Safety Journey Active! Real-time route deviation monitoring enabled.");
    } catch (err) {
      setError(err.message || "Failed to start safety journey.");
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateDeviation = async () => {
    if (!activeJourney || !activeJourney.planned_path.length) return;

    // Simulate position offset 200m away from planned path
    const firstPoint = activeJourney.planned_path[0];
    const offLat = firstPoint[0] + 0.0035;
    const offLon = firstPoint[1] + 0.0035;

    try {
      const res = await fetch(`${API_URL}/routes/deviation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          journey_id: activeJourney.id,
          current_latitude: offLat,
          current_longitude: offLon,
          planned_path: activeJourney.planned_path,
          threshold_meters: 100.0
        })
      });
      const data = await res.json();
      if (data.deviated) {
        setDeviationAlert(data);
      }
    } catch (err) {
      console.error("Deviation check error:", err);
    }
  };

  const handleEndJourney = async () => {
    if (!activeJourney) return;
    try {
      await fetch(`${API_URL}/journeys/${activeJourney.id}/complete`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveJourney(null);
      setDeviationAlert(null);
      setMessage("Journey safely completed and logged.");
    } catch (err) {
      console.error("Failed to complete journey:", err);
    }
  };

  return (
    <div className="safe-route-page">
      <header className="safe-route-heading">
        <div>
          <h2>Intelligent Safe Routing & Journey Monitor</h2>
          <p>DSA-powered multi-objective route optimization integrated with ML Spatio-Temporal Risk</p>
        </div>
      </header>

      {/* Starting Location (Origin) Panel */}
      <section className="route-details-panel">
        <div className="route-explanation">
          <p className="route-eyebrow">Step 1: Starting Point (Origin)</p>
          <h3>Where are you starting from?</h3>
        </div>

        <div className="current-origin-card">
          <div>
            <strong>📍 {originName}</strong>
            <span style={{ display: "block", color: "#64748b", fontSize: "12px", marginTop: "2px" }}>
              Coordinates: {currentCoords.latitude.toFixed(6)}, {currentCoords.longitude.toFixed(6)}
            </span>
          </div>
          <button
            type="button"
            className="preset-chip"
            onClick={handleUseGps}
            title="Use current GPS location"
          >
            📡 Use Live GPS
          </button>
        </div>

        <div className="preset-chips-row">
          <span style={{ fontSize: "12px", color: "#64748b", alignSelf: "center", marginRight: "4px" }}>
            Quick Select Origin:
          </span>
          {ORIGIN_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className={`preset-chip ${originName === p.name ? "active" : ""}`}
              onClick={() => handleSelectOriginPreset(p)}
            >
              📍 {p.name}
            </button>
          ))}
        </div>
      </section>

      {/* Destination Search Box */}
      <section className="route-details-panel">
        <div className="route-explanation">
          <p className="route-eyebrow">Step 2: Set Destination</p>
          <h3>Where are you traveling to?</h3>
        </div>

        <div className="preset-chips-row" style={{ marginBottom: "12px" }}>
          <span style={{ fontSize: "12px", color: "#64748b", alignSelf: "center", marginRight: "4px" }}>
            Quick Destinations:
          </span>
          {DESTINATION_PRESETS.map((dest, idx) => (
            <button
              key={idx}
              type="button"
              className={`preset-chip ${selectedDestination?.name === dest.name ? "active" : ""}`}
              onClick={() => handleSelectDestination(dest)}
            >
              🎯 {dest.name}
            </button>
          ))}
        </div>

        <div className="destination-search-row">
          <input
            type="text"
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") searchDestinations(); }}
            placeholder="Search destination (e.g. Master Canteen, Railway Station, City Mall)..."
          />
          <button
            type="button"
            className="start-route-button"
            onClick={searchDestinations}
            disabled={searching}
          >
            {searching ? "Searching..." : "🔍 Find Destination"}
          </button>
        </div>

        {destinations.length > 0 && (
          <div className="destination-results">
            <p className="destination-results-heading">Select Place to Calculate Routes:</p>
            {destinations.slice(0, 4).map((dest, idx) => (
              <button
                key={idx}
                type="button"
                className={`destination-result ${selectedDestination?.display_name === dest.display_name ? "selected" : ""}`}
                onClick={() => handleSelectDestination(dest)}
              >
                <strong>{dest.name}</strong>
                <span>{dest.display_name}</span>
              </button>
            ))}
          </div>
        )}

        {selectedDestination && (
          <div className="selected-destination">
            <strong>Selected Destination: {selectedDestination.name}</strong>
            <span>{selectedDestination.display_name}</span>
            <small>Coordinates: {selectedDestination.latitude}, {selectedDestination.longitude}</small>
          </div>
        )}

        {error && <p className="route-error">{error}</p>}
        {message && <p className="route-success">{message}</p>}
      </section>

      {computingRoutes && (
        <div className="route-notice">
          Calculating graph edge weights using Dijkstra / A* under safety sensitivity penalty β = 2.5...
        </div>
      )}

      {/* Route Cards */}
      {comparedRoutes.length > 0 && (
        <>
          <div className="route-preference-bar">
            <strong>Select Route Preference:</strong>
            <div className="route-cards">
              {comparedRoutes.map((route) => {
                const isSelected = (route.id === selectedRouteId);
                return (
                  <button
                    type="button"
                    key={route.id}
                    className={`route-card ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedRouteId(route.id)}
                  >
                    <div className="route-card-heading">
                      <strong>{route.name}</strong>
                      {route.recommended && <span className="rec-badge">⭐ Recommended</span>}
                      {isSelected && <span>✓</span>}
                    </div>

                    <div className={`route-risk-bar ${route.color}`} />

                    <div className="route-metrics">
                      <span>{route.distance}</span>
                      <span>{route.duration}</span>
                    </div>

                    <span className={`route-risk-badge ${route.color}`}>
                      <i />
                      Risk Score: {route.risk} · {route.level}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Interactive Route Map with Segment Risk Colors */}
          {selectedRouteObj && (
            <section className="route-map-panel">
              <div className="map-panel-header">
                <div>
                  <h3>Interactive Route Visualization ({selectedRouteObj.name})</h3>
                  <p>Segment-level risk breakdown: Green = Low Risk, Yellow = Moderate, Red = High Risk, Blue = Unassessed</p>
                </div>
                <div className="segment-legend">
                  <span><i style={{background: "#22c55e"}} /> Low Risk</span>
                  <span><i style={{background: "#eab308"}} /> Moderate</span>
                  <span><i style={{background: "#ef4444"}} /> High Risk</span>
                  <span><i style={{background: "#3b82f6"}} /> Unassessed</span>
                </div>
              </div>

              <div style={{ height: "420px", width: "100%", borderRadius: "12px", overflow: "hidden" }}>
                <MapContainer
                  center={[currentCoords.latitude, currentCoords.longitude]}
                  zoom={13}
                  scrollWheelZoom={true}
                  style={{ height: "100%", width: "100%" }}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />

                  {/* Auto-fit map viewport to active road route */}
                  {selectedRouteObj.path_coordinates && (
                    <MapBoundsUpdater coordinates={selectedRouteObj.path_coordinates} />
                  )}

                  <Marker position={[currentCoords.latitude, currentCoords.longitude]} icon={originIcon}>
                    <Popup>Your Location (Origin)</Popup>
                  </Marker>

                  {selectedDestination && (
                    <Marker position={[selectedDestination.latitude, selectedDestination.longitude]} icon={destIcon}>
                      <Popup>Destination: {selectedDestination.name}</Popup>
                    </Marker>
                  )}

                  {/* Base smooth continuous road polyline */}
                  {selectedRouteObj.path_coordinates && selectedRouteObj.path_coordinates.length > 1 && (
                    <Polyline
                      positions={selectedRouteObj.path_coordinates}
                      pathOptions={{
                        color: selectedRouteObj.color === "high" ? "#ef4444" : (selectedRouteObj.color === "medium" ? "#eab308" : "#22c55e"),
                        weight: 6,
                        opacity: 0.85,
                        lineJoin: "round",
                        lineCap: "round"
                      }}
                    />
                  )}

                  {/* Render real road-following geometry */}
                  {selectedRouteObj.segments && selectedRouteObj.segments.map((seg, sIdx) => {
                    const polyPositions = (seg.geometry && seg.geometry.length > 0)
                      ? seg.geometry
                      : [seg.start, seg.end];

                    return (
                      <Polyline
                        key={sIdx}
                        positions={polyPositions}
                        pathOptions={{
                          color: seg.color || "#22c55e",
                          weight: 8,
                          opacity: 0.9,
                          lineJoin: "round",
                          lineCap: "round"
                        }}
                      >
                        <Popup>
                          <strong>{seg.name || `Segment #${sIdx + 1}`}</strong> ({seg.distance_m}m)
                          <br />
                          Risk Assessment: {seg.risk_level === "UNASSESSED" ? "Low / Unassessed (No incident history)" : `${seg.risk_score}/100 (${seg.risk_level})`}
                          <br />
                          <small style={{ color: "#64748b" }}>
                            Road-following OpenStreetMap geometry ({polyPositions.length} curve points)
                          </small>
                        </Popup>
                      </Polyline>
                    );
                  })}
                </MapContainer>
              </div>

              {/* Explainable Risk Details */}
              {selectedRouteObj.xai_factors && selectedRouteObj.xai_factors.length > 0 && (
                <div className="xai-route-box">
                  <h4>💡 Explainable AI (XAI) Route Insights:</h4>
                  <ul>
                    {selectedRouteObj.xai_factors.map((factor, fIdx) => (
                      <li key={fIdx}>{factor}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Active Journey Controls */}
              <div className="journey-action-bar">
                {!activeJourney ? (
                  <button
                    type="button"
                    className="start-route-button start-journey-button"
                    onClick={startJourney}
                    disabled={loading}
                  >
                    {loading ? "Starting Journey..." : "🚀 Start Safety Journey with Live Monitoring"}
                  </button>
                ) : (
                  <div className="active-journey-box">
                    <div className="journey-live-status">
                      <span className="live-pulse" />
                      <strong>Safety Journey Active — Live Path Monitoring</strong>
                      <button type="button" className="end-journey-btn" onClick={handleEndJourney}>
                        End Journey
                      </button>
                    </div>

                    <div className="simulate-deviation-row">
                      <span>Test Route Deviation Detection:</span>
                      <button
                        type="button"
                        className="simulate-dev-btn"
                        onClick={handleSimulateDeviation}
                      >
                        ⚠️ Simulate Off-Route Deviation
                      </button>
                    </div>

                    {/* Prominent Route Deviation Warning */}
                    {deviationAlert && (
                      <div className="route-deviation-warning-banner">
                        <div className="dev-banner-top">
                          <span className="dev-icon">⚠️</span>
                          <div>
                            <strong>{deviationAlert.warning_message}</strong>
                            <p>
                              You are currently {deviationAlert.distance_from_route_m} meters away from your planned safety corridor.
                            </p>
                          </div>
                        </div>
                        <div className="dev-options-row">
                          <button
                            type="button"
                            className="dev-opt-btn recalculate"
                            onClick={() => {
                              setDeviationAlert(null);
                              handleSelectDestination(selectedDestination);
                            }}
                          >
                            🔄 Recalculate Safer Route
                          </button>
                          <button
                            type="button"
                            className="dev-opt-btn continue"
                            onClick={() => setDeviationAlert(null)}
                          >
                            ➡️ Continue Current Route
                          </button>
                          <button
                            type="button"
                            className="dev-opt-btn end"
                            onClick={handleEndJourney}
                          >
                            🛑 End Journey
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default SafeRoute;
