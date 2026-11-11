import { apiClient, ApiError } from './apiClient';

export const scheduleService = {
  getSchedules: async (params = {}, options = {}) => {
    try {
      const response = await apiClient.get('/schedules/', { params, ...options });
      return Array.isArray(response.data) ? response.data : [];
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return [];
      throw e;
    }
  },

  getScheduleById: async (id, options = {}) => {
    const response = await apiClient.get(`/schedules/${id}/`, options);
    return response.data;
  },

  createSchedule: async (scheduleData, options = {}) => {
    const response = await apiClient.post('/schedules/', scheduleData, options);
    return response.data;
  },

  updateSchedule: async (id, scheduleData, options = {}) => {
    const response = await apiClient.put(`/schedules/${id}/`, scheduleData, options);
    return response.data;
  },

  deleteSchedule: async (id, options = {}) => {
    const response = await apiClient.delete(`/schedules/${id}/`, options);
    return response.data;
  },

  activateSchedule: async (id, options = {}) => {
    try {
      const response = await apiClient.post(`/schedules/${id}/activate/`, {}, options);
      return response.data;
    } catch (e) {
      // Fallback to PUT with force_activate: true
      const fallback = await apiClient.put(`/schedules/${id}/`, { is_active: true, force_activate: true }, options);
      return fallback.data;
    }
  },

  parseExcelSchedule: async (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/schedules/parse-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      ...options,
    });
    return response.data;
  },

  getLiveTimetable: async (batch = '*', options = {}) => {
    const response = await apiClient.get('/schedules/live-timetable/', {
      params: { batch },
      ...options,
    });
    return response.data;
  },

  getCurrentSeating: async (params = {}, options = {}) => {
    const response = await apiClient.get('/schedules/current-seating/', {
      params,
      ...options,
    });
    return response.data;
  },
};
