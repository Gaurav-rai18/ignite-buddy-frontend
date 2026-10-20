import { apiClient, ApiError } from './apiClient';

export const buddyService = {
  getBuddySetting: async (options = {}) => {
    try {
      return await apiClient.get('/settings/buddy/', options);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return { enabled: false };
      }
      throw e;
    }
  },
  updateBuddySetting: async (enabled, options = {}) => {
    return apiClient.patch('/settings/buddy/', { enabled }, options);
  },
};
