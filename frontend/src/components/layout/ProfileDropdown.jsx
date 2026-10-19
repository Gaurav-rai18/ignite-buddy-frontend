import React, { useEffect, useRef } from 'react';
import { User, Settings, LogOut, ShieldCheck } from 'lucide-react';

export function ProfileDropdown({ isOpen, onClose, onSignOut }) {
  const dropdownRef = useRef(null);

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
          <small>admin@tcs.demo</small>
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
