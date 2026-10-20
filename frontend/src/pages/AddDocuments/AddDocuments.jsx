import React, { useState } from 'react';
import { FileText, Plus, Search, RotateCw, Sparkles, Filter } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';
import { DocumentList } from '../../components/documents/DocumentList';
import { DocumentUploadModal } from '../../components/documents/DocumentUploadModal';
import { DocumentDetailsModal } from '../../components/documents/DocumentDetailsModal';
import { DeleteDocumentDialog } from '../../components/documents/DeleteDocumentDialog';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export function AddDocuments({ onNotify }) {
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

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);
  const [deletingDoc, setDeletingDoc] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
    if (onNotify) {
      onNotify('Document knowledge base refreshed');
    }
  };

  const handleUploadSubmit = async (uploadData) => {
    const created = await uploadDoc(uploadData);
    if (onNotify) {
      onNotify(`Document "${created.name}" uploaded. RAG processing started.`);
    }
  };

  const handleDeleteConfirm = async (docId) => {
    await deleteDoc(docId);
    if (onNotify) {
      onNotify('Document removed from knowledge base');
    }
  };

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

      <DeleteDocumentDialog
        isOpen={Boolean(deletingDoc)}
        document={deletingDoc}
        onClose={() => setDeletingDoc(null)}
        onConfirm={handleDeleteConfirm}
      />
    </>
  );
}
