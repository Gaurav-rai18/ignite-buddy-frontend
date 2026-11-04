/**
 * @file AddDocuments.jsx
 * @description Document upload and knowledge-base management page for the Ignite Buddy admin panel.
 *
 * This page lets administrators:
 *  - Upload PDF/text files that feed into the Buddy RAG (Retrieval-Augmented Generation) pipeline.
 *  - Search, filter (by processing status), view, and delete existing documents.
 *  - Refresh the document list from the backend API.
 *
 * Data flow:
 *  useDocuments() hook  →  fetches documents from the Django REST API
 *                       →  exposes CRUD helpers (uploadDoc, deleteDoc, refetch)
 *                       →  provides client-side search & status filtering
 *
 * Key exports:
 *  - AddDocuments (React component) — the main page rendered at the /documents route.
 *
 * @module pages/AddDocuments
 */

import React, { useState } from 'react';
import { FileText, Plus, Search, RotateCw, Sparkles } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';
import { DocumentList } from '../../components/documents/DocumentList';
import { DocumentUploadModal } from '../../components/documents/DocumentUploadModal';
import { DocumentDetailsModal } from '../../components/documents/DocumentDetailsModal';
import { DocumentViewerModal } from '../../components/documents/DocumentViewerModal';
import { DeleteDocumentDialog } from '../../components/documents/DeleteDocumentDialog';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

/**
 * AddDocuments page component.
 * Renders the full document management UI — upload modal, search/filter bar,
 * document list, detail viewer, and delete confirmation dialog.
 *
 * @param {Object}   props
 * @param {Function} [props.onNotify] - Callback to show a toast/notification in the app shell.
 * @returns {JSX.Element}
 */
export function AddDocuments({ onNotify }) {
  // Pull all document state and CRUD actions from the custom hook.
  // The hook manages API calls, search filtering, and status filtering internally.
  const {
    documents,
    filteredDocuments,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    uploadDoc,
    deleteDoc,
    refetch,
  } = useDocuments();

  // --- Modal / dialog visibility state ---
  const [isUploadOpen, setIsUploadOpen] = useState(false);       // Upload modal open?
  const [selectedDocDetails, setSelectedDocDetails] = useState(null); // Doc shown in details modal
  const [viewingDoc, setViewingDoc] = useState(null);            // Doc shown in viewer modal
  const [deletingDoc, setDeletingDoc] = useState(null);          // Doc pending delete confirmation
  const [isRefreshing, setIsRefreshing] = useState(false);       // Refresh-button spinner guard

  /** Re-fetches the document list from the API and notifies the user on completion. */
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
    if (onNotify) {
      onNotify('Document knowledge base refreshed');
    }
  };

  /** Sends the file + metadata to the backend and triggers RAG processing. */
  const handleUploadSubmit = async (uploadData) => {
    const created = await uploadDoc(uploadData);
    if (onNotify) {
      onNotify(`Document "${created.name}" uploaded. RAG processing started.`);
    }
  };

  /** Permanently removes a document from the knowledge base via API. */
  const handleDeleteConfirm = async (docId) => {
    await deleteDoc(docId);
    if (onNotify) {
      onNotify('Document removed from knowledge base');
    }
  };

  /** Status filter options — mirrors the possible document processing states from the API. */
  const filterTabs = ['All', 'Ready', 'Processing', 'Failed'];

  return (
    <>
      <div className="welcome-row">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" aria-hidden="true" />
            KNOWLEDGE BASE & RAG
          </div>
          <h1>Add Documents</h1>
          <p className="subheading">
            Upload documents and manage knowledge sources for Buddy.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={handleRefresh}
          disabled={loading || isRefreshing}
        >
          <RotateCw
            size={14}
            style={{
              animation: loading || isRefreshing ? 'spin 1s linear infinite' : 'none',
            }}
            aria-hidden="true"
          />
          {loading || isRefreshing ? 'Refreshing...' : 'Refresh data'}
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <section className="panel" style={{ padding: '24px' }}>
        <div className="panel-heading" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="stat-icon primary" style={{ width: '40px', height: '40px' }} aria-hidden="true">
              <FileText size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', marginBottom: '2px' }}>Add documents</h3>
              <p>Upload PDF or text files to use as knowledge sources for Buddy</p>
            </div>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={() => setIsUploadOpen(true)}
          >
            <Plus size={16} aria-hidden="true" />
            Add document
          </button>
        </div>

        <div className="table-search-bar">
          <div className="search-input-wrap">
            <Search size={16} aria-hidden="true" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search documents by name or description"
            />
          </div>
          <span className="search-count-badge">
            {filteredDocuments.length} documents
          </span>
        </div>

        <div className="doc-filter-pills" role="tablist" aria-label="Filter documents by status">
          {filterTabs.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={statusFilter === tab}
              className={`doc-filter-pill ${statusFilter === tab ? 'active' : ''}`}
              onClick={() => setStatusFilter(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <DocumentList
          documents={filteredDocuments}
          loading={loading}
          onViewDetails={(doc) => setSelectedDocDetails(doc)}
          onViewDocument={(doc) => setViewingDoc(doc)}
          onDelete={(doc) => setDeletingDoc(doc)}
          onOpenUpload={() => setIsUploadOpen(true)}
        />

        <div className="card-table-footer" style={{ marginTop: '20px' }}>
          <span>
            Showing {filteredDocuments.length} of {documents.length} knowledge sources
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Sparkles size={13} color="var(--color-primary)" aria-hidden="true" />
            Processed documents are indexed for Buddy RAG retrieval
          </span>
        </div>
      </section>

      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUploadSubmit}
      />

      <DocumentDetailsModal
        isOpen={Boolean(selectedDocDetails)}
        document={selectedDocDetails}
        onClose={() => setSelectedDocDetails(null)}
      />

      <DocumentViewerModal
        isOpen={Boolean(viewingDoc)}
        document={viewingDoc}
        onClose={() => setViewingDoc(null)}
      />

      <DeleteDocumentDialog
        isOpen={Boolean(deletingDoc)}
        document={deletingDoc}
        onClose={() => setDeletingDoc(null)}
        onConfirm={handleDeleteConfirm}
      />
    </>
  );
}
