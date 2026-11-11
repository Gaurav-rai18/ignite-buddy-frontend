import { apiClient } from './apiClient';

export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const documentsService = {
  getDocuments: async (options = {}) => {
    const response = await apiClient.get('/documents/', options);
    return Array.isArray(response.data) ? response.data : [];
  },

  uploadDocument: async ({
    file,
    name,
    audience = 'All students',
    description = '',
    cohort_id,
    batch_id,
  }, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (audience) formData.append('audience', audience);
    if (description) formData.append('description', description);
    if (cohort_id) formData.append('cohort_id', cohort_id);
    if (batch_id) formData.append('batch_id', batch_id);

    const response = await apiClient.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      ...options,
    });
    return response.data;
  },

  deleteDocument: async (docId, options = {}) => {
    const response = await apiClient.delete(`/documents/${docId}/`, options);
    return response.data;
  },

  getDocumentDetails: async (docId, options = {}) => {
    const response = await apiClient.get(`/documents/${docId}/`, options);
    return response.data;
  },

  /**
   * Retrieves an active URL/Blob for opening or viewing the document
   */
  getDocumentBlobUrl: (doc) => {
    if (!doc) return null;

    if (doc.fileUrl) {
      return doc.fileUrl;
    }

    if (doc.content) {
      const mime = doc.fileType === 'PDF' ? 'text/plain' : 'text/plain';
      const blob = new Blob([doc.content], { type: mime });
      return URL.createObjectURL(blob);
    }

    return null;
  },
};
