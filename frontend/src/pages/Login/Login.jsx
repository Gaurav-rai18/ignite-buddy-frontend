import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Megaphone,
  Link as LinkIcon,
  Bot,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import mascotImg from '../../assets/mascot.png';

export function Login({ onNotify }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('admin@campus.demo');
  const [password, setPassword] = useState('admin123');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [showForgotNotice, setShowForgotNotice] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const validate = () => {
    const errors = {};
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      errors.email = 'Please enter your email.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!password) {
      errors.password = 'Please enter your password.';
    } else if (password.length < 4) {
      errors.password = 'Password must be at least 4 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (isLoading) return;

    setErrorMessage('');
    setShowForgotNotice(false);

    if (!validate()) {
      return;
    }

    setIsLoading(true);
    try {
      await login({ email, password, rememberMe });
      if (onNotify) {
        onNotify('Signed in successfully as Administrator.');
      }
      navigate(from, { replace: true });
    } catch (err) {
      setErrorMessage(err.message || 'Unable to sign in right now. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMicrosoftSignIn = () => {
    if (onNotify) {
      onNotify('Microsoft SSO (Azure AD) is ready to be configured with campus tenant credentials.');
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-container">
        {/* Soft blue organic backdrop shape behind mascot */}
        <div className="mascot-backdrop-curve" aria-hidden="true" />

        {/* LEFT COLUMN: Visual & Branding */}
        <section className="login-brand-col" aria-label="Product highlights">
          <div className="login-brand-header">
            <div className="brand-accent-line" aria-hidden="true" />
            <h1 className="login-brand-title">
              <span className="brand-primary">Ignite Buddy</span>
              <span className="brand-sub">Admin Console</span>
            </h1>
            <p className="login-brand-description">
              Manage campus communications, resources and Buddy – all in one place.
            </p>
          </div>

          <div className="login-left-body">
            {/* 3 FEATURE ITEMS */}
            <div className="login-feature-list" role="list">
              <div className="login-feature-card" role="listitem">
                <div className="feature-icon-box" aria-hidden="true">
                  <Megaphone size={19} />
                </div>
                <div className="feature-text">
                  <strong>Broadcast</strong>
                  <span>announcements</span>
                </div>
              </div>

              <div className="login-feature-card" role="listitem">
                <div className="feature-icon-box" aria-hidden="true">
                  <LinkIcon size={19} />
                </div>
                <div className="feature-text">
                  <strong>Schedule</strong>
                  <span>OneDrive links</span>
                </div>
              </div>

              <div className="login-feature-card" role="listitem">
                <div className="feature-icon-box" aria-hidden="true">
                  <Bot size={19} />
                </div>
                <div className="feature-text">
                  <strong>Control</strong>
                  <span>Buddy availability</span>
                </div>
              </div>
            </div>

            {/* MASCOT & WELCOME BUBBLE */}
            <div className="login-mascot-wrapper">
              <div className="mascot-speech-bubble" role="note">
                <div className="speech-title">Welcome back!</div>
                <div className="speech-subtitle">Let’s keep everything in sync.</div>
                <div className="speech-sparkle" aria-hidden="true" />
              </div>

              <div className="mascot-figure-box">
                <img
                  src={mascotImg}
                  alt="Ignite Buddy Mascot"
                  className="mascot-image-large"
                  loading="eager"
                />
                <div className="mascot-ground-shadow" aria-hidden="true" />
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: Login Card */}
        <section className="login-form-col" aria-label="Sign in form">
          <div className="login-card">
            <div className="login-card-header">
              <h2>Sign in to continue</h2>
              <p>Access the Ignite Buddy Admin Console</p>
            </div>

            {errorMessage && (
              <div className="login-error-banner" role="alert">
                <AlertCircle size={16} aria-hidden="true" />
                <span>{errorMessage}</span>
              </div>
            )}

            {showForgotNotice && (
              <div className="login-info-banner" role="status">
                <HelpCircle size={16} aria-hidden="true" />
                <div>
                  <strong>Admin Password Reset</strong>
                  <p>
                    For security, administrator passwords must be reset via campus IT system or
                    Django manage.py CLI.
                  </p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate>
              {/* EMAIL FIELD */}
              <div className="form-group">
                <label htmlFor="login-email">Email</label>
                <div className={`input-with-icon ${fieldErrors.email ? 'has-error' : ''}`}>
                  <Mail size={18} className="field-icon" aria-hidden="true" />
                  <input
                    id="login-email"
                    type="email"
                    name="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (fieldErrors.email) {
                        setFieldErrors((prev) => ({ ...prev, email: '' }));
                      }
                    }}
                    placeholder="admin@yourdomain.com"
                    disabled={isLoading}
                    aria-invalid={Boolean(fieldErrors.email)}
                    aria-describedby={fieldErrors.email ? 'email-error' : undefined}
                  />
                </div>
                {fieldErrors.email && (
                  <span id="email-error" className="field-error-text">
                    {fieldErrors.email}
                  </span>
                )}
              </div>

              {/* PASSWORD FIELD */}
              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <div className={`input-with-icon ${fieldErrors.password ? 'has-error' : ''}`}>
                  <Lock size={18} className="field-icon" aria-hidden="true" />
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (fieldErrors.password) {
                        setFieldErrors((prev) => ({ ...prev, password: '' }));
                      }
                    }}
                    placeholder="Enter your password"
                    disabled={isLoading}
                    aria-invalid={Boolean(fieldErrors.password)}
                    aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    tabIndex={0}
                  >
                    {showPassword ? (
                      <EyeOff size={18} aria-hidden="true" />
                    ) : (
                      <Eye size={18} aria-hidden="true" />
                    )}
                  </button>
                </div>
                {fieldErrors.password && (
                  <span id="password-error" className="field-error-text">
                    {fieldErrors.password}
                  </span>
                )}
              </div>

              {/* OPTIONS ROW */}
              <div className="login-options-row">
                <label className="checkbox-label" htmlFor="remember-me">
                  <input
                    id="remember-me"
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>Remember me</span>
                </label>

                <button
                  type="button"
                  className="link-button forgot-link"
                  onClick={() => setShowForgotNotice((prev) => !prev)}
                >
                  Forgot password?
                </button>
              </div>

              {/* SUBMIT BUTTON */}
              <button
                type="submit"
                className="primary-button login-submit-button"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="btn-spinner" aria-hidden="true" />
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign in <ArrowRight size={17} aria-hidden="true" />
                  </>
                )}
              </button>

              {/* DIVIDER */}
              <div className="login-divider" aria-hidden="true">
                <span>OR</span>
              </div>

              {/* MICROSOFT SSO BUTTON */}
              <button
                type="button"
                className="secondary-button microsoft-btn"
                onClick={handleMicrosoftSignIn}
                disabled={isLoading}
              >
                <svg
                  className="ms-logo"
                  width="18"
                  height="18"
                  viewBox="0 0 21 21"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden="true"
                >
                  <rect x="1" y="1" width="9" height="9" fill="#F25022" />
                  <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
                  <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
                  <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
                </svg>
                <span>Sign in with Microsoft</span>
              </button>
            </form>

            <div className="login-card-footer">
              <small>This is a development demo for educational purposes only.</small>
            </div>
          </div>
        </section>

        {/* BOTTOM ROYAL BLUE CURVED FOOTER WAVE */}
        <div className="login-curved-footer">
          <svg
            className="footer-wave-svg"
            viewBox="0 0 1200 120"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path
              d="M0,50 C240,95 480,10 720,40 C960,70 1100,20 1200,45 L1200,120 L0,120 Z"
              fill="var(--color-primary)"
            />
          </svg>
          <div className="footer-wave-content">
            <div className="wave-text-left">
              <span className="footer-dash">—</span> Empowering smarter campus communication
            </div>
            <div className="wave-text-right">
              Ignite Buddy Admin Console <span className="footer-dash">—</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
