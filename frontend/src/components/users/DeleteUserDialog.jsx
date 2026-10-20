import React, { useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export function DeleteUserDialog({ isOpen, onClose, onConfirm, user }) {
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

  if (!isOpen || !user) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-user-title"
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
            <h3 id="delete-user-title">Delete this user?</h3>
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

        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: '1.6', margin: '0 0 16px' }}>
          Are you sure you want to remove <b>{user.name}</b> (<code>{user.email}</code>)? This action cannot be undone.
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="primary-button danger-button"
            onClick={() => {
              onConfirm(user.id);
              onClose();
            }}
          >
            Delete user
          </button>
        </div>
      </div>
    </div>
  );
}
