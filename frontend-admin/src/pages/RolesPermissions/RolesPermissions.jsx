import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Users,
  CheckCircle2,
  Lock,
  Save,
  RotateCcw,
  Sparkles,
  Info,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { settingsService } from '../../services/settingsService';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

const MODULES = [
  { key: 'dashboard', name: 'Dashboard Overview', desc: 'Real-time metrics, active trainee counts, and campus summary' },
  { key: 'broadcast', name: 'Broadcast & Announcements', desc: 'Publish notifications to cohorts, batches, and individual users' },
  { key: 'schedule', name: 'Schedule & Timetables', desc: 'Publish weekly batch timetables and room assignments' },
  { key: 'buddy', name: 'Buddy Control Center', desc: 'Master AI assistant toggle, exam lockdowns, and guardrail policies' },
  { key: 'users', name: 'Manage Users & Trainees', desc: 'Directory management, role assignment, and bulk CSV enrollment' },
  { key: 'documents', name: 'Add Documents (Knowledge Base)', desc: 'Upload syllabus PDFs and trigger RAG vector indexing' },
  { key: 'assignments', name: 'Assignments & Coursework', desc: 'Publish, track, and grade student assignments and submissions' },
  { key: 'hierarchy', name: 'Batch & Cohort Hierarchy', desc: 'Manage Cohorts, Major Batches, Sub-batches, and Lab venues' },
  { key: 'roles_permissions', name: 'Roles & Permissions', desc: 'Configure module access control and security permissions' },
  { key: 'system_preferences', name: 'System Preferences', desc: 'Configure workspace identity, academic dates, and global preferences' },
];

