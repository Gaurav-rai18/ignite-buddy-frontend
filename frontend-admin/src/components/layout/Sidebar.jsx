import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Megaphone,
  CalendarClock,
  Bot,
  Users,
  FileText,
  X,
  MoreVertical,
} from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';
import { getUserDisplayName, getUserInitials, getUserRoleLabel } from '../../utils/user';

const NAV_ITEMS = [
  { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard, label: 'Overview' },
  { path: '/broadcast', name: 'Broadcast', icon: Megaphone, label: 'Announcements' },
  { path: '/schedule', name: 'Schedule', icon: CalendarClock, label: 'Timetable & timing' },
  { path: '/buddy', name: 'Buddy Control', icon: Bot, label: 'Exam-time control' },
  { path: '/users', name: 'Manage Users', icon: Users, label: 'Add, edit & roles' },
  { path: '/documents', name: 'Add Documents', icon: FileText, label: 'Documents & sharing' },
];

export function Sidebar({ mobileNav, onCloseMobileNav, broadcastCount = 0, onSignOut, user }) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && mobileNav) {
        onCloseMobileNav();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileNav, onCloseMobileNav]);

  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const roleLabel = getUserRoleLabel(user?.role, user?.is_superuser);

  return (
    <>
      {mobileNav && (
        <button
          type="button"
          className="mobile-scrim"
          onClick={onCloseMobileNav}
          aria-label="Close navigation overlay"
        />
      )}
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`} aria-label="Sidebar navigation">
        <div className="brand">
          <div className="tcs-logo" aria-hidden="true">
            IB
          </div>
          <div className="brand-copy">
            <strong>
              Ignite <span>Buddy</span>
            </strong>
            <small>ADMIN CONSOLE</small>
          </div>
          <button
            type="button"
            className="close-nav"
            onClick={onCloseMobileNav}
            aria-label="Close navigation menu"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div className="workspace">
          <div className="workspace-icon" aria-hidden="true">
            I
          </div>
          <div>
            <b>Ignite workspace</b>
            <small>Administrator account</small>
          </div>
          <span className="workspace-dot" aria-label="Workspace active" />
        </div>

        <div className="nav-caption">WORKSPACE</div>

        <nav aria-label="Main menu">
          {NAV_ITEMS.map(({ path, name, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onCloseMobileNav}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">
                <Icon size={18} aria-hidden="true" />
              </span>
              <span className="nav-copy">
                <b>{name}</b>
                <small>{label}</small>
              </span>
              {name === 'Broadcast' && broadcastCount > 0 && (
                <span className="nav-count" aria-label={`${broadcastCount} announcements`}>
                  {broadcastCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              className={`profile-button ${isProfileOpen ? 'active' : ''}`}
              onClick={() => setIsProfileOpen((prev) => !prev)}
              aria-expanded={isProfileOpen}
              aria-label="Toggle user profile options"
            >
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
              <div className="profile-copy">
                <b>{displayName}</b>
                <small>{roleLabel}</small>
              </div>
              <MoreVertical size={16} className="profile-more" aria-hidden="true" />
            </button>

            <ProfileDropdown
              isOpen={isProfileOpen}
              onClose={() => setIsProfileOpen(false)}
              onSignOut={onSignOut}
              user={user}
            />
          </div>
        </div>
      </aside>
    </>
  );
}
