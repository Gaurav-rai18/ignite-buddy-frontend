import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Palette,
  Bell,
  Shield,
  Database,
  Save,
  CheckCircle2,
  Download,
  AlertCircle,
  Sun,
  Moon,
  Laptop,
} from 'lucide-react';
import { settingsService } from '../../services/settingsService';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export function Settings({ onNotify }) {
  const [activeTab, setActiveTab] = useState('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [prefs, setPrefs] = useState({
    workspace_name: 'TCS Ignite Campus Workspace',
    timezone: 'Asia/Kolkata',
    date_format: 'DD/MM/YYYY',
    time_format: '12-hour',
    theme: 'light',
    sidebar_default_expanded: true,
    notify_announcements: true,
    notify_schedules: true,
    notify_system_alerts: true,
    session_timeout_minutes: 15,
    password_min_length: 8,
    require_special_char: true,
    academic_year: '2026-2027',
    current_semester: 'Term 1 (Foundation & Core Tech)',
    institution_name: 'TCS Ignite Learning Center',
    default_slot_duration_mins: 60,
    data_retention_days: 365,
    auto_archive_broadcasts: true,
  });

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    settingsService
      .getPreferences()
      .then((data) => {
        if (isMounted && data) {
          setPrefs((prev) => ({ ...prev, ...data }));
          // Apply initial theme from stored preferences
          if (data.theme) {
            applyTheme(data.theme);
          }
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to fetch system preferences.');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const applyTheme = (themeName) => {
    if (themeName === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('ignite_admin_theme', themeName);
  };

  const handleFieldChange = (field, value) => {
    setPrefs((prev) => ({ ...prev, [field]: value }));
    if (field === 'theme') {
      applyTheme(value);
    }
  };

  const handleSavePreferences = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const res = await settingsService.updatePreferences(prefs);
      if (res && res.preferences) {
        setPrefs((prev) => ({ ...prev, ...res.preferences }));
      }
      setSuccess('System preferences saved and persisted successfully.');
      if (onNotify) {
        onNotify('System preferences successfully saved.');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to update preferences.');
    } finally {
      setSaving(false);
    }
  };

  const handleExportUsers = async () => {
    setExporting(true);
    try {
      await settingsService.exportUsersCSV();
      if (onNotify) {
        onNotify('User directory CSV downloaded.');
      }
    } catch (err) {
      setError('Failed to export user CSV.');
    } finally {
      setExporting(false);
    }
  };

  const handleExportAudit = async () => {
    setExporting(true);
    try {
      const audit = await settingsService.exportAuditSummary();
      const blob = new Blob([JSON.stringify(audit, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ignite_audit_summary_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      if (onNotify) {
        onNotify('System audit JSON downloaded.');
      }
    } catch (err) {
      setError('Failed to export audit report.');
    } finally {
      setExporting(false);
    }
  };

  const TABS = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security & Auth', icon: Shield },
    { id: 'data', label: 'Data Management', icon: Database },
  ];

  return (
    <div className="settings-page-container">
      <PageIntro
        eyebrow="GLOBAL WORKSPACE CONFIGURATION"
        title="System Preferences"
        subtitle="Configure institution branding, themes, security policies, and workspace parameters."
      />

      {error && <ErrorBanner message={error} />}

      {success && (
        <div
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
          <span>{success}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="settings-tabs-bar" style={{ display: 'flex', gap: '8px', marginBottom: '22px', flexWrap: 'wrap' }}>
        {TABS.map(({ id, label, icon: Icon }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              className={`settings-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 15px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid',
                borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border)',
                background: isActive ? 'var(--color-primary)' : 'var(--color-white)',
                color: isActive ? 'var(--color-white)' : 'var(--color-text-primary)',
                fontWeight: '700',
                fontSize: '12.5px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={15} aria-hidden="true" />
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSavePreferences}>
        {/* SECTION A: GENERAL SETTINGS */}
        {activeTab === 'general' && (
          <div className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>General Workspace Settings</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Workspace identity and localized formatting preferences
                </p>
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="field-group">
                <label style={{ fontSize: '12px', fontWeight: '600' }}>Workspace Name</label>
                <input
                  type="text"
                  value={prefs.workspace_name}
                  onChange={(e) => handleFieldChange('workspace_name', e.target.value)}
                  className="styled-input"
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                <div className="field-group">
                  <label style={{ fontSize: '12px', fontWeight: '600' }}>Timezone</label>
                  <select
                    value={prefs.timezone}
                    onChange={(e) => handleFieldChange('timezone', e.target.value)}
                    className="styled-input"
                  >
                    <option value="Asia/Kolkata">Asia/Kolkata (IST, UTC+5:30)</option>
                    <option value="UTC">UTC (Universal Time)</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="Europe/London">Europe/London (GMT/BST)</option>
                    <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                  </select>
                </div>

                <div className="field-group">
                  <label style={{ fontSize: '12px', fontWeight: '600' }}>Date Format</label>
                  <select
                    value={prefs.date_format}
                    onChange={(e) => handleFieldChange('date_format', e.target.value)}
                    className="styled-input"
                  >
                    <option value="DD/MM/YYYY">DD/MM/YYYY (e.g. 11/11/2026)</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD (ISO standard)</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY (US format)</option>
                  </select>
                </div>

                <div className="field-group">
                  <label style={{ fontSize: '12px', fontWeight: '600' }}>Time Format</label>
                  <select
                    value={prefs.time_format}
                    onChange={(e) => handleFieldChange('time_format', e.target.value)}
                    className="styled-input"
                  >
                    <option value="12-hour">12-hour (e.g. 02:30 PM)</option>
                    <option value="24-hour">24-hour (e.g. 14:30)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SECTION B: APPEARANCE */}
        {activeTab === 'appearance' && (
          <div className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Appearance &amp; Theme</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Select your interface theme. Changes apply immediately and persist across sessions.
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '18px' }}>
              {/* Light Mode */}
              <div
                className={`theme-card ${prefs.theme === 'light' ? 'selected' : ''}`}
                onClick={() => handleFieldChange('theme', 'light')}
                style={{
                  border: `2px solid ${prefs.theme === 'light' ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  background: '#FFFFFF',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <Sun size={20} color="#014BAA" />
                  {prefs.theme === 'light' && <CheckCircle2 size={16} color="#014BAA" />}
                </div>
                <b style={{ color: '#172033', fontSize: '14px', display: 'block' }}>Light Theme</b>
                <span style={{ color: '#667085', fontSize: '11.5px', marginTop: '4px', display: 'block' }}>
                  Signature cream and navy palette pixel-matched to TCS Ignite.
                </span>
              </div>

              {/* Dark Mode */}
              <div
                className={`theme-card ${prefs.theme === 'dark' ? 'selected' : ''}`}
                onClick={() => handleFieldChange('theme', 'dark')}
                style={{
                  border: `2px solid ${prefs.theme === 'dark' ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  background: '#0B0F17',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <Moon size={20} color="#3B82F6" />
                  {prefs.theme === 'dark' && <CheckCircle2 size={16} color="#3B82F6" />}
                </div>
                <b style={{ color: '#F1F5F9', fontSize: '14px', display: 'block' }}>Dark Theme</b>
                <span style={{ color: '#94A3B8', fontSize: '11.5px', marginTop: '4px', display: 'block' }}>
                  High-contrast dark mode optimized for reduced eye strain during long shifts.
                </span>
              </div>
            </div>
          </div>
        )}

        {/* SECTION C: NOTIFICATION PREFERENCES */}
        {activeTab === 'notifications' && (
          <div className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Notification Preferences</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Configure automated toast notifications and system alerts
                </p>
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                <div>
                  <b style={{ fontSize: '13px' }}>Announcement Broadcast Alerts</b>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Display real-time notification alerts whenever a campus broadcast is published.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.notify_announcements}
                  onChange={(e) => handleFieldChange('notify_announcements', e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                <div>
                  <b style={{ fontSize: '13px' }}>Schedule Publish Notifications</b>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Notify admins when weekly batch lecture timetables are activated.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.notify_schedules}
                  onChange={(e) => handleFieldChange('notify_schedules', e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0' }}>
                <div>
                  <b style={{ fontSize: '13px' }}>System Policy &amp; Lockdown Alerts</b>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Surface instant security alerts during exam-mode activation or policy changes.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.notify_system_alerts}
                  onChange={(e) => handleFieldChange('notify_system_alerts', e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* SECTION D: SECURITY SETTINGS */}
        {activeTab === 'security' && (
          <div className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Security &amp; Inactivity Policy</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Zero Trust session timeout and password complexity requirements
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
              <div className="field-group">
                <label style={{ fontSize: '12px', fontWeight: '600' }}>Inactivity Session Timeout</label>
                <select
                  value={prefs.session_timeout_minutes}
                  onChange={(e) => handleFieldChange('session_timeout_minutes', parseInt(e.target.value, 10))}
                  className="styled-input"
                >
                  <option value={15}>15 Minutes (Zero Trust Standard)</option>
                  <option value={30}>30 Minutes</option>
                  <option value={60}>60 Minutes</option>
                  <option value={120}>2 Hours</option>
                </select>
                <small style={{ color: 'var(--color-text-secondary)', marginTop: '4px', display: 'block' }}>
                  Automatically clears in-memory credentials when inactive.
                </small>
              </div>

              <div className="field-group">
                <label style={{ fontSize: '12px', fontWeight: '600' }}>Minimum Password Length</label>
                <select
                  value={prefs.password_min_length}
                  onChange={(e) => handleFieldChange('password_min_length', parseInt(e.target.value, 10))}
                  className="styled-input"
                >
                  <option value={8}>8 Characters (Recommended)</option>
                  <option value={10}>10 Characters</option>
                  <option value={12}>12 Characters (High Security)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* SECTION E: DATA MANAGEMENT */}
        {activeTab === 'data' && (
          <div className="panel" style={{ marginBottom: '22px' }}>
            <div className="panel-heading">
              <div>
                <h3 style={{ margin: 0, fontSize: '15px' }}>Data Management &amp; Export</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
                  Export institutional records directly from the database
                </p>
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                <div>
                  <b style={{ fontSize: '13px' }}>Export User Roster (CSV)</b>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Download complete user directory including employee IDs, cohort assignments, and active statuses.
                  </p>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleExportUsers}
                  disabled={exporting}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Download size={14} />
                  <span>{exporting ? 'Exporting...' : 'Export Users CSV'}</span>
                </button>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                <div>
                  <b style={{ fontSize: '13px' }}>Export System Audit &amp; Configuration (JSON)</b>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Export system counts, cohort hierarchies, and active configuration snapshot.
                  </p>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleExportAudit}
                  disabled={exporting}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Download size={14} />
                  <span>{exporting ? 'Exporting...' : 'Export Audit JSON'}</span>
                </button>
              </div>

              <div className="field-group" style={{ marginTop: '6px' }}>
                <label style={{ fontSize: '12px', fontWeight: '600' }}>Data Retention Period (Days)</label>
                <input
                  type="number"
                  value={prefs.data_retention_days}
                  onChange={(e) => handleFieldChange('data_retention_days', parseInt(e.target.value, 10) || 365)}
                  min={30}
                  max={1825}
                  className="styled-input"
                  style={{ maxWidth: '240px' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Global Save Button Bar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button
            type="submit"
            className="primary-button"
            disabled={saving || loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}
          >
            <Save size={16} aria-hidden="true" />
            <span>{saving ? 'Saving Preferences...' : 'Save Preferences'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}

