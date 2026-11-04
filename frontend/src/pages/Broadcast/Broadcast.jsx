/**
 * @file Broadcast.jsx
 * @description Broadcast management page for the Ignite Buddy admin panel.
 *
 * Provides a two-column layout:
 *  - Left column: a form for composing and sending new broadcast announcements.
 *  - Right column: a list of previously sent broadcasts.
 *
 * Data flow:
 *  useBroadcasts() hook  →  fetches existing broadcasts from the Django REST API
 *                        →  manages form state (title, body, recipients)
 *                        →  handles validation errors and submission
 *
 * Key exports:
 *  - Broadcast (React component) — rendered at the /broadcast route.
 *
 * @module pages/Broadcast
 */

import React from 'react';
import { PageIntro } from '../../components/ui/PageIntro';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { BroadcastForm } from '../../components/broadcast/BroadcastForm';
import { BroadcastList } from '../../components/broadcast/BroadcastList';
import { useBroadcasts } from '../../hooks/useBroadcasts';

/**
 * Broadcast page component.
 * Lets admins compose a new announcement and view a history of past broadcasts.
 *
 * @param {Object}   props
 * @param {Function} [props.onNotify]             - Callback to show a toast/notification in the app shell.
 * @param {Function} [props.onUpdateBroadcastCount] - Callback to update the broadcast count in the sidebar badge.
 * @returns {JSX.Element}
 */
export function Broadcast({ onNotify, onUpdateBroadcastCount }) {
  // Destructure all broadcast-related state and actions from the custom hook.
  const {
    broadcasts,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    toggleRecipient,
    setRecipients,
    submitBroadcast,
    refetch,
  } = useBroadcasts();

  /**
   * Submits the broadcast form. On success, notifies the user via toast
   * and updates the sidebar broadcast count to keep the badge in sync.
   */
  const handleSubmit = () => {
    submitBroadcast((msg) => {
      if (onNotify) {
        onNotify(msg);
      }
      // Optimistically increment the count so the sidebar badge reflects the new broadcast
      if (onUpdateBroadcastCount) {
        onUpdateBroadcastCount(broadcasts.length + 1);
      }
    });
  };

  /** Scrolls focus to the broadcast title input so users can start typing immediately. */
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
          onToggleRecipient={toggleRecipient}
          onSetRecipients={setRecipients}
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
