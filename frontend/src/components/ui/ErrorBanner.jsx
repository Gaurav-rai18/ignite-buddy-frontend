/**
 * @file ErrorBanner.jsx
 * @description Reusable error banner displayed at the top of a section.
 * Shows an error message with an optional "Retry" button.
 * @param {Object} props - { message: string, onRetry?: Function }
 */
import React from 'react';

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
