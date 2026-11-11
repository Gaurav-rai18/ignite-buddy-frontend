import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Settings, LogOut, ShieldCheck } from 'lucide-react';
import { getUserDisplayName, getUserInitials, getUserRoleLabel } from '../../utils/user';

export function ProfileDropdown({ isOpen, onClose, onSignOut, user }) {
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        onClose();
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const roleLabel = getUserRoleLabel(user?.role, user?.is_superuser);
  const canManageRoles = Boolean(user?.is_superuser || (user?.role && user.role.toUpperCase() === 'ADMIN'));

  const handleNavigate = (path) => {
    onClose();
    navigate(path);
  };

  return (
    <div
      ref={dropdownRef}
      className="dropdown-menu profile-dropdown"
      role="menu"
      aria-label="User profile menu"
    >
      <div className="profile-dropdown-header">
        <div className="avatar" aria-hidden="true">
          {user?.profile_picture ? (
            <img
              src={user.profile_picture}
              alt={displayName}
              style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
            />
          ) : (
            initials
          )}
        </div>
        <div style={{ minWidth: 0, overflow: 'hidden' }}>
          <b style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {displayName}
          </b>
          <small style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {user?.email || ''}
          </small>
          <span
            className="user-role-badge"
            style={{
              display: 'inline-block',
              marginTop: '4px',
              fontSize: '9.5px',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'var(--color-primary-light)',
              color: 'var(--color-primary)',
            }}
          >
            {roleLabel}
          </span>
        </div>
      </div>

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => handleNavigate('/profile')}
      >
        <User size={15} aria-hidden="true" />
        <span>My Profile</span>
      </button>

      {canManageRoles && (
        <button
          type="button"
          className="profile-menu-item"
          role="menuitem"
          onClick={() => handleNavigate('/roles-permissions')}
        >
          <ShieldCheck size={15} aria-hidden="true" />
          <span>Roles &amp; Permissions</span>
        </button>
      )}

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => handleNavigate('/settings')}
      >
        <Settings size={15} aria-hidden="true" />
        <span>System Preferences</span>
      </button>

      <div className="profile-divider" />

      <button
        type="button"
        className="profile-menu-item danger"
        role="menuitem"
        onClick={() => {
          onClose();
          if (onSignOut) onSignOut();
        }}
      >
        <LogOut size={15} aria-hidden="true" />
        <span>Sign Out</span>
      </button>
    </div>
  );
}
