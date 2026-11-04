/**
 * @file usersService.js
 * @description Service layer for user management CRUD operations against the Django REST API.
 *
 * Provides methods to list, create, update (partial), and delete campus users.
 * Uses PATCH (not PUT) for updates so only changed fields need to be sent.
 *
 * Data flow:
 *   ManageUsers page / useUsers hook → usersService → apiClient → Django /api/users/
 *
 * @exports {Object} usersService - Object containing getUsers, createUser, updateUser, deleteUser.
 */
import { apiClient } from './apiClient';

export const usersService = {
  /** Fetches the full list of campus users. */
  getUsers: async () => {
    return apiClient.get('/users/');
  },

  /**
   * Creates a new user on the backend.
   * @param {Object} userData - User fields (username, email, batch, subbatch, etc.).
   */
  createUser: async (userData) => {
    return apiClient.post('/users/', userData);
  },

  /**
   * Partially updates an existing user.
   * @param {string|number} userId - The user's primary key.
   * @param {Object} userData - Only the fields to update.
   */
  updateUser: async (userId, userData) => {
    return apiClient.patch(`/users/${userId}/`, userData);
  },

  /**
   * Deletes a user by ID.
   * @param {string|number} userId - The user's primary key.
   */
  deleteUser: async (userId) => {
    return apiClient.delete(`/users/${userId}/`);
  },
};
