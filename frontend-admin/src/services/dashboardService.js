import { apiClient, ApiError } from './apiClient';

export const dashboardService = {
  getSummary: async (options = {}) => {
    try {
      const response = await apiClient.get('/dashboard/', options);
      const data = response.data || response;
      return {
        broadcast_count: Number(data?.broadcast_count) || 0,
        scheduled_count: Number(data?.scheduled_count) || 0,
        upcoming_count: Number(data?.upcoming_count) || 0,
        buddy_enabled: Boolean(data?.buddy_enabled),
        total_users: Number(data?.total_users) || 0,
        total_trainees: Number(data?.total_trainees) || 0,
        total_cohorts: Number(data?.total_cohorts) || 0,
        total_batches: Number(data?.total_batches) || 0,
        total_sub_batches: Number(data?.total_sub_batches) || 0,
      };
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return {
          broadcast_count: 0,
          scheduled_count: 0,
          upcoming_count: 0,
          buddy_enabled: false,
          total_users: 0,
          total_trainees: 0,
          total_cohorts: 0,
          total_batches: 0,
          total_sub_batches: 0,
        };
      }
      throw e;
    }
  },
};
