import React, { useState, useEffect } from "react";
import { Bot, Lock, User, ArrowRight, Loader2, AlertCircle, X, KeyRound } from "lucide-react";

/**
 * Desktop login gate for trainees.
 * Authenticates against the central server via local agent (POST /auth/login).
 * Supports regular sign-in and first-time / admin-reset password updates.
 */
export default function Login({
  onSubmit,
  onClose,
  error,
  busy,
  mustChangePassword = null,
  onClearMustChangePassword,
}) {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  const isPasswordChange = Boolean(mustChangePassword);
  const effectiveUserId = mustChangePassword?.userId || userId;

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && onClose && !busy) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, busy]);

  // Clear local validation error on input
  useEffect(() => {
    setValidationError("");
  }, [userId, password, newPassword, confirmPassword]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (busy) return;

    if (isPasswordChange) {
      if (!newPassword) {
        setValidationError("Please enter a new password.");
        return;
      }
      if (newPassword.length < 8) {
        setValidationError("New password must be at least 8 characters long.");
        return;
      }
      if (!confirmPassword) {
        setValidationError("Please confirm your new password.");
        return;
      }
      if (newPassword !== confirmPassword) {
        setValidationError("Passwords do not match. Please re-enter your new password.");
        return;
      }
      if (password && newPassword === password) {
        setValidationError("New password cannot be the same as your current/temporary password.");
        return;
      }
      onSubmit(effectiveUserId, password, newPassword);
    } else {
      if (!userId.trim() || !password) return;
      onSubmit(userId.trim(), password);
    }
  };

  const handleBackToSignIn = () => {
    setNewPassword("");
    setConfirmPassword("");
    setValidationError("");
    onClearMustChangePassword?.();
  };

  const displayError = validationError || error;

  return (
    <div
      className="login-backdrop"
      data-hit
      role="dialog"
      aria-modal="true"
      aria-label={isPasswordChange ? "Set New Password" : "Sign in"}
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose && !busy) {
          onClose();
        }
      }}
    >
      <div className="login-card" data-hit onClick={(e) => e.stopPropagation()}>
        {onClose && (
          <button
            type="button"
            className="login-btn-close"
            onClick={onClose}
            aria-label="Close"
            disabled={busy}
            data-hit
          >
            <X size={16} aria-hidden="true" />
          </button>
        )}

        <div className="login-brand">
          <div className={`login-brand-icon ${isPasswordChange ? "key-icon" : ""}`} aria-hidden="true">
            {isPasswordChange ? <KeyRound size={20} /> : <Bot size={20} />}
          </div>
          <div className="login-brand-text">
            <h2>{isPasswordChange ? "Set New Password" : "TCS Ignite Buddy"}</h2>
            <p>
              {isPasswordChange
                ? mustChangePassword?.name
                  ? `Welcome, ${mustChangePassword.name}`
                  : "First-time sign-in or password reset"
                : "Sign in to your trainee assistant"}
            </p>
          </div>
        </div>

        {isPasswordChange && (
          <div className="login-notice">
            Your account requires a new password before you can proceed. Please create a secure password below.
          </div>
        )}

        {displayError && (
          <div className="login-error-banner" role="alert">
            <AlertCircle size={15} style={{ flexShrink: 0, marginTop: "1px" }} aria-hidden="true" />
            <span>{displayError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {isPasswordChange ? (
            <>
              <div className="login-badge-user">
                <User size={13} aria-hidden="true" />
                <span>Account: <strong>{effectiveUserId}</strong></span>
              </div>

              <div className="login-field">
                <label htmlFor="login-new-password">New Password</label>
                <div className="login-input-wrap">
                  <Lock size={14} className="login-input-icon" aria-hidden="true" />
                  <input
                    id="login-new-password"
                    type="password"
                    autoFocus
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    autoComplete="new-password"
                    placeholder="Enter new password (min. 8 characters)"
                    className="login-input"
                    disabled={busy}
                  />
                </div>
              </div>

              <div className="login-field">
                <label htmlFor="login-confirm-password">New Password Again</label>
                <div className="login-input-wrap">
                  <Lock size={14} className="login-input-icon" aria-hidden="true" />
                  <input
                    id="login-confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    placeholder="Re-enter new password"
                    className="login-input"
                    disabled={busy}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="login-btn-submit"
                disabled={busy || !newPassword || !confirmPassword}
              >
                {busy ? (
                  <>
                    <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} aria-hidden="true" />
                    <span>Updating password...</span>
                  </>
                ) : (
                  <>
                    <span>Update Password & Sign In</span>
                    <ArrowRight size={14} aria-hidden="true" />
                  </>
                )}
              </button>

              <button
                type="button"
                className="login-btn-back"
                onClick={handleBackToSignIn}
                disabled={busy}
              >
                Cancel and back to sign in
              </button>
            </>
          ) : (
            <>
              <div className="login-field">
                <label htmlFor="login-userid">Email or 7-Digit Employee ID</label>
                <div className="login-input-wrap">
                  <User size={14} className="login-input-icon" aria-hidden="true" />
                  <input
                    id="login-userid"
                    autoFocus
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    autoComplete="username"
                    placeholder="e.g. 2109845 or trainee1@tcs.com"
                    className="login-input"
                    disabled={busy}
                  />
                </div>
              </div>

              <div className="login-field">
                <label htmlFor="login-password">Password</label>
                <div className="login-input-wrap">
                  <Lock size={14} className="login-input-icon" aria-hidden="true" />
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    placeholder="Enter your account password"
                    className="login-input"
                    disabled={busy}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="login-btn-submit"
                disabled={busy || !userId.trim() || !password}
              >
                {busy ? (
                  <>
                    <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} aria-hidden="true" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign in</span>
                    <ArrowRight size={14} aria-hidden="true" />
                  </>
                )}
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
