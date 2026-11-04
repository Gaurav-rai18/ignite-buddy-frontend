/**
 * @file buddyService.js
 * @description Service layer for the "Ignite Buddy" AI assistant feature toggle.
 *
 * The buddy setting is a single boolean flag (`enabled`) stored on the backend.
 * This service reads and updates that flag via the Django REST API.
 *
 * Data flow:
 *   Component / Hook → buddyService → apiClient → Django /api/settings/buddy/
 *
 * @exports {Object} buddyService - Object containing getBuddySetting and updateBuddySetting methods.
 */
import { apiClient, ApiError } from './apiClient';

export const buddyService = {
  /**
   * Retrieves the current buddy enabled/disabled setting from the backend.
   * @param {Object} [options={}] - Request options (e.g. { signal } for abort support).
   * @returns {Promise<{enabled: boolean}>} The buddy setting object.
   */
  getBuddySetting: async (options = {}) => {
    try {
      return await apiClient.get('/settings/buddy/', options);
    } catch (e) {
      // If the setting has never been created (404), default to disabled
      if (e instanceof ApiError && e.status === 404) {
        return { enabled: false };
      }
      throw e;
    }
  },

  /**
   * Updates the buddy enabled/disabled setting on the backend via PATCH.
   * @param {boolean} enabled - Whether the buddy feature should be enabled.
   * @param {Object} [options={}] - Request options.
   * @returns {Promise<{enabled: boolean}>} The updated buddy setting from the API.
   */
  updateBuddySetting: async (enabled, options = {}) => {
    return apiClient.patch('/settings/buddy/', { enabled }, options);
  },
};
