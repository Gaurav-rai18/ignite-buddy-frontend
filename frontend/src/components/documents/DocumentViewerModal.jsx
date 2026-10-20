import React, { useEffect } from 'react';
import { FileText, ExternalLink, X, Copy, Check, Sparkles } from 'lucide-react';
import { documentsService } from '../../services/documentsService';

export function DocumentViewerModal({ isOpen, document, onClose }) {
  const [copied, setCopied] = React.useState(false);

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

  if (!isOpen || !document) return null;

  const handleOpenExternal = () => {
    const url = documentsService.getDocumentBlobUrl(document);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleCopyText = async () => {
    if (document.content) {
      await navigator.clipboard.writeText(document.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="viewer-modal-title"
      onClick={onClose}
    >
      <div
        className="modal-card"
        style={{ maxWidth: '640px', width: '92%' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="entry-icon primary" aria-hidden="true">
              <FileText size={18} />
            </span>
            <div>
              <h3 id="viewer-modal-title" style={{ margin: 0, fontSize: '15px' }}>
                {document.name}
              </h3>
              <small style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>
                {document.fileName} • {document.fileType} • {document.sizeFormatted}
              </small>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              className="primary-button"
              style={{ padding: '6px 12px', fontSize: '11.5px', height: 'auto' }}
              onClick={handleOpenExternal}
              title="Open document in a new browser window"
            >
              <ExternalLink size={13} aria-hidden="true" />
              Open file
            </button>
            <button
              type="button"
              className="modal-close"
              onClick={onClose}
              aria-label="Close document viewer"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        </div>

        <div style={{ marginTop: '14px', marginBottom: '14px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '8px',
            }}
          >
            <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--color-text-secondary)' }}>
              EXTRACTED KNOWLEDGE TEXT ({document.chunks} RAG CHUNKS)
            </span>
            {document.content && (
              <button
                type="button"
                className="text-button"
                style={{ fontSize: '11px', padding: '2px 6px' }}
                onClick={handleCopyText}
              >
                {copied ? <Check size={12} color="var(--color-success)" /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy text'}
              </button>
            )}
          </div>

          <div
            style={{
              background: 'var(--color-bg-cream)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '16px',
              maxHeight: '300px',
              overflowY: 'auto',
              fontFamily: 'monospace',
              fontSize: '11.5px',
              lineHeight: '1.6',
              color: 'var(--color-text-primary)',
              whiteSpace: 'pre-wrap',
            }}
          >
            {document.content || 'No text extracted for this document.'}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderTop: '1px solid var(--color-border-light)',
            paddingTop: '12px',
            marginTop: '8px',
            fontSize: '11px',
            color: 'var(--color-text-secondary)',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Sparkles size={13} color="var(--color-primary)" aria-hidden="true" />
            RAG Status: <b>{document.status === 'Ready' ? 'Ready for RAG' : document.status}</b>
          </span>
          <button type="button" className="secondary-button" onClick={onClose} style={{ padding: '6px 14px' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
