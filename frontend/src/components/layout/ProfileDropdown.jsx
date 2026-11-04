/**
 * @file ProfileDropdown.jsx
 * @description Dropdown menu attached to the admin avatar in the Topbar / Sidebar.
 *
 * Provides quick-access links to profile, permissions, and preferences, plus a
 * sign-out action.  Currently all non-sign-out items close the menu without
 * navigating (placeholder actions).
 *
 * Accessibility:
 *  - Uses `role="menu"` / `role="menuitem"` for screen readers.
 *  - Closes on outside click or Escape key.
 *
 * @exports ProfileDropdown
 */
import React, { useEffect, useRef } from 'react';
import { User, Settings, LogOut, ShieldCheck } from 'lucide-react';

/**
 * User profile flyout menu.
 * @param {Object}   props
 * @param {boolean}  props.isOpen    - Whether the menu is visible.
 * @param {Function} props.onClose   - Called to close the menu.
 * @param {Function} props.onSignOut - Called when the user clicks "Sign out".
 */
export function ProfileDropdown({ isOpen, onClose, onSignOut }) {
  const dropdownRef = useRef(null);

  /* ── Close-on-outside-click & Escape key handler ─────────────────────── */
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

  return (
    <div
      ref={dropdownRef}
      className="dropdown-menu profile-dropdown"
      role="menu"
      aria-label="User profile menu"
    >
      <div className="profile-dropdown-header">
        <div className="avatar" aria-hidden="true">AD</div>
        <div>
          <b>Administrator</b>
          <small>admin@campus.demo</small>
        </div>
      </div>

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => {
          onClose();
        }}
      >
        <User size={15} aria-hidden="true" />
        <span>Admin Profile</span>
      </button>

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => {
          onClose();
        }}
      >
        <ShieldCheck size={15} aria-hidden="true" />
        <span>Workspace Owner Permissions</span>
      </button>

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => {
          onClose();
        }}
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
        <span>Sign out</span>
      </button>
    </div>
  );
}
