/**
 * @file BuddyControl.jsx
 * @description Buddy chatbot control page for the Ignite Buddy admin panel.
 *
 * Allows administrators to toggle the Buddy AI chatbot ON/OFF — useful for
 * disabling the bot during exam periods or maintenance windows.
 *
 * The page displays:
 *  - A hero card with Buddy's current status and a toggle button.
 *  - A details panel with additional configuration info.
 *
 * Data flow:
 *  useBuddy() hook  →  fetches Buddy state from the Django REST API
 *                   →  exposes toggleBuddy() to PATCH the status
 *
 * Key exports:
 *  - BuddyControl (React component) — rendered at the /buddy route.
 *
 * @module pages/BuddyControl
 */

import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BuddyHero } from '../../components/buddy/BuddyHero';
import { BuddyDetails } from '../../components/buddy/BuddyDetails';
import { useBuddy } from '../../hooks/useBuddy';

/**
 * BuddyControl page component.
 * Shows the current Buddy chatbot status and lets admins enable/disable it.
 *
 * @param {Object}   props
 * @param {Function} [props.onNotify] - Callback to show a toast/notification in the app shell.
 * @returns {JSX.Element}
 */
export function BuddyControl({ onNotify }) {
  // Buddy state and API actions from the custom hook
  const {
    buddy,
    isUpdating,
    error,
    toggleBuddy,
    refetch,
  } = useBuddy();

  /**
   * Toggles Buddy's active state via the API.
   * The callback receives the *new* boolean state so the notification
   * message accurately reflects whether Buddy was turned ON or OFF.
   */
  const handleToggleBuddy = () => {
    toggleBuddy((nextState) => {
      if (onNotify) {
        onNotify(`Buddy turned ${nextState ? 'ON' : 'OFF'}`);
      }
    });
  };

  return (
    <>
      <PageIntro
        eyebrow="FEATURE SETTINGS"
        title="Buddy control"
        subtitle="Manage Buddy availability for exam periods from one place."
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="buddy-layout">
        <BuddyHero
          buddy={buddy}
          isUpdating={isUpdating}
          onToggleBuddy={handleToggleBuddy}
        />
        <BuddyDetails
          buddy={buddy}
          isUpdating={isUpdating}
          onToggleBuddy={handleToggleBuddy}
        />
      </div>
    </>
  );
}
