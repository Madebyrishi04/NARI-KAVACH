
import { useState } from "react";
import "./ResetPassword.css";

const API_URL = "http://127.0.0.1:8000";

function ResetPassword() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const token = new URLSearchParams(window.location.search).get("token");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    if (!token) {
      setMessage("This reset link is invalid or missing its token.");
      return;
    }

    if (password.length < 8) {
      setMessage("Password must contain at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/auth/reset-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token,
            new_password: password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to reset password.");
      }

      setMessage(
        "Password reset successfully. You can now log in with your new password."
      );
      setPassword("");
      setConfirmPassword("");
    } catch (error) {
      setMessage(error.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const isSuccess = message.startsWith("Password reset successfully.");

  return (
    <div className="reset-page">
      <main className="reset-card">
        <div className="reset-brand">
          <span className="reset-shield">♢</span>
          <span>SafeRoute</span>
        </div>

        <div className="reset-heading">
          <div className="reset-icon">🔐</div>
          <h1>Reset password</h1>
          <p>
            Create a new password to securely access your account.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="reset-form">
          <div className="reset-field">
            <label htmlFor="new-password">New password</label>
            <input
              id="new-password"
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </div>

          <div className="reset-field">
            <label htmlFor="confirm-password">
              Confirm new password
            </label>
            <input
              id="confirm-password"
              type="password"
              placeholder="Re-enter your new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </div>

          <button
            type="submit"
            className="reset-submit"
            disabled={loading}
          >
            {loading ? "Resetting password..." : "Reset password"}
          </button>
        </form>

        {message && (
          <div
            className={`reset-message ${
              isSuccess ? "reset-message-success" : "reset-message-error"
            }`}
            role="status"
          >
            <span>{isSuccess ? "✓" : "!"}</span>
            <p>{message}</p>
          </div>
        )}

        <a className="reset-back-link" href="/">
          ← Back to login
        </a>

        <p className="reset-security-note">
          <span>♢</span> Keep your account safe with a strong password.
        </p>
      </main>
    </div>
  );
}

export default ResetPassword;
