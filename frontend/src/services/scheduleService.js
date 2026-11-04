import { apiClient, ApiError } from './apiClient';
import { API_BASE_URL } from '../constants';

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

  deleteSchedule: async (id, options = {}) => {
    return apiClient.delete(`/schedules/${id}/`, options);
  },

  getConfig: async (options = {}) => {
    return apiClient.get('/schedule-config/', options);
  },

  createBatch: async (batchData, options = {}) => {
    return apiClient.post('/schedule-batches/', batchData, options);
  },

  deleteBatch: async (id, options = {}) => {
    return apiClient.delete(`/schedule-batches/${id}/`, options);
  },

  createSubBatch: async (subBatchData, options = {}) => {
    return apiClient.post('/schedule-subbatches/', subBatchData, options);
  },

  deleteSubBatch: async (id, options = {}) => {
    return apiClient.delete(`/schedule-subbatches/${id}/`, options);
  },

  createTimeSlot: async (slotData, options = {}) => {
    return apiClient.post('/schedule-timeslots/', slotData, options);
  },

  updateTimeSlot: async (id, slotData, options = {}) => {
    return apiClient.patch(`/schedule-timeslots/${id}/`, slotData, options);
  },

  deleteTimeSlot: async (id, options = {}) => {
    return apiClient.delete(`/schedule-timeslots/${id}/`, options);
  },

  parseExcel: async (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/schedules/parse-excel/', formData, options);
  },

  getTemplateDownloadUrl: () => {
    const base = API_BASE_URL.replace(/\/+$/, '');
    return `${base}/schedule-template/`;
  },
};
