import { apiClient, ApiError } from './apiClient';

export const broadcastService = {
  getBroadcasts: async (options = {}) => {
    try {
      const response = await apiClient.get(
        '/notifications/broadcast/history/',
        options
      );

      return Array.isArray(response.data)
        ? response.data
        : [];
    } catch (e) {
      if (
        e instanceof ApiError &&
        e.status === 404
      ) {
        return [];
      }

      throw e;
    }
  },

  createBroadcast: async (
    broadcastData,
    options = {}
  ) => {
    const response =
      await apiClient.post(
        '/notifications/broadcast/',
        broadcastData,
        options
      );

    return response.data;
  },
};
