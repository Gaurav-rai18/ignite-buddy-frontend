import React, { useEffect } from 'react';
import { X, Users, Megaphone } from 'lucide-react';

export function BroadcastPreviewModal({ isOpen, onClose, form }) {
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

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="preview-title"
      onClick={onClose}
    >
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
              {form.audience || 'All students'}
            </span>
            <small style={{ color: 'var(--color-text-secondary)', fontSize: '10px' }}>
              Preview as student
            </small>
          </div>

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
