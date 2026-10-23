
import { useState } from "react";
import "./Emergency.css";

const API_URL = "http://127.0.0.1:8000";

function Emergency({ token }) {
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [alert, setAlert] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const getCurrentLocation = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(
          new Error("Location is not supported by this browser.")
        );
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (locationError) => {
          if (locationError.code === 1) {
            reject(
              new Error(
                "Location permission denied. Allow location access in your browser settings and try again."
              )
            );
          } else if (locationError.code === 2) {
            reject(
              new Error(
                "Your current location could not be determined. Please try again."
              )
            );
          } else if (locationError.code === 3) {
            reject(
              new Error(
                "Location request timed out. Please try again."
              )
            );
          } else {
            reject(new Error("Unable to retrieve your location."));
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 0,
        }
      );
    });

  const triggerSOS = async () => {
    if (!token) {
      setError("Please log in to trigger SOS.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      // 1. Capture the user's current GPS location.
      const location = await getCurrentLocation();

      // 2. Save the location for the authenticated user.
      const locationResponse = await fetch(`${API_URL}/locations/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(location),
      });

      const locationData = await locationResponse.json();

      if (!locationResponse.ok) {
        throw new Error(
          locationData.detail || "Could not save your location."
        );
      }

      // 3. Trigger SOS using the saved location.
      const response = await fetch(`${API_URL}/sos/trigger`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not trigger SOS.");
      }

      setAlert(data);
      setConfirming(false);
      setMessage(`Emergency alert #${data.id} was created.`);
    } catch (err) {
      setError(err.message || "Could not trigger SOS.");
    } finally {
      setLoading(false);
    }
  };

  const resolveSOS = async () => {
    if (!alert?.id || !token) return;

    if (
      !window.confirm(
        "Are you sure you are safe and want to resolve this alert?"
      )
    ) {
      return;
    }

    setResolving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/sos/resolve/${alert.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not resolve the alert.");
      }

      setAlert((previous) => ({
        ...previous,
        status: data.status,
      }));

      setMessage(`Emergency alert #${alert.id} was resolved.`);
    } catch (err) {
      setError(err.message || "Could not resolve the alert.");
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="emergency-page">
      <header className="emergency-heading">
        <h1>Emergency</h1>
        <p>
          SOS is triggered by you. Your browser must allow location access
          for the app to capture your current coordinates.
        </p>
      </header>

      <div className="emergency-layout">
        <section className="emergency-card">
          {alert?.status === "active" ? (
            <div className="active-alert">
              <span className="critical-badge">
                <span /> CRITICAL
              </span>

              <h2>Emergency alert active</h2>
              <p>
                Alert #{alert.id} · Status: {alert.status}
              </p>

              <button
                className="resolve-button"
                onClick={resolveSOS}
                disabled={resolving}
              >
                {resolving ? "Resolving..." : "Mark as resolved"}
              </button>
            </div>
          ) : (
            <>
              <button
                type="button"
                className="sos-button"
                onClick={() => {
                  setError("");
                  setMessage("");
                  setConfirming(true);
                }}
                disabled={loading || resolving}
              >
                <span className="sos-symbol">♧</span>
                <strong>SOS</strong>
                <small>tap to confirm</small>
              </button>

              <p className="sos-instruction">
                Confirm the alert to capture your current location and
                create an emergency alert.
              </p>
            </>
          )}

          {confirming && (
            <div
              className="confirmation-panel"
              role="dialog"
              aria-modal="true"
              aria-labelledby="sos-confirm-title"
            >
              <span className="warning-symbol">⚠</span>
              <h3 id="sos-confirm-title">Confirm emergency alert</h3>
              <p>
                Your current location will be requested and saved before
                the alert is created. Confirm only if you need emergency
                assistance. Contact notification is not guaranteed.
              </p>

              <div className="confirmation-actions">
                <button
                  className="cancel-button"
                  onClick={() => setConfirming(false)}
                  disabled={loading}
                >
                  Cancel
                </button>

                <button
                  className="confirm-button"
                  onClick={triggerSOS}
                  disabled={loading}
                >
                  {loading
                    ? "Capturing location..."
                    : "Confirm SOS"}
                </button>
              </div>
            </div>
          )}

          {alert?.status === "resolved" && (
            <div className="resolved-alert">
              <h2>Alert resolved</h2>
              <p>Emergency alert #{alert.id} has been resolved.</p>
              <button onClick={() => setAlert(null)}>
                Return to SOS
              </button>
            </div>
          )}

          {message && (
            <p className="emergency-success" role="status">
              {message}
            </p>
          )}

          {error && (
            <p className="emergency-error" role="alert">
              {error}
            </p>
          )}
        </section>

        <aside className="emergency-card official-emergency">
          <p>Official emergency number</p>
          <h2>☎ 112</h2>
          <p>
            India's official emergency service. This app supports you;
            it never replaces calling 112 directly.
          </p>
          <a className="call-112-button" href="tel:112">
            ☎ Call 112
          </a>
        </aside>
      </div>
    </div>
  );
}

export default Emergency;
