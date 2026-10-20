import { apiClient, ApiError } from './apiClient';

export const broadcastService = {
  getBroadcasts: async (options = {}) => {
    try {
      const list = await apiClient.get('/broadcasts/', options);
      return Array.isArray(list) ? list : [];
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return [];
      throw e;
    }
  },
  createBroadcast: async (broadcastData, options = {}) => {
    return apiClient.post('/broadcasts/', broadcastData, options);
  },
};
