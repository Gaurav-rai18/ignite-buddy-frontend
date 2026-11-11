import React, { useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export function DeleteDocumentDialog({ isOpen, onClose, onConfirm, document: doc }) {
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

  if (!isOpen || !doc) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-doc-title"
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
            <h3 id="delete-doc-title">Delete document?</h3>
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
          Are you sure you want to remove <b>{doc.fileName || doc.name}</b> from the knowledge base? This document will no longer be available for Buddy RAG retrieval.
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="primary-button danger-button"
            onClick={() => {
              onConfirm(doc.id);
              onClose();
            }}
          >
            Delete document
          </button>
        </div>
      </div>
    </div>
  );
}
