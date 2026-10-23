
import { useState } from "react";

function LocationTracker({ token }) {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return;
    }

    setError("");
    setMessage("");
    setLoading(true);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const coordinates = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };

        setLocation(coordinates);

        try {
          const response = await fetch(
            "http://127.0.0.1:8000/locations/",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
              },
              body: JSON.stringify(coordinates)
            }
          );

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || "Could not save location.");
          }

          setMessage("Location successfully saved!");
        } catch (err) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      }
    );
  };

  return (
    <div>
      <h2>Live Location Tracking</h2>

      <button onClick={getCurrentLocation} disabled={loading}>
        {loading ? "Processing..." : "Detect My Location"}
      </button>

      {location && (
        <div>
          <p>Latitude: {location.latitude}</p>
          <p>Longitude: {location.longitude}</p>
        </div>
      )}

      {message && <p style={{ color: "green" }}>{message}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default LocationTracker;
