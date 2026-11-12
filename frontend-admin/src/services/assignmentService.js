import { apiClient, ApiError } from './apiClient';

export const assignmentService = {
  getAssignments: async (params = {}, options = {}) => {
    try {
      const response = await apiClient.get('/assignments/', {
        params,
        ...options,
      });
      return Array.isArray(response.data) ? response.data : [];
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return [];
      }
      throw e;
    }
  },

  createAssignment: async (assignmentData, options = {}) => {
    const response = await apiClient.post('/assignments/', assignmentData, options);
    return response.data;
  },

  updateAssignmentDeadline: async (id, deadline, options = {}) => {
    const response = await apiClient.patch(
      `/assignments/${id}/`,
      { deadline },
      options
    );
    return response.data;
  },

  deleteAssignment: async (id, options = {}) => {
    const response = await apiClient.delete(`/assignments/${id}/`, options);
    return response.data;
  },

  getSubmissions: async (id, options = {}) => {
    const response = await apiClient.get(`/assignments/${id}/submissions/`, options);
    return response.data;
  },

  evaluateSubmission: async (assignmentId, recipientId, evaluationData, options = {}) => {
    const response = await apiClient.post(
      `/assignments/${assignmentId}/evaluate/${recipientId}/`,
      evaluationData,
      options
    );
    return response.data;
  },
};
