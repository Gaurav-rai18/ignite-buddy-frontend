import React, { useState } from 'react';
import { useLocation, Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { Footer } from './Footer';
import { Toast } from '../ui/Toast';

export function AppLayout({ broadcastCount = 0, toastMessage = '', onNotify }) {
  const [mobileNav, setMobileNav] = useState(false);
  const location = useLocation();

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
      default:
        return 'Page Not Found';
    }
  };

  const handleSignOut = () => {
    if (onNotify) {
      onNotify('Session reset: Logged out of demo administrator mode.');
    }
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
            TCS
          </div>
          <Outlet />
          <Footer />
        </div>
      </main>
      <Toast message={toastMessage} />
    </div>
  );
}