export function RolesPermissions({ onNotify }) {
  const { user } = useAuth();

  const [rolesData, setRolesData] = useState({});
  const [userCounts, setUserCounts] = useState({});
  const [selectedRole, setSelectedRole] = useState('ADMIN');
  const [canManage, setCanManage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const isSuperUserOrAdmin = Boolean(user?.is_superuser || (user?.role && user.role.toUpperCase() === 'ADMIN'));

  const fetchMatrix = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await settingsService.getRolesPermissions();
      if (data && data.roles) {
        setRolesData(data.roles);
        setUserCounts(data.user_counts || {});
        setCanManage(Boolean(data.can_manage));
        if (!data.roles[selectedRole]) {
          setSelectedRole(Object.keys(data.roles)[0]);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load roles and permissions matrix.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatrix();
  }, []);

  const handleTogglePermission = (moduleKey) => {
    if (!canManage) return;
    if (rolesData[selectedRole]?.is_immutable) return;

    setRolesData((prev) => {
      const roleObj = prev[selectedRole];
      if (!roleObj) return prev;
      const currentVal = Boolean(roleObj.permissions?.[moduleKey]);
      return {
        ...prev,
        [selectedRole]: {
          ...roleObj,
          permissions: {
            ...roleObj.permissions,
            [moduleKey]: !currentVal,
          },
        },
      };
    });
  };

  const handleSave = async () => {
    if (!canManage) return;
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const res = await settingsService.updateRolesPermissions(rolesData);
      if (res && res.roles) {
        setRolesData(res.roles);
      }
      setSuccess('Role permissions saved and enforced across backend and frontend.');
      if (onNotify) {
        onNotify('Roles & Permissions matrix successfully updated.');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to save permissions.');
    } finally {
      setSaving(false);
    }
  };

  const activeRoleConfig = rolesData[selectedRole] || {
    label: selectedRole,
    description: '',
    is_immutable: false,
    permissions: {},
  };

  return (
    <div className="roles-page-container">
      <PageIntro
        eyebrow="ACCESS CONTROL & GOVERNANCE"
        title="Roles &amp; Permissions"
        subtitle="Manage module-level privileges, administrative authority, and governance across TCS Ignite user roles."
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

      {!isSuperUserOrAdmin && (
        <div
          style={{
            background: 'var(--color-warning-bg)',
            border: '1px solid var(--color-warning)',
            color: 'var(--color-warning)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '20px',
            fontSize: '13px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <ShieldAlert size={18} />
          <span>
            You have view-only access to this configuration. Only Ignite Administrators and Workspace Owners can modify permission policies.
          </span>
        </div>
      )}

      {/* Role Selector Tabs */}
      <div className="role-selector-bar" style={{ display: 'flex', gap: '10px', marginBottom: '22px', flexWrap: 'wrap' }}>
        {Object.entries(rolesData).map(([roleKey, roleObj]) => {
          const isActive = selectedRole === roleKey;
          const count = userCounts[roleKey] || 0;
          return (
            <button
              key={roleKey}
              type="button"
              className={`role-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setSelectedRole(roleKey)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
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
              <span>{roleObj.label || roleKey}</span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'var(--color-bg-cream)',
                  color: isActive ? 'var(--color-white)' : 'var(--color-text-secondary)',
                }}
              >
                {count} {count === 1 ? 'user' : 'users'}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Permissions Card */}
      <div className="panel" style={{ marginBottom: '22px' }}>
        <div className="panel-heading" style={{ alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>{activeRoleConfig.label} Privileges</h3>
              {activeRoleConfig.is_immutable && (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '10px',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: selectedRole === 'ADMIN' ? 'var(--color-primary-light)' : 'var(--color-bg-cream)',
                    color: selectedRole === 'ADMIN' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  }}
                >
                  <Lock size={11} />
                  {selectedRole === 'ADMIN' ? 'Irrevocable Workspace Owner' : 'Enforced Non-Admin Policy'}
                </span>
              )}
            </div>
            <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
              {activeRoleConfig.description}
            </p>
          </div>

          {canManage && !activeRoleConfig.is_immutable && (
            <button
              type="button"
              className="primary-button"
              onClick={handleSave}
              disabled={saving}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Save size={15} aria-hidden="true" />
              <span>{saving ? 'Saving...' : 'Save Permissions'}</span>
            </button>
          )}
        </div>

        {/* Modules Permission Table */}
        <div style={{ marginTop: '20px', borderTop: '1px solid var(--color-border-light)' }}>
          {MODULES.map(({ key, name, desc }) => {
            const isEnabled = Boolean(activeRoleConfig.permissions?.[key]);
            const isLocked = activeRoleConfig.is_immutable || !canManage;

            return (
              <div
                key={key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 0',
                  borderBottom: '1px solid var(--color-border-light)',
                  opacity: isLocked && !isEnabled ? 0.75 : 1,
                }}
              >
                <div style={{ paddingRight: '20px' }}>
                  <b style={{ fontSize: '13.5px', color: 'var(--color-text-primary)' }}>{name}</b>
                  <p style={{ margin: '3px 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>{desc}</p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      color: isEnabled ? 'var(--color-success)' : 'var(--color-text-secondary)',
                      textTransform: 'uppercase',
                    }}
                  >
                    {isEnabled ? 'Permitted' : 'Restricted'}
                  </span>
                  <label
                    style={{
                      position: 'relative',
                      display: 'inline-block',
                      width: '42px',
                      height: '24px',
                      cursor: isLocked ? 'not-allowed' : 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      onChange={() => handleTogglePermission(key)}
                      disabled={isLocked}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: isEnabled ? 'var(--color-primary)' : 'var(--color-border)',
                        borderRadius: '24px',
                        transition: 'background-color 0.2s',
                        cursor: isLocked ? 'not-allowed' : 'pointer',
                      }}
                    >
                      <span
                        style={{
                          position: 'absolute',
                          height: '18px',
                          width: '18px',
                          left: isEnabled ? '21px' : '3px',
                          bottom: '3px',
                          backgroundColor: 'var(--color-white)',
                          borderRadius: '50%',
                          transition: 'left 0.2s',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                        }}
                      />
                    </span>
                  </label>
                </div>
              </div>
            );
          })}
        </div>

        {canManage && !activeRoleConfig.is_immutable && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
            <button
              type="button"
              className="primary-button"
              onClick={handleSave}
              disabled={saving}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Save size={15} aria-hidden="true" />
              <span>{saving ? 'Saving...' : 'Save Permissions'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div
        className="panel"
        style={{
          background: 'var(--color-bg-cream)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
        }}
      >
        <Info size={20} style={{ color: 'var(--color-primary)', flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
          <b>Security Architecture Note:</b> Workspace Owner access cannot be downgraded to prevent administrative lockout.
          Module permissions configured here are validated across both frontend routes and Django REST backend permission classes.
        </div>
      </div>
    </div>
  );
}

