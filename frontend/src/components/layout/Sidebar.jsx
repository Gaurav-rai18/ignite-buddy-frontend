import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Megaphone, CalendarClock, Bot, X, MoreVertical } from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';

const NAV_ITEMS = [
  { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard, label: 'Overview' },
  { path: '/broadcast', name: 'Broadcast', icon: Megaphone, label: 'Announcements' },
  { path: '/schedule', name: 'Schedule', icon: CalendarClock, label: 'OneDrive & timing' },
  { path: '/buddy', name: 'Buddy Control', icon: Bot, label: 'Exam-time control' },
];

export function Sidebar({ mobileNav, onCloseMobileNav, broadcastCount = 0, onSignOut }) {
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

  return (
    <>
      {mobileNav && (
        <button
          type="button"
          className="mobile-scrim"
          onClick={onCloseMobileNav}
          aria-label="Close navigation menu"
        />
      )}
      <aside
        className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}
        aria-label="Main sidebar navigation"
      >
        <div className="brand">
          <div className="tcs-logo" aria-label="TCS project demo">
            TCS
          </div>
          <div className="brand-copy">
            <strong>
              TCS<span> Admin</span>
            </strong>
            <small>PROJECT DEMO CONSOLE</small>
          </div>
          <button
            type="button"
            className="close-nav"
            onClick={onCloseMobileNav}
            aria-label="Close menu"
          >
            <X size={19} aria-hidden="true" />
          </button>
        </div>

        <div className="workspace">
          <div className="workspace-icon tcs-workspace-mark" aria-hidden="true">
            T
          </div>
          <div>
            <b>TCS workspace</b>
            <small>Administrator account</small>
          </div>
          <span className="workspace-dot" aria-hidden="true" />
        </div>

        <div className="nav-caption">WORKSPACE</div>

        <nav>
          {NAV_ITEMS.map(({ path, name, icon: Icon, label }) => (
            <NavLink
              key={name}
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
          <div className="system-status-widget">
            <div className="system-status-info">
              <b>Connected: SQLite</b>
              <small>Django REST API active</small>
            </div>
            <span className="status-indicator-dot" title="Database connected" aria-hidden="true" />
          </div>

          <div style={{ position: 'relative' }}>
            <button
              type="button"
              className={`profile-button ${isProfileOpen ? 'active' : ''}`}
              onClick={() => setIsProfileOpen((prev) => !prev)}
              aria-expanded={isProfileOpen}
              aria-label="Toggle admin profile options"
            >
              <div className="avatar" aria-hidden="true">
                AD
              </div>
              <div className="profile-copy">
                <b>Admin</b>
                <small>Workspace owner</small>
              </div>
              <MoreVertical size={16} className="profile-more" aria-hidden="true" />
            </button>

            <ProfileDropdown
              isOpen={isProfileOpen}
              onClose={() => setIsProfileOpen(false)}
              onSignOut={onSignOut}
            />
          </div>
        </div>
      </aside>
    </>
  );
}
