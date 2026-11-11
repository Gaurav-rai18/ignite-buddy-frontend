import axios from 'axios';
import { API_BASE_URL, REQUEST_TIMEOUT_MS } from '../constants';

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// Token getter & unauthorized callback configured by authService
let tokenGetter = () => null;
let unauthorizedHandler = null;

export const setAuthTokenGetter = (fn) => {
  tokenGetter = fn;
};

export const setOnUnauthorized = (fn) => {
  unauthorizedHandler = fn;
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    // Zero Trust: read access token purely from active in-memory session
    const token = tokenGetter ? tokenGetter() : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Safety guard: if config.signal is provided but is not a valid AbortSignal,
    // remove it so Axios does not crash with "_config.signal.addEventListener is not a function"
    if (
      config.signal &&
      (typeof config.signal.addEventListener !== 'function' ||
        typeof config.signal.removeEventListener !== 'function')
    ) {
      delete config.signal;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Pass through Axios CanceledError and fetch AbortError unchanged.
    // These are intentional request cancellations triggered by AbortController.abort()
    // during React component unmount or refetch. They must NOT be re-wrapped as ApiError
    // because hooks inspect error.name / error.code to skip showing the error banner.
    if (
      axios.isCancel(error) ||
      error.name === 'CanceledError' ||
      error.name === 'AbortError' ||
      error.code === 'ERR_CANCELED'
    ) {
      return Promise.reject(error);
    }

    const status = error.response?.status || 0;

    // Zero Trust: on 401 Unauthorized, immediately revoke active in-memory session
    if (status === 401 && unauthorizedHandler) {
      unauthorizedHandler();
    }

    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'Network error encountered';

    throw new ApiError(message, status, error.response?.data);
  }
);
