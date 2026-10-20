import React, { useEffect } from 'react';
import { FileText, X, CheckCircle2, Clock, AlertTriangle, Layers, Database, Hash } from 'lucide-react';

export function DocumentDetailsModal({ isOpen, onClose, document: doc }) {
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

  const isReady = doc.status === 'Ready' || doc.status === 'Ready for RAG';
  const isProcessing = doc.status === 'Processing';

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="doc-details-title"
      onClick={onClose}
    >
      <div className="modal-card" style={{ maxWidth: '500px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="entry-icon" aria-hidden="true">
              <FileText size={16} />
            </span>
            <h3 id="doc-details-title">Document & RAG Details</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close details modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div style={{ display: 'grid', gap: '14px' }}>
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)', fontWeight: '700' }}>
              DOCUMENT TITLE
            </span>
            <h4 style={{ margin: '4px 0 2px', fontSize: '15px', color: 'var(--color-text-primary)' }}>
              {doc.name}
            </h4>
            <p style={{ margin: 0, fontSize: '11px', color: 'var(--color-text-secondary)' }}>
              {doc.description || 'No description provided'}
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '10px',
              background: 'var(--color-bg-cream)',
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div>
              <small style={{ fontSize: '9.5px', color: 'var(--color-text-secondary)', display: 'block' }}>
                FILE NAME
              </small>
              <b style={{ fontSize: '11px', color: 'var(--color-text-primary)' }}>{doc.fileName}</b>
            </div>
            <div>
              <small style={{ fontSize: '9.5px', color: 'var(--color-text-secondary)', display: 'block' }}>
                FILE FORMAT / SIZE
              </small>
              <b style={{ fontSize: '11px', color: 'var(--color-text-primary)' }}>
                {doc.fileType} • {doc.sizeFormatted}
              </b>
            </div>
            <div>
              <small style={{ fontSize: '9.5px', color: 'var(--color-text-secondary)', display: 'block' }}>
                UPLOADED
              </small>
              <b style={{ fontSize: '11px', color: 'var(--color-text-primary)' }}>{doc.uploadedAt}</b>
            </div>
            <div>
              <small style={{ fontSize: '9.5px', color: 'var(--color-text-secondary)', display: 'block' }}>
                TARGET AUDIENCE
              </small>
              <b style={{ fontSize: '11px', color: 'var(--color-text-primary)' }}>{doc.audience || 'All students'}</b>
            </div>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)', fontWeight: '700' }}>
              RAG LIFECYCLE & INDEXING
            </span>
            <div
              style={{
                marginTop: '6px',
                display: 'grid',
                gap: '8px',
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'var(--color-white)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                  <CheckCircle2 size={14} color={isReady ? 'var(--color-success)' : 'var(--color-text-secondary)'} />
                  <b>Status:</b>
                </span>
                <span className={`status-pill ${isReady ? 'active' : isProcessing ? 'inactive' : 'inactive'}`}>
                  <i aria-hidden="true" />
                  {isReady ? 'Ready for RAG' : isProcessing ? 'Processing text...' : 'Failed'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                  <Layers size={14} color="var(--color-primary)" />
                  <b>Extracted Chunks:</b>
                </span>
                <b style={{ fontSize: '11.5px', color: 'var(--color-primary)' }}>
                  {doc.chunks || 0} chunks
                </b>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                  <Database size={14} color="var(--color-primary)" />
                  <b>Vector Store:</b>
                </span>
                <span style={{ fontSize: '10.5px', color: 'var(--color-text-secondary)' }}>
                  {doc.vectorStore || 'SQLite local knowledge base'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                  <Hash size={14} color="var(--color-text-secondary)" />
                  <b>Knowledge ID:</b>
                </span>
                <code style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>{doc.id}</code>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '6px' }}>
            <button type="button" className="secondary-button" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
