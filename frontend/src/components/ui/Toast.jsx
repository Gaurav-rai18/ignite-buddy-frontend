/**
 * @file Toast.jsx
 * @description Floating toast notification component. Shows a brief success message
 * that auto-dismisses after the timeout set in App.jsx (2.8s).
 */
import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export function Toast({ message }) {
  if (!message) return null;

  return (
    <div className="toast" role="status" aria-live="polite">
      <CheckCircle2 size={18} aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}
