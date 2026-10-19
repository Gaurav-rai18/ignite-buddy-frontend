import { apiClient } from './apiClient';

export const scheduleService = {
  getSchedules: async (options = {}) => {
    const list = await apiClient.get('/schedules/', options);
    return Array.isArray(list) ? list : [];
  },
  createSchedule: async (scheduleData, options = {}) => {
    return apiClient.post('/schedules/', scheduleData, options);
  },
};
