import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BroadcastForm } from '../../components/broadcast/BroadcastForm';
import { BroadcastList } from '../../components/broadcast/BroadcastList';
import { useBroadcasts } from '../../hooks/useBroadcasts';

export function Broadcast({ onNotify, onUpdateBroadcastCount }) {
  const {
    broadcasts,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    submitBroadcast,
    refetch,
  } = useBroadcasts();

  const handleSubmit = () => {
    submitBroadcast((msg) => {
      if (onNotify) {
        onNotify(msg);
      }
      if (onUpdateBroadcastCount) {
        onUpdateBroadcastCount(broadcasts.length + 1);
      }
    });
  };

  const handleFocusForm = () => {
    document.getElementById('broadcast-title')?.focus();
  };

  return (
    <>
      <PageIntro
        eyebrow="COMMUNICATION"
        title="Broadcast centre"
        subtitle="Create an announcement for students and keep everyone informed."
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="two-column">
        <BroadcastForm
          form={form}
          formErrors={formErrors}
          isSubmitting={isSubmitting}
          onChangeField={updateFormField}
          onSubmit={handleSubmit}
        />
        <BroadcastList
          broadcasts={broadcasts}
          loading={loading}
          onCreateClick={handleFocusForm}
        />
      </div>
    </>
  );
}
