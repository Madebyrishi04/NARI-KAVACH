
import { useState } from "react";
import "./ForgotPassword.css";

const API_URL = "http://127.0.0.1:8000";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/auth/forgot-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email: email.trim() }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to process your request."
        );
      }

      setMessage(
        data.message ||
          "If an account exists for this email, password reset instructions will be sent."
      );
      setEmail("");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-password-page">
      <div className="forgot-password-card">
        <div className="forgot-password-icon">🔐</div>

        <h1>Forgot password?</h1>
        <p>
          Enter the email address associated with your SafeRoute
          account. We'll send you a password reset link.
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="forgot-email">Email address</label>

          <input
            id="forgot-email"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send reset link"}
          </button>
        </form>

        {message && (
          <p className="forgot-password-success" role="status">
            {message}
          </p>
        )}

        {error && (
          <p className="forgot-password-error" role="alert">
            {error}
          </p>
        )}

        <a className="forgot-password-back" href="/">
          Back to login
        </a>
      </div>
    </div>
  );
}

export default ForgotPassword;
