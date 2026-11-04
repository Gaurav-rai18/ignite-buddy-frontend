/**
 * scheduleService.js — API Client for Schedule Management & Configuration.
 *
 * Centralizes all HTTP communication with Django backend for:
 *  - Fetching & creating timetable schedules (/api/schedules/)
 *  - Fetching dynamic configuration metadata (/api/schedule-config/)
 *  - Dynamic CRUD for batches & sub-batches (/api/schedule-batches/, /api/schedule-subbatches/)
 *  - Dynamic CRUD for time slots (/api/schedule-timeslots/)
 *  - Uploading & parsing timetable Excel files (/api/schedules/parse-excel/)
 *  - Downloading official Excel timetable templates (/api/schedule-template/)
 */

import { apiClient, ApiError } from './apiClient';
import { API_BASE_URL } from '../constants';

export const scheduleService = {
  /**
   * Fetch all saved schedules (timetables, excel uploads, and links).
   * @param {Object} [options] Fetch options (e.g. abort signal).
   * @returns {Promise<Array>} List of schedule objects from database.
   */
  getSchedules: async (options = {}) => {
    try {
      const list = await apiClient.get('/schedules/', options);
      return Array.isArray(list) ? list : [];
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return [];
      throw e;
    }
  },

  /**
   * Save a new schedule item to the database.
   * Supports JSON payloads (native grid) or FormData (Excel spreadsheet).
   * @param {Object|FormData} scheduleData Schedule payload.
   * @param {Object} [options]
   * @returns {Promise<Object>} Created ScheduledLink record from backend.
   */
  createSchedule: async (scheduleData, options = {}) => {
    return apiClient.post('/schedules/', scheduleData, options);
  },

  /**
   * Delete an existing schedule by ID.
   * @param {number|string} id Schedule ID.
   * @param {Object} [options]
   */
  deleteSchedule: async (id, options = {}) => {
    return apiClient.delete(`/schedules/${id}/`, options);
  },

  /**
   * Fetch complete schedule configuration (locations, batches, time slots, weekdays).
   * @param {Object} [options]
   * @returns {Promise<{locations: Array, batches: Array, time_slots: Array, weekdays: Array}>}
   */
  getConfig: async (options = {}) => {
    return apiClient.get('/schedule-config/', options);
  },

  /**
   * Dynamically create a new batch group (e.g. Batch D).
   * @param {{name: string, code: string, subbatches_count?: number}} batchData
   */
  createBatch: async (batchData, options = {}) => {
    return apiClient.post('/schedule-batches/', batchData, options);
  },

  /**
   * Delete a batch group and cascade delete its sub-batches.
   * @param {number|string} id Batch ID.
   */
  deleteBatch: async (id, options = {}) => {
    return apiClient.delete(`/schedule-batches/${id}/`, options);
  },

  /**
   * Dynamically add a sub-batch (e.g. A5) to a parent batch.
   * @param {{batch: number, name: string, code: string}} subBatchData
   */
  createSubBatch: async (subBatchData, options = {}) => {
    return apiClient.post('/schedule-subbatches/', subBatchData, options);
  },

  /**
   * Delete a sub-batch.
   * @param {number|string} id SubBatch ID.
   */
  deleteSubBatch: async (id, options = {}) => {
    return apiClient.delete(`/schedule-subbatches/${id}/`, options);
  },

  /**
   * Add a new dynamic time slot (e.g. 4:30 PM – 6:00 PM).
   * @param {{start_time: string, end_time: string, label?: string}} slotData
   */
  createTimeSlot: async (slotData, options = {}) => {
    return apiClient.post('/schedule-timeslots/', slotData, options);
  },

  /**
   * Update an existing time slot.
   * @param {number|string} id
   * @param {{start_time: string, end_time: string, label?: string}} slotData
   */
  updateTimeSlot: async (id, slotData, options = {}) => {
    return apiClient.patch(`/schedule-timeslots/${id}/`, slotData, options);
  },

  /**
   * Delete a time slot.
   * @param {number|string} id
   */
  deleteTimeSlot: async (id, options = {}) => {
    return apiClient.delete(`/schedule-timeslots/${id}/`, options);
  },

  /**
   * Upload an Excel spreadsheet to backend for structure validation & timetable parsing.
   * @param {File} file Uploaded .xlsx or .xls file.
   * @returns {Promise<Object>} Parsed timetable preview data.
   */
  parseExcel: async (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/schedules/parse-excel/', formData, options);
  },

  /**
   * Returns the direct backend URL to download the standardized Excel timetable template.
   * @returns {string} Download URL.
   */
  getTemplateDownloadUrl: () => {
    const base = API_BASE_URL.replace(/\/+$/, '');
    return `${base}/schedule-template/`;
  },
};
