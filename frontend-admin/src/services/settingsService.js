import { apiClient } from './apiClient';

export const settingsService = {
  getPreferences: async () => {
    const res = await apiClient.get('/settings/preferences/');
    return res.data;
  },

  updatePreferences: async (preferences) => {
    const res = await apiClient.post('/settings/preferences/', preferences);
    return res.data;
  },

  getRolesPermissions: async () => {
    const res = await apiClient.get('/accounts/roles-permissions/');
    return res.data;
  },

  updateRolesPermissions: async (roles) => {
    const res = await apiClient.post('/accounts/roles-permissions/', { roles });
    return res.data;
  },

  exportUsersCSV: async () => {
    const res = await apiClient.get('/settings/export/?type=users', {
      responseType: 'blob',
    });
    // Trigger browser file download
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'ignite_users_export.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    return true;
  },

  exportAuditSummary: async () => {
    const res = await apiClient.get('/settings/export/?type=audit');
    return res.data;
  },
};

