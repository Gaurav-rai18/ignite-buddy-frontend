import React, { useState, useEffect } from 'react';
import {
  User as UserIcon,
  Mail,
  Building2,
  Briefcase,
  IdCard,
  Shield,
  KeyRound,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  Save,
  X,
  Edit3,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { profileService } from '../../services/profileService';
import { authService } from '../../services/authService';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { getUserDisplayName, getUserInitials, getUserRoleLabel } from '../../utils/user';

export function Profile({ onNotify }) {
  const { user } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    department: '',
    designation: '',
    profile_picture: '',
  });

  // Password Change State
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Sync profile data on mount or when user updates
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        username: user.username || '',
        email: user.email || '',
        department: user.department || 'TCS Ignite Training',
        designation: user.designation || 'Administrator',
        profile_picture: user.profile_picture || '',
      });
    }
  }, [user]);

  // Fetch freshest profile from backend
  useEffect(() => {
    let isMounted = true;
    profileService
      .getProfile()
      .then((data) => {
        if (isMounted && data) {
          authService.updateCurrentUser(data);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const roleLabel = getUserRoleLabel(user?.role, user?.is_superuser);

  const handleFieldChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      const payload = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        username: formData.username.trim() || `${formData.first_name} ${formData.last_name}`.trim(),
        email: formData.email.trim(),
        department: formData.department.trim(),
        designation: formData.designation.trim(),
        profile_picture: formData.profile_picture.trim(),
      };

      const updated = await profileService.updateProfile(payload);
      authService.updateCurrentUser(updated);
      setIsEditing(false);
      setSuccessMessage('Profile details updated and saved successfully.');
      if (onNotify) {
        onNotify('Profile details saved successfully.');
      }
    } catch (err) {
      const msg = err.response?.data?.email?.[0] || err.message || 'Failed to update profile.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setError('');
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        username: user.username || '',
        email: user.email || '',
        department: user.department || 'TCS Ignite Training',
        designation: user.designation || 'Administrator',
        profile_picture: user.profile_picture || '',
      });
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!passwordData.oldPassword) {
      setPasswordError('Please provide your current password.');
      return;
    }
    if (passwordData.newPassword.length < 8) {
      setPasswordError('New password must contain at least 8 characters.');
      return;
    }
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }

    setPasswordLoading(true);
    try {
      await profileService.changePassword({
        oldPassword: passwordData.oldPassword,
        newPassword: passwordData.newPassword,
      });

      setPasswordSuccess('Password changed successfully.');
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      if (onNotify) {
        onNotify('Account password successfully updated.');
      }
    } catch (err) {
      const msg =
        err.response?.data?.old_password?.[0] ||
        err.response?.data?.new_password?.[0] ||
        err.response?.data?.error ||
        err.message ||
        'Unable to change password. Please verify your current password.';
      setPasswordError(msg);
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="profile-page-container">
      <PageIntro
        eyebrow="ACCOUNT & IDENTITY MANAGEMENT"
        title="My Profile"
        subtitle="Manage your personal information, institutional affiliation, and account security."
      />

      {error && <ErrorBanner message={error} />}

      {successMessage && (
        <div
          className="profile-alert success"
          role="status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'var(--color-success-bg)',
            border: '1px solid var(--color-success)',
            color: 'var(--color-success)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '20px',
            fontSize: '13px',
            fontWeight: '600',
          }}
        >
          <CheckCircle2 size={18} aria-hidden="true" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* SECTION A: PROFILE HEADER */}
      <div className="panel profile-hero-panel" style={{ marginBottom: '22px' }}>
        <div className="profile-hero-content">
          <div className="profile-avatar-large">
            {formData.profile_picture ? (
              <img
                src={formData.profile_picture}
                alt={displayName}
                style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
              />
            ) : (
              <span>{initials}</span>
            )}
          </div>
          <div className="profile-hero-meta">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800' }}>{displayName}</h2>
              <span
                style={{
                  background: 'var(--color-primary-light)',
                  color: 'var(--color-primary)',
                  fontSize: '10.5px',
                  fontWeight: '700',
                  padding: '3px 8px',
                  borderRadius: '12px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {roleLabel}
              </span>
              <span
                style={{
                  background: user?.is_active !== false ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
                  color: user?.is_active !== false ? 'var(--color-success)' : 'var(--color-danger)',
                  fontSize: '10.5px',
                  fontWeight: '700',
                  padding: '3px 8px',
                  borderRadius: '12px',
                }}
              >
                {user?.is_active !== false ? '● ACTIVE ACCOUNT' : '● INACTIVE'}
              </span>
            </div>
            <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
              {user?.email} {user?.employee_id ? `· Employee ID: ${user.employee_id}` : ''}
            </p>
          </div>
        </div>

        <div className="profile-hero-actions">
          {!isEditing ? (
            <button
              type="button"
              className="primary-button"
              onClick={() => setIsEditing(true)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Edit3 size={15} aria-hidden="true" />
              <span>Edit Profile</span>
            </button>
          ) : (
            <button
              type="button"
              className="text-button"
              onClick={handleCancelEdit}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <X size={15} aria-hidden="true" />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>

      <div className="two-column profile-grid-layout">
        {/* LEFT COLUMN: Personal & Professional Information */}
        <div className="profile-column">
          {/* SECTION B & C: Personal & Professional Details */}
          <form onSubmit={handleSaveProfile}>
            <section className="panel" style={{ marginBottom: '22px' }}>
              <div className="panel-heading">
                <div>
                  <h3 style={{ margin: 0, fontSize: '15px' }}>Personal Information</h3>
                  <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                    Personal and account details
                  </p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
                <div className="field-group">
                  <label htmlFor="prof-first-name" style={{ fontSize: '12px', fontWeight: '600' }}>
                    First Name
                  </label>
                  <input
                    id="prof-first-name"
                    name="first_name"
                    type="text"
                    value={formData.first_name}
                    onChange={handleFieldChange}
                    disabled={!isEditing}
                    placeholder="e.g. Gaurav"
                    className="styled-input"
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="prof-last-name" style={{ fontSize: '12px', fontWeight: '600' }}>
                    Last Name
                  </label>
                  <input
                    id="prof-last-name"
                    name="last_name"
                    type="text"
                    value={formData.last_name}
                    onChange={handleFieldChange}
                    disabled={!isEditing}
                    placeholder="e.g. Rai"
                    className="styled-input"
                  />
                </div>
              </div>

              <div className="field-group" style={{ marginTop: '14px' }}>
                <label htmlFor="prof-email" style={{ fontSize: '12px', fontWeight: '600' }}>
                  Email Address
                </label>
                <input
                  id="prof-email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleFieldChange}
                  disabled={!isEditing}
                  required
                  className="styled-input"
                />
              </div>

              <div className="field-group" style={{ marginTop: '14px' }}>
                <label htmlFor="prof-avatar-url" style={{ fontSize: '12px', fontWeight: '600' }}>
                  Profile Picture URL (Optional)
                </label>
                <input
                  id="prof-avatar-url"
                  name="profile_picture"
                  type="url"
                  value={formData.profile_picture}
                  onChange={handleFieldChange}
                  disabled={!isEditing}
                  placeholder="https://example.com/avatar.jpg"
                  className="styled-input"
                />
                <small style={{ color: 'var(--color-text-secondary)', fontSize: '11px', marginTop: '4px', display: 'block' }}>
                  Leave empty to automatically use your initials ({initials}).
                </small>
              </div>

              <div className="panel-divider" style={{ margin: '20px 0 16px', borderTop: '1px solid var(--color-border-light)' }} />

              {/* SECTION C: Professional Details */}
              <h3 style={{ margin: 0, fontSize: '15px' }}>Professional Information</h3>
              <p style={{ margin: '4px 0 16px', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                Campus training role and organizational credentials
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="field-group">
                  <label htmlFor="prof-emp-id" style={{ fontSize: '12px', fontWeight: '600' }}>
                    Employee ID (Protected)
                  </label>
                  <input
                    id="prof-emp-id"
                    type="text"
                    value={user?.employee_id || 'Not assigned'}
                    disabled
                    style={{ background: 'var(--color-bg-cream)', cursor: 'not-allowed' }}
                    className="styled-input"
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="prof-org" style={{ fontSize: '12px', fontWeight: '600' }}>
                    Organization
                  </label>
                  <input
                    id="prof-org"
                    type="text"
                    value="Tata Consultancy Services - TCS Ignite"
                    disabled
                    style={{ background: 'var(--color-bg-cream)', cursor: 'not-allowed' }}
                    className="styled-input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '14px' }}>
                <div className="field-group">
                  <label htmlFor="prof-dept" style={{ fontSize: '12px', fontWeight: '600' }}>
                    Department
                  </label>
                  <input
                    id="prof-dept"
                    name="department"
                    type="text"
                    value={formData.department}
                    onChange={handleFieldChange}
                    disabled={!isEditing}
                    placeholder="e.g. TCS Ignite Training"
                    className="styled-input"
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="prof-desig" style={{ fontSize: '12px', fontWeight: '600' }}>
                    Designation
                  </label>
                  <input
                    id="prof-desig"
                    name="designation"
                    type="text"
                    value={formData.designation}
                    onChange={handleFieldChange}
                    disabled={!isEditing}
                    placeholder="e.g. Campus Lead / TA"
                    className="styled-input"
                  />
                </div>
              </div>

              {isEditing && (
                <div style={{ display: 'flex', gap: '10px', marginTop: '20px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    className="text-button"
                    onClick={handleCancelEdit}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="primary-button"
                    disabled={loading}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  >
                    <Save size={15} aria-hidden="true" />
                    <span>{loading ? 'Saving Changes...' : 'Save Changes'}</span>
                  </button>
                </div>
              )}
            </section>
          </form>

          {/* SECTION D: Account Information */}
          <section className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Account Information</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  System authorization and record metadata
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginTop: '14px' }}>
              <div className="account-meta-card">
                <span className="meta-label">User ID</span>
                <span className="meta-value">#{user?.id || '—'}</span>
              </div>
              <div className="account-meta-card">
                <span className="meta-label">Assigned Role</span>
                <span className="meta-value">{user?.role || 'ADMIN'}</span>
              </div>
              <div className="account-meta-card">
                <span className="meta-label">Account Created</span>
                <span className="meta-value">
                  {user?.date_joined
                    ? new Date(user.date_joined).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })
                    : 'System Init'}
                </span>
              </div>
              <div className="account-meta-card">
                <span className="meta-label">Assigned Batch</span>
                <span className="meta-value">{user?.full_batch_name || 'All Campus Batches'}</span>
              </div>
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN: Security & Activity */}
        <div className="profile-column">
          {/* SECTION E: Security / Password Change */}
          <section className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Security &amp; Password</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Update your authentication credentials securely
                </p>
              </div>
              <KeyRound size={18} style={{ color: 'var(--color-primary)' }} aria-hidden="true" />
            </div>

            {passwordError && (
              <div
                style={{
                  background: 'var(--color-danger-bg)',
                  color: 'var(--color-danger)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontWeight: '600',
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <AlertCircle size={15} />
                <span>{passwordError}</span>
              </div>
            )}

            {passwordSuccess && (
              <div
                style={{
                  background: 'var(--color-success-bg)',
                  color: 'var(--color-success)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontWeight: '600',
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <CheckCircle2 size={15} />
                <span>{passwordSuccess}</span>
              </div>
            )}

            <form onSubmit={handlePasswordChange} style={{ marginTop: '14px' }}>
              <div className="field-group">
                <label htmlFor="curr-pass" style={{ fontSize: '12px', fontWeight: '600' }}>
                  Current Password
                </label>
                <input
                  id="curr-pass"
                  type="password"
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData((prev) => ({ ...prev, oldPassword: e.target.value }))}
                  required
                  placeholder="Enter current password"
                  className="styled-input"
                />
              </div>

              <div className="field-group" style={{ marginTop: '12px' }}>
                <label htmlFor="new-pass" style={{ fontSize: '12px', fontWeight: '600' }}>
                  New Password
                </label>
                <input
                  id="new-pass"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData((prev) => ({ ...prev, newPassword: e.target.value }))}
                  required
                  minLength={8}
                  placeholder="Minimum 8 characters"
                  className="styled-input"
                />
              </div>

              <div className="field-group" style={{ marginTop: '12px' }}>
                <label htmlFor="conf-pass" style={{ fontSize: '12px', fontWeight: '600' }}>
                  Confirm New Password
                </label>
                <input
                  id="conf-pass"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData((prev) => ({ ...prev, confirmPassword: e.target.value }))}
                  required
                  minLength={8}
                  placeholder="Re-type new password"
                  className="styled-input"
                />
              </div>

              <button
                type="submit"
                className="primary-button"
                disabled={passwordLoading}
                style={{ width: '100%', marginTop: '16px', display: 'flex', justifyContent: 'center' }}
              >
                {passwordLoading ? 'Updating Password...' : 'Update Password'}
              </button>
            </form>
          </section>

          {/* SECTION F: Activity Information */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Session &amp; Activity</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Security session details and auditing status
                </p>
              </div>
              <Clock size={18} style={{ color: 'var(--color-text-secondary)' }} aria-hidden="true" />
            </div>

            <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="activity-item-compact">
                <span className="activity-dot live" />
                <div style={{ flex: 1 }}>
                  <b>Active In-Memory Session</b>
                  <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Session initiated at {user?.loginTime ? new Date(user.loginTime).toLocaleTimeString() : 'Current session'}
                  </p>
                </div>
                <span className="activity-pill">ONLINE</span>
              </div>

              <div className="activity-item-compact">
                <span className="activity-dot" />
                <div style={{ flex: 1 }}>
                  <b>Last Account Access</b>
                  <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    {user?.last_login
                      ? new Date(user.last_login).toLocaleString('en-GB')
                      : 'Initial administrator session'}
                  </p>
                </div>
              </div>

              <div className="activity-item-compact">
                <span className="activity-dot" />
                <div style={{ flex: 1 }}>
                  <b>Session Security Policy</b>
                  <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Tokens stored purely in memory. Auto-locks after 15 min of inactivity.
                  </p>
                </div>
                <span className="activity-pill safe">ACTIVE</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

