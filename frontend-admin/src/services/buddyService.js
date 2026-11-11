import { apiClient, ApiError } from './apiClient';

export const buddyService = {
  getBuddySetting: async (options = {}) => {
    try {
      const response = await apiClient.get('/settings/buddy/', options);
      return response.data || response;
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return { enabled: false };
      }
      throw e;
    }
  },
  updateBuddySetting: async (payload, options = {}) => {
    const body = typeof payload === 'boolean' ? { enabled: payload } : payload;
    const response = await apiClient.patch('/settings/buddy/', body, options);
    return response.data || response;
  },
};
