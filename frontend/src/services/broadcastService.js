/**
 * @file broadcastService.js
 * @description Service layer for broadcast CRUD operations against the Django REST API.
 *
 * Provides methods to fetch all broadcasts and create new ones.
 * Each method accepts an optional `options` object (e.g. for AbortController signals).
 *
 * Data flow:
 *   Component / Hook → broadcastService → apiClient → Django /api/broadcasts/
 *
 * @exports {Object} broadcastService - Object containing getBroadcasts and createBroadcast methods.
 */
import { apiClient, ApiError } from './apiClient';

export const broadcastService = {
  /**
   * Fetches all broadcasts from the backend.
   * @param {Object} [options={}] - Request options (e.g. { signal } for abort support).
   * @returns {Promise<Array>} Array of broadcast objects, or empty array on 404.
   */
  getBroadcasts: async (options = {}) => {
    try {
      const list = await apiClient.get('/broadcasts/', options);
      // Defensive check: ensure the response is always an array for downstream consumers
      return Array.isArray(list) ? list : [];
    } catch (e) {
      // Gracefully handle 404 (e.g. endpoint not yet seeded) by returning empty list
      if (e instanceof ApiError && e.status === 404) return [];
      throw e;
    }
  },

  /**
   * Creates a new broadcast on the backend.
   * @param {Object} broadcastData - Payload with title, message, audience fields.
   * @param {Object} [options={}] - Request options (e.g. { signal }).
   * @returns {Promise<Object>} The newly created broadcast object from the API.
   */
  createBroadcast: async (broadcastData, options = {}) => {
    return apiClient.post('/broadcasts/', broadcastData, options);
  },
};
