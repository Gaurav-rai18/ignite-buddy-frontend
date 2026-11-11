import { apiClient } from './apiClient';

export const profileService = {
  getProfile: async () => {
    const res = await apiClient.get('/accounts/me/');
    return res.data;
  },

  updateProfile: async (data) => {
    const res = await apiClient.patch('/accounts/me/', data);
    return res.data;
  },

  changePassword: async ({ oldPassword, newPassword }) => {
    const res = await apiClient.post('/accounts/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return res.data;
  },
};

