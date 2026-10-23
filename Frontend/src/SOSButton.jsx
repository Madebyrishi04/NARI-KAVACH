
import { useState } from "react";

function SOSButton({ token }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const triggerSOS = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to trigger an emergency SOS alert?"
    );

    if (!confirmed) {
      return;
    }

    setLoading(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/sos/trigger",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not trigger SOS.");
      }

      setMessage(
        `SOS alert created successfully! Alert ID: ${data.id}`
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Emergency SOS</h2>

      <button
        onClick={triggerSOS}
        disabled={loading}
        style={{
          backgroundColor: "red",
          color: "white",
          padding: "15px 30px",
          border: "none",
          borderRadius: "8px",
          fontSize: "18px",
          cursor: "pointer"
        }}
      >
        {loading ? "Sending Alert..." : "SOS"}
      </button>

      {message && <p style={{ color: "green" }}>{message}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default SOSButton;
