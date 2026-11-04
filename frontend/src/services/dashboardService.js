/**
 * @file dashboardService.js
 * @description Service layer for fetching dashboard summary statistics from the Django REST API.
 *
 * Returns a normalized summary object with broadcast counts, scheduled counts,
 * upcoming event counts, and buddy feature status. All values are coerced to
 * safe types (Number / Boolean) to prevent NaN or undefined from reaching the UI.
 *
 * Data flow:
 *   Dashboard page / Hook → dashboardService → apiClient → Django /api/dashboard/
 *
 * @exports {Object} dashboardService - Object containing the getSummary method.
 */
import { apiClient, ApiError } from './apiClient';

export const dashboardService = {
  /**
   * Fetches aggregated dashboard statistics from the backend.
   * @param {Object} [options={}] - Request options (e.g. { signal }).
   * @returns {Promise<{broadcast_count: number, scheduled_count: number, upcoming_count: number, buddy_enabled: boolean}>}
   */
  getSummary: async (options = {}) => {
    try {
      const data = await apiClient.get('/dashboard/', options);
      // Normalize every field to a safe primitive type so the UI never renders NaN or undefined
      return {
        broadcast_count: Number(data?.broadcast_count) || 0,
        scheduled_count: Number(data?.scheduled_count) || 0,
        upcoming_count: Number(data?.upcoming_count) || 0,
        buddy_enabled: Boolean(data?.buddy_enabled),
      };
    } catch (e) {
      // Return zeroed-out defaults when the endpoint is not found (fresh deploy)
      if (e instanceof ApiError && e.status === 404) {
        return { broadcast_count: 0, scheduled_count: 0, upcoming_count: 0, buddy_enabled: false };
      }
      throw e;
    }
  },
};
