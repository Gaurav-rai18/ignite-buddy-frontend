import React, { useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export function DeleteScheduleDialog({ isOpen, onClose, onConfirm, schedule, isDeleting = false }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !schedule) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-schedule-title"
      onClick={onClose}
    >
      <div className="modal-card" style={{ maxWidth: '420px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '30px',
                height: '30px',
                borderRadius: '6px',
                background: 'var(--color-danger-bg)',
                color: 'var(--color-danger)',
                display: 'grid',
                placeItems: 'center',
              }}
              aria-hidden="true"
            >
              <AlertTriangle size={16} />
            </span>
            <h3 id="delete-schedule-title">Delete schedule?</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close delete dialog"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <p style={{ fontSize: '11.5px', color: 'var(--color-text-secondary)', lineHeight: '1.5', margin: '14px 0 20px' }}>
          Are you sure you want to delete the scheduled item <strong>"{schedule.title}"</strong>? This will remove it from the publication queue.
        </p>

        <div className="modal-actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            type="button"
            className="secondary-button"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="danger-button"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Schedule'}
          </button>
        </div>
      </div>
    </div>
  );
}

