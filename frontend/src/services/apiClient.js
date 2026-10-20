import { API_BASE_URL, REQUEST_TIMEOUT_MS } from '../constants';

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Normalizes URL path with base URL
 */
function resolveUrl(path) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const base = API_BASE_URL.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
}

/**
 * Central fetch wrapper with timeout, signal, and error handling
 */
async function request(path, { method = 'GET', body, headers = {}, signal, timeout = REQUEST_TIMEOUT_MS } = {}) {
  const url = resolveUrl(path);

  // Handle timeout via AbortController if supported and no external signal provided
  const controller = new AbortController();
  let timerId;
  let activeSignal = signal;

  if (!activeSignal && timeout > 0) {
    timerId = setTimeout(() => controller.abort(), timeout);
    activeSignal = controller.signal;
  }

  const finalHeaders = {
    Accept: 'application/json',
    ...headers,
  };

  if (body !== undefined && !(body instanceof FormData)) {
    finalHeaders['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(url, {
      method,
      headers: finalHeaders,
      body: body !== undefined && !(body instanceof FormData) ? JSON.stringify(body) : body,
      signal: activeSignal,
    });

    if (timerId) clearTimeout(timerId);

    // 204 No Content
    if (res.status === 204) {
      return null;
    }

    // Try parsing JSON response
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }

    if (!res.ok) {
      let message =
        (typeof data === 'object' && data?.detail) ||
        (typeof data === 'object' && data?.message);

      if (!message) {
        if (res.status === 404) {
          message = `Endpoint ${path} was not found (404). Please verify backend is running.`;
        } else {
          message = `Request failed with status ${res.status}`;
        }
      }

      throw new ApiError(message, res.status, data);
    }

    return data;
  } catch (error) {
    if (timerId) clearTimeout(timerId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out or was aborted.', 0, null);
    }

    throw new ApiError(error.message || 'Network error encountered.', 0, null);
  }
}

export const apiClient = {
  get: (path, options) => request(path, { method: 'GET', ...options }),
  post: (path, body, options) => request(path, { method: 'POST', body, ...options }),
  patch: (path, body, options) => request(path, { method: 'PATCH', body, ...options }),
  put: (path, body, options) => request(path, { method: 'PUT', body, ...options }),
  delete: (path, options) => request(path, { method: 'DELETE', ...options }),
};
