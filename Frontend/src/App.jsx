
import { useEffect, useState } from "react";

import Login from "./Login";
import ResetPassword from "./ResetPassword";
import ForgotPassword from "./ForgotPassword";
import SafetyMap from "./SafetyMap";
import SafeRoute from "./SafeRoute";
import Emergency from "./Emergency";
import Contacts from "./Contacts";
import Profile from "./Profile";

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

  // Load dashboard information after login.
  useEffect(() => {
    if (!token) {
      setDashboardLoading(false);
      return;
    }

    let cancelled = false;

    const headers = {
      Authorization: `Bearer ${token}`,
    };

    async function loadDashboard() {
      setDashboardLoading(true);

      try {
        const results = await Promise.allSettled([
          fetch(`${API_URL}/users/me`, { headers }),
          fetch(`${API_URL}/emergency-contacts/`, { headers }),
          fetch(`${API_URL}/sos/history`, { headers }),
          fetch(`${API_URL}/safety-reports/`, { headers }),
        ]);

        if (cancelled) return;

        const [
          userResult,
          contactsResult,
          sosResult,
          reportsResult,
        ] = results;

        // Load user information.
        if (
          userResult.status === "fulfilled" &&
          userResult.value.ok
        ) {
          const user = await userResult.value.json();

          if (cancelled) return;

          setUserName(
            user.full_name ||
              user.name ||
              user.username ||
              user.email?.split("@")[0] ||
              ""
          );
        }

        // Load trusted contacts.
        if (
          contactsResult.status === "fulfilled" &&
          contactsResult.value.ok
        ) {
          const data = await contactsResult.value.json();

          if (cancelled) return;

          const contacts = Array.isArray(data)
            ? data
            : data.contacts || data.items || [];

          setTrustedContactsCount(
            Array.isArray(contacts) ? contacts.length : 0
          );
        }

        // Load recent SOS alerts and safety reports.
        const activities = [];

        if (
          sosResult.status === "fulfilled" &&
          sosResult.value.ok
        ) {
          const data = await sosResult.value.json();

          const alerts = Array.isArray(data)
            ? data
            : data.alerts || data.items || data.history || [];

          if (Array.isArray(alerts)) {
            alerts.forEach((alert) => {
              activities.push({
                id: `sos-${alert.id}`,
                title: "SOS alert",
                description: `Status: ${
                  alert.status ||
                  (alert.resolved ? "Resolved" : "Recorded")
                }`,
                time:
                  alert.created_at ||
                  alert.triggered_at ||
                  alert.timestamp ||
                  null,
                type: "sos",
              });
            });
          }
        }

        if (
          reportsResult.status === "fulfilled" &&
          reportsResult.value.ok
        ) {
          const data = await reportsResult.value.json();

          const reports = Array.isArray(data)
            ? data
            : data.reports || data.items || [];

          if (Array.isArray(reports)) {
            reports.forEach((report) => {
              activities.push({
                id: `report-${report.id}`,
                title: "Safety report submitted",
                description:
                  report.description ||
                  report.title ||
                  "A safety report was recorded.",
                time: report.created_at || report.timestamp || null,
                type: "report",
              });
            });
          }
        }

        if (cancelled) return;

        activities.sort((a, b) => {
          const timeA = a.time ? new Date(a.time).getTime() : 0;
          const timeB = b.time ? new Date(b.time).getTime() : 0;
          return timeB - timeA;
        });

        setRecentActivity(activities.slice(0, 4));
      } catch (error) {
        console.error("Dashboard loading failed:", error);
      } finally {
        if (!cancelled) {
          setDashboardLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
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
    ["Emergency", "♙"],
    ["Contacts", "♧"],
    ["Analytics", "▥"],
    ["Profile", "♙"],
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

                  <div className="risk-level">
                    <span></span>
                    34&nbsp; · &nbsp;MEDIUM
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
                        points="0,125 90,123 180,120 270,112 360,94 450,70 540,55 620,50 700,47"
                        className="risk-line"
                      />
                    </svg>

                    <div className="chart-times">
                      <span>7pm</span>
                      <span>8pm</span>
                      <span>9pm</span>
                      <span>10pm</span>
                      <span>11pm</span>
                    </div>
                  </div>

                  <p className="chart-note">
                    Forecast estimate — not a guarantee.
                  </p>
                </div>
              </section>

              <section className="middle-dashboard">
                <div className="dashboard-card info-card">
                  <p className="card-label">Recommended route</p>

                  <h2>
                    Home <span>→</span> Metro station
                  </h2>

                  <div className="route-info">
                    <span>4.8 km</span>
                    <span>15 min</span>
                  </div>

                  <div className="safety-badge low">
                    <span></span>
                    27&nbsp; · &nbsp;LOW
                  </div>
                </div>

                <div className="dashboard-card info-card">
                  <p className="card-label">Nearby services</p>

                  <div className="service-row">
                    <span className="service-icon">⌖</span>
                    <span>Police station</span>
                    <span className="distance">—</span>
                  </div>

                  <div className="service-row">
                    <span className="service-icon">+</span>
                    <span>Hospital</span>
                    <span className="distance">—</span>
                  </div>

                  <div className="service-row">
                    <span className="service-icon">♧</span>
                    <span>Trusted contacts</span>
                    <span className="distance">
                      {trustedContactsCount}
                    </span>
                  </div>
                </div>

                <div className="dashboard-card info-card">
                  <p className="card-label">Recent activity</p>

                  {dashboardLoading ? (
                    <p className="activity">
                      Loading recent activity...
                    </p>
                  ) : recentActivity.length === 0 ? (
                    <p className="activity">
                      No recent SOS alerts or safety reports found.
                    </p>
                  ) : (
                    <div className="dashboard-activity-list">
                      {recentActivity.map((item) => (
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
                                ? new Date(item.time).toLocaleString()
                                : "Time unavailable"}
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
          ) : activeScreen === "Emergency" ? (
            <Emergency token={token} />
          ) : activeScreen === "Contacts" ? (
            <Contacts token={token} />
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
