import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BuddyHero } from '../../components/buddy/BuddyHero';
import { BuddyDetails } from '../../components/buddy/BuddyDetails';
import { useBuddy } from '../../hooks/useBuddy';

export function BuddyControl({ onNotify }) {
  const {
    buddy,
    settings,
    isUpdating,
    error,
    toggleBuddy,
    updateSetting,
    saveBatchSettings,
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
        eyebrow="CAMPUS ASSISTANT GOVERNANCE"
        title="Buddy Control Center"
        subtitle="Configure master availability, assessment lockdowns, AI model parameters, voice & vision modalities, and campus safety guardrails."
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="buddy-layout">
        <BuddyHero
          buddy={buddy}
          isUpdating={isUpdating}
          onToggleBuddy={handleToggleBuddy}
        />
        <BuddyDetails
          settings={settings}
          isUpdating={isUpdating}
          onToggleBuddy={handleToggleBuddy}
          onUpdateSetting={updateSetting}
          onSaveBatch={saveBatchSettings}
          onNotify={onNotify}
        />
      </div>
    </>
  );
}
