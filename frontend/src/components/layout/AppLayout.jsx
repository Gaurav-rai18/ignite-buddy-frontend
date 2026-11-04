/**
 * @file AppLayout.jsx
 * @description Main application shell that wraps every authenticated page.
 *
 * Responsibilities:
 *  - Renders the persistent Sidebar, Topbar, and Footer around page content.
 *  - Derives the current page title from the URL pathname so the Topbar
 *    breadcrumb stays in sync with React Router navigation.
 *  - Manages mobile sidebar open/close state.
 *  - Provides a shared sign-out handler (calls `useAuth().logout`, shows a
 *    toast notification, and redirects to `/login`).
 *  - Uses `<Outlet />` from React Router to render nested child routes.
 *
 * Data flow:
 *  Parent (App.jsx) ➜ broadcastCount, toastMessage, onNotify
 *  AppLayout ➜ Sidebar, Topbar, Footer, Toast
 *
 * @exports AppLayout
 */
import React, { useState } from 'react';
import { useLocation, useNavigate, Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { Footer } from './Footer';
import { Toast } from '../ui/Toast';
import { useAuth } from '../../hooks/useAuth';

/**
 * Root layout wrapper rendered inside ProtectedRoute.
 * @param {Object} props
 * @param {number}  props.broadcastCount - Number of active broadcasts (shown as badge in Sidebar).
 * @param {string}  props.toastMessage   - If non-empty, a global toast is displayed at the bottom.
 * @param {Function} props.onNotify      - Callback to surface toast messages to the parent App.
 */
export function AppLayout({ broadcastCount = 0, toastMessage = '', onNotify }) {
  /** Controls the visibility of the mobile navigation drawer */
  const [mobileNav, setMobileNav] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  /**
   * Maps a URL pathname to a human-readable page title for the Topbar breadcrumb.
   * Returns 'Page Not Found' for any unrecognised route.
   */
  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
      case '/dashboard':
        return 'Dashboard';
      case '/broadcast':
        return 'Broadcast';
      case '/schedule':
        return 'Schedule';
      case '/buddy':
        return 'Buddy Control';
      case '/users':
        return 'Manage Users';
      case '/documents':
        return 'Add Documents';
      default:
        return 'Page Not Found';
    }
  };

  /** Clears auth state, notifies the parent (for a toast), and redirects to login. */
  const handleSignOut = () => {
    logout();
    if (onNotify) {
      onNotify('Signed out of Ignite Buddy Admin Console.');
    }
    navigate('/login');
  };

  const pageTitle = getPageTitle(location.pathname);

  return (
    <div className="app-shell">
      <Sidebar
        mobileNav={mobileNav}
        onCloseMobileNav={() => setMobileNav(false)}
        broadcastCount={broadcastCount}
        onSignOut={handleSignOut}
      />
      <main className="main-area">
        <Topbar
          onOpenMobileNav={() => setMobileNav(true)}
          pageTitle={pageTitle}
          onSignOut={handleSignOut}
        />
        <div className="content">
          <div className="tcs-watermark" aria-hidden="true">
            IGNITE BUDDY
          </div>
          <Outlet />
          <Footer />
        </div>
      </main>
      <Toast message={toastMessage} />
    </div>
  );
}
