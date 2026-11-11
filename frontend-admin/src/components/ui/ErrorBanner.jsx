import React from 'react';

export function ErrorBanner({ message, onRetry }) {
  if (
    !message ||
    typeof message !== 'string' ||
    !message.trim() ||
    message.trim().toLowerCase() === 'canceled' ||
    message.trim().toLowerCase() === 'cancelled'
  ) {
    return null;
  }

  return (
    <div className="error-banner" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={() => onRetry()}>
          Retry
        </button>
      )}
    </div>
  );
}
