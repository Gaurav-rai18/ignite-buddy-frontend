import { apiClient } from './apiClient';

export const buddyService = {
  getBuddySetting: async (options = {}) => {
    return apiClient.get('/settings/buddy/', options);
  },
  updateBuddySetting: async (enabled, options = {}) => {
    return apiClient.patch('/settings/buddy/', { enabled }, options);
  },
};
