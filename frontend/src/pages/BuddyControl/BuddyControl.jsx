import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BuddyHero } from '../../components/buddy/BuddyHero';
import { BuddyDetails } from '../../components/buddy/BuddyDetails';
import { useBuddy } from '../../hooks/useBuddy';

export function BuddyControl({ onNotify }) {
  const {
    buddy,
    isUpdating,
    error,
    toggleBuddy,
    refetch,
  } = useBuddy();

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
