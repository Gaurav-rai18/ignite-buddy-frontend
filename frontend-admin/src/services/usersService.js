// import { apiClient } from "./apiClient";

// export const usersService = {
//   getUsers: async () => {
//     return await apiClient.get(
//       "/accounts/users/"
//     );
//   },

//   createUser: async (userData) => {
//     return await apiClient.post(
//       "/accounts/users/",
//       userData
//     );
//   },

//   updateUser: async (
//     userId,
//     userData
//   ) => {
//     return await apiClient.patch(
//       `/accounts/users/${userId}/`,
//       userData
//     );
//   },

//   deleteUser: async (userId) => {
//     return await apiClient.delete(
//       `/accounts/users/${userId}/`
//     );
//   },

//   getUserById: async (userId) => {
//     return await apiClient.get(
//       `/accounts/users/${userId}/`
//     );
//   },

//   resetPassword: async (
//     userId,
//     newPassword
//   ) => {
//     return await apiClient.post(
//       `/accounts/users/${userId}/reset-password/`,
//       {
//         new_password: newPassword,
//       }
//     );
//   },
// };

import { apiClient } from "./apiClient";

export const usersService = {
  getUsers: async () => {
    const response = await apiClient.get(
      "/accounts/users/"
    );

    return response.data;
  },

  createUser: async (userData) => {
    const response = await apiClient.post(
      "/accounts/users/",
      userData
    );

    return response.data;
  },

  updateUser: async (
    userId,
    userData
  ) => {
    const response = await apiClient.patch(
      `/accounts/users/${userId}/`,
      userData
    );

    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await apiClient.delete(
      `/accounts/users/${userId}/`
    );

    return response.data;
  },

  getUserById: async (userId) => {
    const response = await apiClient.get(
      `/accounts/users/${userId}/`
    );

    return response.data;
  },

  resetPassword: async (
    userId,
    newPassword
  ) => {
    const response = await apiClient.post(
      `/accounts/users/${userId}/reset-password/`,
      {
        new_password: newPassword,
      }
    );

    return response.data;
  },
  bulkUploadUsers: async (file) => {

    const formData =
      new FormData();
  
    formData.append(
      "file",
      file
    );
  
    const response =
      await apiClient.post(
        "/accounts/users/bulk-upload/",
        formData,
        {
          headers: {
            "Content-Type":
            "multipart/form-data",
          },
        }
      );
  
    return response.data;
  },

  getCohorts: async () => {
    const response = await apiClient.get("/accounts/cohorts/");
    return Array.isArray(response.data) ? response.data : response.data?.results || [];
  },

  getBatches: async (cohortId) => {
    const response = await apiClient.get("/accounts/batches/", {
      params: cohortId ? { cohort: cohortId } : {},
    });
    return Array.isArray(response.data) ? response.data : response.data?.results || [];
  },

  getSubBatches: async (batchId) => {
    const response = await apiClient.get("/accounts/sub-batches/", {
      params: batchId ? { batch: batchId } : {},
    });
    return Array.isArray(response.data) ? response.data : response.data?.results || [];
  },

  getLabs: async () => {
    const response = await apiClient.get("/accounts/labs/");
    return Array.isArray(response.data) ? response.data : response.data?.results || [];
  },

  createSubBatch: async (data) => {
    const response = await apiClient.post("/accounts/sub-batches/", data);
    return response.data;
  },

  createBatch: async (data) => {
    const response = await apiClient.post("/accounts/batches/", data);
    return response.data;
  },

  createCohort: async (data) => {
    const response = await apiClient.post("/accounts/cohorts/", data);
    return response.data;
  },

  createLab: async (data) => {
    const response = await apiClient.post("/accounts/labs/", data);
    return response.data;
  },

  deleteSubBatch: async (id) => {
    const response = await apiClient.delete(`/accounts/sub-batches/${id}/`);
    return response.data;
  },

  deleteBatch: async (id) => {
    const response = await apiClient.delete(`/accounts/batches/${id}/`);
    return response.data;
  },

  deleteCohort: async (id) => {
    const response = await apiClient.delete(`/accounts/cohorts/${id}/`);
    return response.data;
  },

  deleteLab: async (id) => {
    const response = await apiClient.delete(`/accounts/labs/${id}/`);
    return response.data;
  },
};
