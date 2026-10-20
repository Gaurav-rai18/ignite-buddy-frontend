import React from 'react';
import { FileText, Users, Clock, Trash2, Eye, FileSearch } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';

export function DocumentList({
  documents = [],
  loading = false,
  onViewDetails,
  onViewDocument,
  onDelete,
  onOpenUpload,
}) {
  if (loading && documents.length === 0) {
    return (
      <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '11.5px' }}>
        Loading documents...
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No documents yet"
        text="Upload a PDF or text file to start building your knowledge base."
        action="Upload document"
        onClick={onOpenUpload}
      />
    );
  }

  return (
    <div className="document-cards-grid">
      {documents.map((doc) => {
        const isReady = doc.status === 'Ready' || doc.status === 'Ready for RAG';
        const isProcessing = doc.status === 'Processing';

        return (
          <article className="document-card" key={doc.id}>
            <div className="document-card-top">
              <div className="doc-type-icon" aria-hidden="true">
                <FileText size={18} />
              </div>
              <span className={`doc-status-tag ${isReady ? 'ready' : isProcessing ? 'processing' : 'failed'}`}>
                {isReady ? 'Ready for RAG' : isProcessing ? 'Processing text...' : 'Failed'}
              </span>
            </div>

            <h4>{doc.name}</h4>
            <p className="doc-description">{doc.description}</p>

            <div className="doc-divider" />

            <div className="doc-meta-row">
              <span>
                <Users size={13} aria-hidden="true" />
                {doc.audience || 'All students'}
              </span>
              <span>
                <Clock size={13} aria-hidden="true" />
                {doc.uploadedAt}
              </span>
              <span className="doc-format-pill">
                {doc.fileType} • {doc.sizeFormatted}
              </span>
            </div>

            <div className="doc-actions-row">
              <button
                type="button"
                className="secondary-button"
                style={{ padding: '7px 12px', fontSize: '11px' }}
                onClick={() => onViewDetails(doc)}
              >
                <Eye size={13} aria-hidden="true" />
                View details
              </button>

              <button
                type="button"
                className="secondary-button"
                style={{ padding: '7px 12px', fontSize: '11px' }}
                onClick={() => onViewDocument(doc)}
                title={`View ${doc.name}`}
              >
                <FileSearch size={13} aria-hidden="true" />
                View document
              </button>

              <button
                type="button"
                className="icon-action-btn danger"
                style={{ marginLeft: 'auto' }}
                onClick={() => onDelete(doc)}
                title={`Delete ${doc.name}`}
                aria-label={`Delete ${doc.name}`}
              >
                <Trash2 size={15} aria-hidden="true" />
              </button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
