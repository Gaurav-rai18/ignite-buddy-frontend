import { apiClient } from './apiClient';

export const broadcastService = {
  getBroadcasts: async (options = {}) => {
    const list = await apiClient.get('/broadcasts/', options);
    return Array.isArray(list) ? list : [];
  },
  createBroadcast: async (broadcastData, options = {}) => {
    return apiClient.post('/broadcasts/', broadcastData, options);
  },
};
