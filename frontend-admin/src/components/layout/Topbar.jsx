import React, { useState } from 'react';
import { Menu } from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';
import { getUserDisplayName, getUserInitials } from '../../utils/user';

export function Topbar({ onOpenMobileNav, pageTitle, onSignOut, user }) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const toggleProfile = () => {
    setIsProfileOpen((prev) => !prev);
  };

  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);

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
        <button
          type="button"
          className={`top-avatar-button ${isProfileOpen ? 'active' : ''}`}
          title={`${displayName} – Account menu`}
          aria-label="Toggle user profile menu"
          aria-expanded={isProfileOpen}
          onClick={toggleProfile}
        >
          <div className="top-avatar" aria-hidden="true">
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
        </button>

        <ProfileDropdown
          isOpen={isProfileOpen}
          onClose={() => setIsProfileOpen(false)}
          onSignOut={onSignOut}
          user={user}
        />
      </div>
    </header>
  );
}
