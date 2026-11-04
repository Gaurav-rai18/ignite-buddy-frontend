/**
 * @file BroadcastPreviewModal.jsx
 * @description Read-only preview modal that shows the admin what a broadcast announcement
 *              will look like before it is saved/sent. Displays recipient targeting summary,
 *              the title, and the full message body. The modal can be dismissed via the
 *              close button, the overlay backdrop, or the Escape key.
 *
 * Data flow: Receives the current broadcast `form` state object from the parent Broadcast
 *            page — no API calls are made inside this component.
 */
import React, { useEffect } from 'react';
import { X, Users, Megaphone } from 'lucide-react';

/**
 * Modal that previews a broadcast announcement before submission.
 *
 * @param {Object}   props
 * @param {boolean}  props.isOpen  - Controls visibility of the modal.
 * @param {Function} props.onClose - Callback to close/dismiss the modal.
 * @param {Object}   props.form    - The broadcast form state with title, message, recipientMode, selectedUsers, and role.
 */
export function BroadcastPreviewModal({ isOpen, onClose, form }) {
  // Close the modal when the user presses Escape; listener is added only while open
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

  if (!isOpen) return null;

  // Build a human-readable summary of who will receive this broadcast,
  // depending on the chosen targeting mode (All users / By role / Specific users).
  const mode = form.recipientMode || 'All users';
  const selectedUsers = Array.isArray(form.selectedUsers) ? form.selectedUsers : [];
  const recipientSummary =
    mode === 'By role'
      ? form.role || 'Select a role'
      : mode === 'Specific users'
        ? `${selectedUsers.length} selected user${selectedUsers.length === 1 ? '' : 's'}`
        : 'All users';

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="preview-title"
      onClick={onClose}
    >
      {/* Stop propagation so clicking inside the card doesn't trigger the overlay's onClose */}
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="entry-icon" aria-hidden="true">
              <Megaphone size={16} />
            </span>
            <h3 id="preview-title">Announcement Preview</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close preview modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div style={{ display: 'grid', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="count-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
              <Users size={12} aria-hidden="true" />
              {recipientSummary}
            </span>
            <small style={{ color: 'var(--color-text-secondary)', fontSize: '10px' }}>
              Preview as student
            </small>
          </div>

          {mode === 'Specific users' && selectedUsers.length > 0 && (
            <div className="recipient-chips">
              {selectedUsers.map((user) => (
                <span className="recipient-chip static" key={user.id}>
                  {user.username}
                </span>
              ))}
            </div>
          )}

          <h4 style={{ margin: '0', fontSize: '15px', fontWeight: '800', color: 'var(--color-text-primary)' }}>
            {form.title.trim() || 'Untitled Announcement'}
          </h4>

          <div
            style={{
              fontSize: '12px',
              lineHeight: '1.7',
              color: 'var(--color-text-primary)',
              background: 'var(--color-bg-cream)',
              padding: '14px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              whiteSpace: 'pre-wrap',
            }}
          >
            {form.message.trim() || 'No announcement message entered yet.'}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px' }}>
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
            >
              Close Preview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
