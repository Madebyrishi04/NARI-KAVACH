
import { useEffect, useState } from "react";

import Login from "./Login";
import ResetPassword from "./ResetPassword";
import ForgotPassword from "./ForgotPassword";
import SafetyMap from "./SafetyMap";
import SafeRoute from "./SafeRoute";
import Emergency from "./Emergency";
import Contacts from "./Contacts";
import Profile from "./Profile";
import Analytics from "./Analytics";
import NLPAssistant from "./NLPAssistant";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const [activeScreen, setActiveScreen] = useState("Dashboard");
  const [userName, setUserName] = useState("");
  const [trustedContactsCount, setTrustedContactsCount] = useState(0);
  const [recentActivity, setRecentActivity] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);

  const handleLogin = (accessToken) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setActiveScreen("Dashboard");
    setUserName("");
    setTrustedContactsCount(0);
    setRecentActivity([]);
    setDashboardData(null);
  };

  // Handle password pages before showing the login page.
  const isResetPasswordPage =
    window.location.pathname === "/reset-password";

  const isForgotPasswordPage =
    window.location.pathname === "/forgot-password";

  if (isResetPasswordPage) {
    return <ResetPassword />;
  }

  if (isForgotPasswordPage) {
    return <ForgotPassword />;
  }

  // Load live dynamic dashboard information after login.
  useEffect(() => {
    if (!token) {
      setDashboardLoading(false);
      return;
    }

    let cancelled = false;

    const headers = {
      Authorization: `Bearer ${token}`,
    };

    async function loadDashboard(isInitial = false) {
      if (isInitial) {
        setDashboardLoading(true);
      }

      try {
        let lat = 20.354563;
        let lon = 85.816109;

        if (typeof window !== "undefined" && "geolocation" in navigator) {
          try {
            const pos = await new Promise((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject, {
                timeout: 3000,
                maximumAge: 60000,
              });
            });
            if (pos && pos.coords) {
              lat = pos.coords.latitude;
              lon = pos.coords.longitude;
            }
          } catch (e) {
            // Use default coordinates if permission not granted
          }
        }

        if (cancelled) return;

        const liveRes = await fetch(
          `${API_URL}/dashboard/live?latitude=${lat}&longitude=${lon}`,
          { headers }
        );

        if (cancelled) return;

        if (liveRes.ok) {
          const liveData = await liveRes.json();
          if (cancelled) return;

          setDashboardData(liveData);
          if (liveData.user_name) {
            setUserName(liveData.user_name);
          }
          if (liveData.nearby_services?.trusted_contacts_count !== undefined) {
            setTrustedContactsCount(
              liveData.nearby_services.trusted_contacts_count
            );
          }
          if (Array.isArray(liveData.recent_activity)) {
            setRecentActivity(liveData.recent_activity);
          }
        } else {
          // Fallback to basic me endpoint if live dashboard fails
          const userRes = await fetch(`${API_URL}/users/me`, { headers });
          if (userRes.ok && !cancelled) {
            const user = await userRes.json();
            setUserName(
              user.full_name ||
                user.name ||
                user.username ||
                user.email?.split("@")[0] ||
                ""
            );
          }
        }
      } catch (error) {
        console.error("Live dashboard loading failed:", error);
      } finally {
        if (!cancelled && isInitial) {
          setDashboardLoading(false);
        }
      }
    }

    loadDashboard(true);

    // Live refresh every 30 seconds
    const intervalId = setInterval(() => {
      loadDashboard(false);
    }, 30000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [token]);

  // Show login when the user is not authenticated.
  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  const navigationItems = [
    ["Dashboard", "⌂"],
    ["Safety map", "⌖"],
    ["Safe route", "⌁"],
    ["AI Assistant", "⚡"],
    ["Emergency", "🚨"],
    ["Contacts", "👥"],
    ["Analytics", "📊"],
    ["Profile", "👤"],
  ];

  return (
    <div className="safety-app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">♢</div>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map(([label, icon]) => (
            <button
              key={label}
              type="button"
              className={`side-link ${
                activeScreen === label ? "active" : ""
              }`}
              onClick={() => setActiveScreen(label)}
            >
              <span>{icon}</span>
              <small>{label}</small>
            </button>
          ))}
        </nav>
      </aside>

      <div className="app-main">
        <header className="preview-bar">
          <div className="preview-left">
            <span className="preview-icon">◧</span>
            <span>
              Walk with confidence. Live without fear. The world is
              yours to explore.
            </span>
          </div>

          <div className="preview-right">
            <button
              type="button"
              className="preview-button"
              onClick={() => setActiveScreen("Dashboard")}
              title="Go to dashboard"
            >
              Landing
            </button>

            <button
              type="button"
              className="preview-button"
              onClick={handleLogout}
              title="Sign out and return to login"
            >
              Login
            </button>

            <button
              type="button"
              className={`preview-button ${
                activeScreen === "Dashboard" ? "active" : ""
              }`}
              onClick={() => setActiveScreen("Dashboard")}
              title="Open SafeRoute dashboard"
            >
              App
            </button>
          </div>
        </header>

        <main className="dashboard">
          {activeScreen === "Dashboard" ? (
            <>
              <header className="dashboard-header">
                <div>
                  <h1>
                    {new Date().getHours() < 12
                      ? "Good morning"
                      : new Date().getHours() < 17
                      ? "Good afternoon"
                      : "Good evening"}
                    {userName ? `, ${userName}` : ""}
                  </h1>

                  <p>Here's your current safety status</p>
                </div>

                <button
                  className="logout-btn"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </header>

              <section className="top-dashboard">
                <div className="dashboard-card risk-card">
                  <p className="card-label">Current risk</p>

                  <button
                    type="button"
                    className="risk-circle"
                    onClick={() => setActiveScreen("Emergency")}
                    aria-label="Open emergency SOS controls"
                  >
                    <span className="risk-inner">
                      <span className="sos-icon">♧</span>
                      <strong>SOS</strong>
                      <span className="sos-hint">
                        click to
                        <br />
                        open emergency
                      </span>
                    </span>
                  </button>

                  <div
                    className={`risk-level ${
                      dashboardData?.current_risk?.color || "low"
                    }`}
                  >
                    <span></span>
                    {dashboardData?.current_risk?.score ?? 15}&nbsp; · &nbsp;
                    {dashboardData?.current_risk?.level || "LOW"}
                  </div>
                </div>

                <div className="dashboard-card prediction-card">
                  <p className="card-label">
                    Predicted risk — next 4 hours
                  </p>

                  <div className="chart">
                    <svg
                      viewBox="0 0 700 180"
                      preserveAspectRatio="none"
                    >
                      <line
                        x1="0"
                        y1="35"
                        x2="700"
                        y2="35"
                        className="chart-grid"
                      />

                      <line
                        x1="0"
                        y1="90"
                        x2="700"
                        y2="90"
                        className="chart-grid"
                      />

                      <line
                        x1="0"
                        y1="145"
                        x2="700"
                        y2="145"
                        className="chart-grid"
                      />

                      <polyline
                        points={
                          dashboardData?.prediction?.svg_points ||
                          "0,140 175,139 350,138 525,136 700,134"
                        }
                        className="risk-line"
                      />
                    </svg>

                    <div className="chart-times">
                      {(
                        dashboardData?.prediction?.labels || [
                          "1pm",
                          "2pm",
                          "3pm",
                          "4pm",
                          "5pm",
                        ]
                      ).map((label, idx) => (
                        <span key={idx}>{label}</span>
                      ))}
                    </div>
                  </div>

                  <p className="chart-note">
                    {dashboardData?.prediction
                      ? `Forecast estimate · Peak around ${dashboardData.prediction.peak_hour} (${dashboardData.prediction.trend.toLowerCase()} trend).`
                      : "Forecast estimate — not a guarantee."}
                  </p>
                </div>
              </section>

              <section className="middle-dashboard">
                <div
                  className="dashboard-card info-card interactive-card"
                  onClick={() => setActiveScreen("Safe route")}
                  title="Click to view full Safe Route navigation"
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <p className="card-label">Recommended route</p>
                    <span style={{ fontSize: "11px", color: "#7164ff" }}>
                      Open map →
                    </span>
                  </div>

                  <h2>
                    {dashboardData?.recommended_route?.source || "KIIT Campus 6"}{" "}
                    <span>→</span>{" "}
                    {dashboardData?.recommended_route?.destination || "Patia Chowk"}
                  </h2>

                  <div className="route-info">
                    <span>
                      {dashboardData?.recommended_route?.distance || "1.4 km"}
                    </span>
                    <span>
                      {dashboardData?.recommended_route?.duration || "3 min"}
                    </span>
                  </div>

                  <div
                    className={`safety-badge ${
                      dashboardData?.recommended_route?.color || "low"
                    }`}
                  >
                    <span></span>
                    {dashboardData?.recommended_route?.risk_score ?? 15}&nbsp; · &nbsp;
                    {dashboardData?.recommended_route?.risk_level || "LOW"}
                  </div>
                </div>

                <div className="dashboard-card info-card">
                  <p className="card-label">Nearby services</p>

                  <div className="service-row">
                    <span className="service-icon">⌖</span>
                    <div className="service-name-container">
                      <span>
                        {dashboardData?.nearby_services?.police_station?.name ||
                          "Police station"}
                      </span>
                    </div>
                    <span className="distance">
                      {dashboardData?.nearby_services?.police_station?.distance ||
                        "—"}
                    </span>
                  </div>

                  <div className="service-row">
                    <span className="service-icon">+</span>
                    <div className="service-name-container">
                      <span>
                        {dashboardData?.nearby_services?.hospital?.name ||
                          "Hospital"}
                      </span>
                    </div>
                    <span className="distance">
                      {dashboardData?.nearby_services?.hospital?.distance ||
                        "—"}
                    </span>
                  </div>

                  <div
                    className="service-row interactive"
                    onClick={() => setActiveScreen("Contacts")}
                    style={{ cursor: "pointer" }}
                    title="Manage Emergency Contacts"
                  >
                    <span className="service-icon">♧</span>
                    <span>Trusted contacts</span>
                    <span className="distance">
                      {dashboardData?.nearby_services?.trusted_contacts_count ??
                        trustedContactsCount}
                      {(dashboardData?.nearby_services
                        ?.trusted_contacts_count ??
                        trustedContactsCount) === 0
                        ? " (+ Add)"
                        : ""}
                    </span>
                  </div>
                </div>

                <div className="dashboard-card info-card">
                  <p className="card-label">Recent activity</p>

                  {dashboardLoading && !dashboardData ? (
                    <p className="activity">
                      Loading recent activity...
                    </p>
                  ) : (dashboardData?.recent_activity?.length ??
                      recentActivity.length) === 0 ? (
                    <p className="activity">
                      No recent SOS alerts or safety reports found.
                    </p>
                  ) : (
                    <div className="dashboard-activity-list">
                      {(dashboardData?.recent_activity || recentActivity)
                        .slice(0, 3)
                        .map((item) => (
                          <div
                            className="dashboard-activity-item"
                            key={item.id}
                          >
                            <span
                              className={`activity-dot ${
                                item.type === "sos"
                                  ? "activity-sos"
                                  : "activity-report"
                              }`}
                            />

                            <div className="dashboard-activity-content">
                              <strong>{item.title}</strong>
                              <p>{item.description}</p>
                              <small>
                                {item.time &&
                                !Number.isNaN(
                                  new Date(item.time).getTime()
                                )
                                  ? new Date(
                                      item.time
                                    ).toLocaleTimeString([], {
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    }) +
                                    " · " +
                                    new Date(
                                      item.time
                                    ).toLocaleDateString()
                                  : "Recent"}
                              </small>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </section>
            </>
          ) : activeScreen === "Safety map" ? (
            <SafetyMap token={token} />
          ) : activeScreen === "Safe route" ? (
            <SafeRoute token={token} />
          ) : activeScreen === "AI Assistant" ? (
            <NLPAssistant
              token={token}
              onTriggerEmergency={() => setActiveScreen("Emergency")}
            />
          ) : activeScreen === "Emergency" ? (
            <Emergency token={token} />
          ) : activeScreen === "Contacts" ? (
            <Contacts token={token} />
          ) : activeScreen === "Analytics" ? (
            <Analytics token={token} />
          ) : activeScreen === "Profile" ? (
            <Profile token={token} onLogout={handleLogout} />
          ) : (
            <section>
              <header className="dashboard-header">
                <div>
                  <h1>{activeScreen}</h1>
                  <p>Personal Safety Application</p>
                </div>

                <button
                  className="logout-btn"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </header>

              <div className="dashboard-card info-card">
                <p className="card-label">{activeScreen} screen</p>
                <p>
                  This screen is ready for its next implementation
                  step.
                </p>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
