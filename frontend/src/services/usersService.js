import { apiClient } from './apiClient';

export const usersService = {
  getUsers: async () => {
    return apiClient.get('/users/');
  },

  createUser: async (userData) => {
    return apiClient.post('/users/', userData);
  },

  updateUser: async (userId, userData) => {
    return apiClient.patch(`/users/${userId}/`, userData);
  },

  deleteUser: async (userId) => {
    return apiClient.delete(`/users/${userId}/`);
  },
};
