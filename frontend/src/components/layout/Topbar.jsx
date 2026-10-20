import React, { useState } from 'react';
import { Menu, Bell } from 'lucide-react';
import { NotificationsDropdown } from './NotificationsDropdown';
import { ProfileDropdown } from './ProfileDropdown';

export function Topbar({ onOpenMobileNav, pageTitle, onSignOut }) {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const toggleNotifications = () => {
    setIsNotificationsOpen((prev) => !prev);
    setIsProfileOpen(false);
  };

  const toggleProfile = () => {
    setIsProfileOpen((prev) => !prev);
    setIsNotificationsOpen(false);
  };

  return (
    <header className="topbar">
      <button
        type="button"
        className="menu-toggle"
        onClick={onOpenMobileNav}
        aria-label="Open navigation menu"
      >
        <Menu size={20} aria-hidden="true" />
      </button>

      <div className="breadcrumb" aria-label="Breadcrumb">
        <span className="breadcrumb-brand">Ignite</span> Workspace <span>/</span> <b>{pageTitle}</b>
      </div>

      <div className="top-actions">
        <div className="system-pill" title="Backend connection active">
          <span aria-hidden="true" /> System ready
        </div>

        <button
          type="button"
          className={`icon-button ${isNotificationsOpen ? 'active' : ''}`}
          title="Notifications"
          aria-label="Toggle notifications panel"
          aria-expanded={isNotificationsOpen}
          onClick={toggleNotifications}
        >
          <Bell size={18} aria-hidden="true" />
          <span className="notification-badge" aria-hidden="true" />
        </button>

        <button
          type="button"
          className={`top-avatar-button ${isProfileOpen ? 'active' : ''}`}
          title="Administrator profile"
          aria-label="Toggle user profile menu"
          aria-expanded={isProfileOpen}
          onClick={toggleProfile}
        >
          <div className="top-avatar" aria-hidden="true">
            AD
          </div>
        </button>

        <NotificationsDropdown
          isOpen={isNotificationsOpen}
          onClose={() => setIsNotificationsOpen(false)}
        />

        <ProfileDropdown
          isOpen={isProfileOpen}
          onClose={() => setIsProfileOpen(false)}
          onSignOut={onSignOut}
        />
      </div>
    </header>
  );
}
