import React, { useState } from 'react';
import { useLocation, useNavigate, Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { Footer } from './Footer';
import { Toast } from '../ui/Toast';
import { useAuth } from '../../hooks/useAuth';

export function AppLayout({ broadcastCount = 0, toastMessage = '', onNotify }) {
  const [mobileNav, setMobileNav] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

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
