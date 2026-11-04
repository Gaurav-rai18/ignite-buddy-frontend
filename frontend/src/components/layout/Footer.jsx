/**
 * @file Footer.jsx
 * @description Simple presentational footer displayed at the bottom of every page.
 *
 * Shows the application brand name and the technology stack badges (React, Django, SQLite).
 * This component is purely visual — it receives no props and manages no state.
 *
 * @exports Footer
 */
import React from 'react';

/**
 * Static footer rendered inside the main content area of AppLayout.
 * @returns {JSX.Element}
 */
export function Footer() {
  return (
    <footer className="footer">
      <span>
        <b className="footer-tcs">Ignite Buddy</b> Admin console · Campus management console
      </span>
      <span>
        React <i aria-hidden="true" /> Django <i aria-hidden="true" /> SQLite
      </span>
    </footer>
  );
}
