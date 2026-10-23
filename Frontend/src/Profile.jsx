
import { useEffect, useState } from "react";
import "./Profile.css";

const API_URL = "http://127.0.0.1:8000";

function Profile({ token, onLogout }) {
  const [user, setUser] = useState({
    name: "",
    email: "",
    phone_number: "",
  });

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone_number: "",
  });

  const [activePanel, setActivePanel] = useState("");
  const [notifications, setNotifications] = useState({
    sos: true,
    journey: true,
    safety: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch(`${API_URL}/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Could not load profile details.");
        }

        const data = await response.json();

        const profile = {
          name: data.full_name || data.name || data.username || "",
          email: data.email || "",
          phone_number: data.phone_number || "",
        };

        setUser(profile);
        setFormData(profile);
      } catch (error) {
        setMessage(error.message);
        setMessageType("error");
      } finally {
        setLoading(false);
      }
    }

    if (token) {
      loadProfile();
    } else {
      setLoading(false);
      setMessage("Please log in to view your profile.");
      setMessageType("error");
    }
  }, [token]);

  const initials = user.name
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  function toggleNotification(key) {
    setNotifications((previous) => ({
      ...previous,
      [key]: !previous[key],
    }));
  }

  function handleInputChange(event) {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function saveProfile(event) {
    event.preventDefault();
    setMessage("");
    setMessageType("");

    if (!formData.name.trim() || !formData.email.trim()) {
      setMessage("Full name and email are required.");
      setMessageType("error");
      return;
    }

    if (formData.name.trim().length < 2) {
      setMessage("Full name must contain at least 2 characters.");
      setMessageType("error");
      return;
    }

    setSaving(true);

    try {
      const response = await fetch(`${API_URL}/users/me`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: formData.name.trim(),
          email: formData.email.trim(),
          phone_number: formData.phone_number.trim() || null,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not update profile."
        );
      }

      const updatedProfile = {
        name: data.full_name || formData.name.trim(),
        email: data.email || formData.email.trim(),
        phone_number: data.phone_number || "",
      };

      setUser(updatedProfile);
      setFormData(updatedProfile);
      setMessage("Profile updated successfully.");
      setMessageType("success");
      setActivePanel("");
    } catch (error) {
      setMessage(error.message || "Could not update profile.");
      setMessageType("error");
    } finally {
      setSaving(false);
    }
  }

  function renderPanel() {
    if (!activePanel) return null;

    return (
      <div className="profile-overlay" onClick={() => setActivePanel("")}>
        <section
          className="profile-modal"
          onClick={(event) => event.stopPropagation()}
        >
          <button
            className="profile-modal-close"
            onClick={() => setActivePanel("")}
            aria-label="Close"
            disabled={saving}
          >
            ×
          </button>

          {activePanel === "edit" && (
            <>
              <h2>Edit profile</h2>
              <p className="profile-muted">
                Update your account information.
              </p>

              <form onSubmit={saveProfile}>
                <label htmlFor="profile-name">Full name</label>
                <input
                  id="profile-name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  minLength={2}
                  maxLength={100}
                  required
                />

                <label htmlFor="profile-email">Email address</label>
                <input
                  id="profile-email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  maxLength={255}
                  required
                />

                <label htmlFor="profile-phone">Phone number</label>
                <input
                  id="profile-phone"
                  name="phone_number"
                  type="tel"
                  value={formData.phone_number}
                  onChange={handleInputChange}
                  maxLength={20}
                />

                {message && (
                  <p
                    className={
                      messageType === "success"
                        ? "profile-success"
                        : "profile-error"
                    }
                    role="status"
                  >
                    {message}
                  </p>
                )}

                <div className="profile-form-actions">
                  <button
                    type="button"
                    className="profile-cancel-button"
                    onClick={() => {
                      setFormData(user);
                      setMessage("");
                      setMessageType("");
                      setActivePanel("");
                    }}
                    disabled={saving}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="profile-save-button"
                    disabled={saving || loading}
                  >
                    {saving ? "Saving..." : "Save changes"}
                  </button>
                </div>
              </form>
            </>
          )}

          {activePanel === "notifications" && (
            <>
              <h2>Notification preferences</h2>
              <p className="profile-muted">
                Choose which alerts you want enabled in this interface.
              </p>

              {[
                ["sos", "SOS alerts", "Emergency-related alerts"],
                ["journey", "Journey updates", "Journey start and completion"],
                ["safety", "Safety updates", "General safety notifications"],
              ].map(([key, title, description]) => (
                <div className="preference-row" key={key}>
                  <div>
                    <strong>{title}</strong>
                    <p>{description}</p>
                  </div>
                  <button
                    className={`toggle-switch ${
                      notifications[key] ? "enabled" : ""
                    }`}
                    onClick={() => toggleNotification(key)}
                    aria-label={`Toggle ${title}`}
                    aria-pressed={notifications[key]}
                  >
                    <span />
                  </button>
                </div>
              ))}

              <p className="profile-muted">
                These preferences are currently local to this session and do
                not control server-side notifications.
              </p>
            </>
          )}

          {activePanel === "privacy" && (
            <>
              <h2>Privacy and data</h2>
              <p className="profile-muted">
                Review how SafeRoute handles your account and safety data.
              </p>
              <div className="privacy-item">
                <strong>Account information</strong>
                <p>Your name and email are loaded from your account.</p>
              </div>
              <div className="privacy-item">
                <strong>Location data</strong>
                <p>
                  Location access is used by features that need your position.
                  Allow browser location access only when needed.
                </p>
              </div>
              <div className="privacy-item">
                <strong>Account session</strong>
                <p>
                  Sign out to remove the saved access token from this browser.
                </p>
              </div>
            </>
          )}
        </section>
      </div>
    );
  }

  return (
    <section className="profile-page">
      <header className="profile-page-header">
        <div>
          <h1>Profile</h1>
          <p>Manage your account and preferences</p>
        </div>
      </header>

      <div className="profile-card">
        <div className="profile-identity">
          <div className="profile-avatar">
            {loading ? "…" : initials || "U"}
          </div>

          <div className="profile-user-info">
            <h2>{loading ? "Loading profile..." : user.name}</h2>
            <p>{user.email || "Email not available"}</p>
          </div>
        </div>

        {message && (
          <p
            className={
              messageType === "success"
                ? "profile-success"
                : "profile-error"
            }
            role="status"
          >
            {message}
          </p>
        )}

        <div className="profile-options">
          <button
            className="profile-option"
            onClick={() => {
              setFormData(user);
              setMessage("");
              setMessageType("");
              setActivePanel("edit");
            }}
          >
            <span>Edit profile</span>
            <span className="option-arrow">›</span>
          </button>

          <button
            className="profile-option"
            onClick={() => setActivePanel("notifications")}
          >
            <span>Notification preferences</span>
            <span className="option-arrow">›</span>
          </button>

          <button
            className="profile-option"
            onClick={() => setActivePanel("privacy")}
          >
            <span>Privacy and data</span>
            <span className="option-arrow">›</span>
          </button>

          <button
            className="profile-option signout-option"
            onClick={onLogout}
          >
            <span>Sign out</span>
            <span className="option-arrow">›</span>
          </button>
        </div>
      </div>

      {renderPanel()}
    </section>
  );
}

export default Profile;
