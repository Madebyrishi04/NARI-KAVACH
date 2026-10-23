
import { useState } from "react";
import "./Login.css";

const API_URL = "http://127.0.0.1:8000";

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email.trim());
      formData.append("password", password);

      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed.");
      }

      onLogin(data.access_token);
    } catch (err) {
      setError(err.message || "Unable to log in.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          password,
          phone_number: phoneNumber.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not create your account."
        );
      }

      setSuccess("Account created successfully! You can now log in.");
      setMode("login");
      setFullName("");
      setPhoneNumber("");
      setPassword("");
    } catch (err) {
      setError(err.message || "Unable to create your account.");
    } finally {
      setLoading(false);
    }
  };

  const isRegister = mode === "register";

  return (
    <div className="login-page">
      <header className="preview-bar">
        <div className="preview-left">
          <span className="preview-icon">◧</span>
          <span>frontend preview → click to switch screens</span>
        </div>

        <div className="preview-right">
          <button type="button" className="preview-button">
            Landing
          </button>
          <button type="button" className="preview-button active">
            Login
          </button>
          <button type="button" className="preview-button">
            App
          </button>
        </div>
      </header>

      <main className="login-content">
        <div className="login-card">
          <div className="login-heading">
            <div className="login-shield">♢</div>
            <h1>{isRegister ? "Create account" : "Log in"}</h1>
          </div>

          <form onSubmit={isRegister ? handleRegister : handleLogin}>
            {isRegister && (
              <>
                <label htmlFor="register-name">Full name</label>
                <div className="login-input-wrapper">
                  <span>♙</span>
                  <input
                    id="register-name"
                    type="text"
                    placeholder="Enter your full name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    minLength={2}
                    maxLength={100}
                    required
                  />
                </div>
              </>
            )}

            <label htmlFor="login-email">Email</label>
            <div className="login-input-wrapper">
              <span>✉</span>
              <input
                id="login-email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                maxLength={255}
                required
              />
            </div>

            {isRegister && (
              <>
                <label htmlFor="register-phone">Phone number (optional)</label>
                <div className="login-input-wrapper">
                  <span>☎</span>
                  <input
                    id="register-phone"
                    type="tel"
                    placeholder="Enter phone number"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    maxLength={20}
                  />
                </div>
              </>
            )}

            <label htmlFor="login-password">Password</label>
            <div className="login-input-wrapper">
              <span>♙</span>
              <input
                id="login-password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={isRegister ? 8 : undefined}
                required
              />
            </div>
            
          {!isRegister && (
            <div className="forgot-password-row">
              <button
                type="button"
                className="forgot-password-link"
                onClick={() => {
                  window.location.href = "/forgot-password";
                }}
              >
                Forgot password?
              </button>
            </div>
          )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading
                ? isRegister
                  ? "Creating account..."
                  : "Logging in..."
                : isRegister
                  ? "Create account"
                  : "Log in"}
            </button>
          </form>

          {error && (
            <p className="login-error" role="alert">
              {error}
            </p>
          )}

          {success && (
            <p className="login-success" role="status">
              {success}
            </p>
          )}

          <p className="login-switch">
            {isRegister
              ? "Already have an account?"
              : "New to SafeRoute?"}{" "}
            <button
              type="button"
              className="login-switch-button"
              onClick={() => switchMode(isRegister ? "login" : "register")}
            >
              {isRegister ? "Log in" : "Create account"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}

export default Login;
