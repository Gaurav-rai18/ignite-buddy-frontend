import { apiClient, ApiError } from './apiClient';

export const dashboardService = {
  getSummary: async (options = {}) => {
    try {
      const data = await apiClient.get('/dashboard/', options);
      return {
        broadcast_count: Number(data?.broadcast_count) || 0,
        scheduled_count: Number(data?.scheduled_count) || 0,
        upcoming_count: Number(data?.upcoming_count) || 0,
        buddy_enabled: Boolean(data?.buddy_enabled),
      };
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return { broadcast_count: 0, scheduled_count: 0, upcoming_count: 0, buddy_enabled: false };
      }
      throw e;
    }
  },
};
