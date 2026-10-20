import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { documentsService } from '../services/documentsService';

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All'); // 'All' | 'Ready' | 'Processing' | 'Failed'

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await documentsService.getDocuments();
      if (isMountedRef.current) {
        setDocuments(data);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.message || 'Failed to load documents');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // Periodic status polling if any document is currently in 'Processing' state
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'Processing');
    if (!hasProcessing) return;

    const interval = setInterval(async () => {
      const updated = await documentsService.getDocuments();
      if (isMountedRef.current) {
        setDocuments(updated);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [documents]);

  const uploadDoc = useCallback(async ({ file, audience, description }) => {
    setIsUploading(true);
    try {
      const newDoc = await documentsService.uploadDocument({ file, audience, description });
      if (isMountedRef.current) {
        setDocuments((prev) => [newDoc, ...prev]);
      }
      return newDoc;
    } finally {
      if (isMountedRef.current) {
        setIsUploading(false);
      }
    }
  }, []);

  const deleteDoc = useCallback(async (docId) => {
    await documentsService.deleteDocument(docId);
    if (isMountedRef.current) {
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    }
  }, []);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesStatus =
        statusFilter === 'All' ||
        (statusFilter === 'Ready' && (doc.status === 'Ready' || doc.status === 'Ready for RAG')) ||
        (statusFilter === 'Processing' && doc.status === 'Processing') ||
        (statusFilter === 'Failed' && doc.status === 'Failed');

      if (!matchesStatus) return false;

      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();
      return (
        doc.name.toLowerCase().includes(q) ||
        doc.fileName.toLowerCase().includes(q) ||
        doc.fileType.toLowerCase().includes(q) ||
        (doc.description && doc.description.toLowerCase().includes(q))
      );
    });
  }, [documents, searchQuery, statusFilter]);

  return {
    documents,
    filteredDocuments,
    loading,
    error,
    isUploading,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    uploadDoc,
    deleteDoc,
    refetch: fetchDocs,
  };
}
