
import { useState } from "react";
import "./SafeRoute.css";

const routePreviews = [
  {
    id: "A",
    name: "Route A",
    distance: "4.2 km",
    duration: "12 min",
    risk: 72,
    level: "HIGH",
    color: "high",
  },
  {
    id: "B",
    name: "Route B",
    distance: "4.8 km",
    duration: "15 min",
    risk: 27,
    level: "LOW",
    color: "low",
  },
  {
    id: "C",
    name: "Route C",
    distance: "4.5 km",
    duration: "14 min",
    risk: 45,
    level: "MEDIUM",
    color: "medium",
  },
];

function SafeRoute({ token }) {
  const [selectedRoute, setSelectedRoute] = useState("B");

  const [destinationQuery, setDestinationQuery] = useState("");
  const [destinations, setDestinations] = useState([]);
  const [selectedDestination, setSelectedDestination] = useState(null);

  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [journey, setJourney] = useState(null);

  const getCurrentPosition = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(
          new Error("Your browser does not support location detection.")
        );
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => resolve(position.coords),
        () =>
          reject(
            new Error(
              "Location unavailable. Please allow location access and try again."
            )
          ),
        {
          enableHighAccuracy: true,
          timeout: 30000,
          maximumAge: 0,
        }
      );
    });

  const searchDestinations = async () => {
    setError("");
    setMessage("");
    setDestinations([]);
    setSelectedDestination(null);
    setJourney(null);

    const query = destinationQuery.trim();

    if (query.length < 2) {
      setError("Please type at least 2 characters for your destination.");
      return;
    }

    setSearching(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/destinations/search?q=${encodeURIComponent(query)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not search for this destination."
        );
      }

      setDestinations(data);

      if (data.length === 0) {
        setMessage("No matching places found. Try a more specific name.");
      }
    } catch (err) {
      setError(
        err.message || "Destination search failed. Please try again."
      );
    } finally {
      setSearching(false);
    }
  };

  const startJourney = async () => {
    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (!token) {
        throw new Error("Please log in again before starting a journey.");
      }

      if (!selectedDestination) {
        throw new Error("Please search for and select a destination first.");
      }

      const current = await getCurrentPosition();

      const createResponse = await fetch(
        "http://127.0.0.1:8000/journeys/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            source_latitude: current.latitude,
            source_longitude: current.longitude,
            destination_latitude: selectedDestination.latitude,
            destination_longitude: selectedDestination.longitude,
          }),
        }
      );

      const created = await createResponse.json();

      if (!createResponse.ok) {
        throw new Error(
          created.detail || "Could not create your safety journey."
        );
      }

      const startResponse = await fetch(
        `http://127.0.0.1:8000/journeys/${created.id}/start`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const started = await startResponse.json();

      if (!startResponse.ok) {
        throw new Error(
          started.detail || "Journey was created but could not be started."
        );
      }

      setJourney(started);
      setMessage("Your journey has started successfully.");
    } catch (err) {
      setError(err.message || "Could not start your journey.");
    } finally {
      setLoading(false);
    }
  };

  const selected = routePreviews.find(
    (route) => route.id === selectedRoute
  );

  return (
    <div className="safe-route-page">
      <header className="safe-route-heading">
        <div>
          <h2>Safe route</h2>
          <p>Compare route options and start a safety journey.</p>
        </div>
      </header>

      <div className="route-notice">
        These route cards are design previews, not routes calculated from
        real road or risk data. Your journey starts from your detected GPS
        location.
      </div>

      <div className="route-cards">
        {routePreviews.map((route) => (
          <button
            type="button"
            key={route.id}
            className={`route-card ${
              selectedRoute === route.id ? "selected" : ""
            }`}
            onClick={() => setSelectedRoute(route.id)}
          >
            <div className="route-card-heading">
              <strong>{route.name}</strong>
              {selectedRoute === route.id && <span>✓</span>}
            </div>

            <div className={`route-risk-bar ${route.color}`} />

            <div className="route-metrics">
              <span>{route.distance}</span>
              <span>{route.duration}</span>
            </div>

            <span className={`route-risk-badge ${route.color}`}>
              <i />
              {route.risk} · {route.level}
            </span>
          </button>
        ))}
      </div>

      <section className="route-details-panel">
        <div className="route-explanation">
          <p className="route-eyebrow">
            Selected option: {selected.name}
          </p>
          <h3>Start a safety journey</h3>
          <p>
            Search for a place, select the correct result, and allow location
            access when starting your journey.
          </p>
        </div>

        <div className="destination-fields">
          <label htmlFor="destination-search">
            Destination
          </label>

          <div className="destination-search-row">
            <input
              id="destination-search"
              type="text"
              value={destinationQuery}
              onChange={(event) => {
                setDestinationQuery(event.target.value);
                setSelectedDestination(null);
                setDestinations([]);
                setError("");
                setMessage("");
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  searchDestinations();
                }
              }}
             placeholder="Enter any destination, e.g. railway station"
            />

            <button
              type="button"
              className="start-route-button"
              onClick={searchDestinations}
              disabled={searching || loading}
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </div>

          {destinations.length > 0 && (
            <div className="destination-results">
              <p className="destination-results-heading">
                Choose your destination
              </p>

              {destinations.map((destination, index) => {
                const isSelected =
                  selectedDestination?.latitude === destination.latitude &&
                  selectedDestination?.longitude === destination.longitude;

                return (
                  <button
                    type="button"
                    key={`${destination.latitude}-${destination.longitude}-${index}`}
                    className={`destination-result ${
                      isSelected ? "selected" : ""
                    }`}
                    onClick={() => {
                      setSelectedDestination(destination);
                      setError("");
                      setMessage("");
                    }}
                  >
                    <strong>{destination.name}</strong>
                    <span>{destination.display_name}</span>
                    {isSelected && (
                      <small>✓ Destination selected</small>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {selectedDestination && (
            <div className="selected-destination">
              <strong>Selected destination</strong>
              <span>{selectedDestination.display_name}</span>
              <small>
                Coordinates: {selectedDestination.latitude},{" "}
                {selectedDestination.longitude}
              </small>
            </div>
          )}

          <button
            type="button"
            className="start-route-button start-journey-button"
            onClick={startJourney}
            disabled={loading || searching || !selectedDestination}
          >
            {loading ? "Starting journey..." : "➤ Start this journey"}
          </button>
        </div>

        {error && <p className="route-error">{error}</p>}
        {message && <p className="route-success">{message}</p>}

        {journey && (
          <div className="journey-status">
            <strong>Journey #{journey.id}</strong>
            <span>Status: {journey.status}</span>
            <span>
              Destination: {journey.destination_latitude},{" "}
              {journey.destination_longitude}
            </span>
          </div>
        )}

        <p className="route-disclaimer">
          The distance, duration, and risk values above are demonstration
          data. Destination search identifies places but does not calculate
          roads, turn-by-turn directions, or a verified safest route.
        </p>
      </section>
    </div>
  );
}

export default SafeRoute;
