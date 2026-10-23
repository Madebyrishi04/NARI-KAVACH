import { useState, useEffect } from "react";

function AlertHistory({ token }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAlerts = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/sos/history",
        {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to load alert history."
        );
      }

      setAlerts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sos/resolve/${alertId}`,
        {
          method: "PUT",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to resolve alert."
        );
      }

      // Refresh alert history after resolving
      fetchAlerts();

    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [token]);

  return (
    <div>
      <h2>SOS Alert History</h2>

      <button onClick={fetchAlerts} disabled={loading}>
        {loading ? "Loading..." : "Refresh History"}
      </button>

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}

      {!loading && !error && alerts.length === 0 && (
        <p>No emergency alerts found.</p>
      )}

      {alerts.map((alert) => (
        <div
          key={alert.id}
          style={{
            border: "1px solid #ccc",
            padding: "12px",
            margin: "10px 0",
            borderRadius: "8px"
          }}
        >
          <p>
            <strong>Alert ID:</strong> {alert.id}
          </p>

          <p>
            <strong>Status:</strong>{" "}
            <span
              style={{
                color:
                  alert.status === "active"
                    ? "red"
                    : "green"
              }}
            >
              {alert.status.toUpperCase()}
            </span>
          </p>

          <p>
            <strong>Created:</strong>{" "}
            {new Date(alert.created_at).toLocaleString()}
          </p>

          <p>
            <strong>Location ID:</strong>{" "}
            {alert.location_id}
          </p>

          {alert.status === "active" && (
            <button
              onClick={() => resolveAlert(alert.id)}
              style={{
                backgroundColor: "green",
                color: "white",
                padding: "8px 15px",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer"
              }}
            >
              Resolve Alert
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

export default AlertHistory;