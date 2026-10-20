import { apiClient, ApiError } from './apiClient';

export const scheduleService = {
  getSchedules: async (options = {}) => {
    try {
      const list = await apiClient.get('/schedules/', options);
      return Array.isArray(list) ? list : [];
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return [];
      throw e;
    }
  },
  createSchedule: async (scheduleData, options = {}) => {
    return apiClient.post('/schedules/', scheduleData, options);
  },
};
