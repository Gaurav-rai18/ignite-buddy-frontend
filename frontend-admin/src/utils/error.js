/**
 * Returns true when an error is an expected Axios/fetch request cancellation
 * (AbortController.abort() called on unmount or refetch). These must NOT be
 * shown to the user as error banners.
 *
 * Axios surfaces cancellations as:
 *   - error.name  === 'CanceledError'  (Axios >= 0.22)
 *   - error.code  === 'ERR_CANCELED'   (Axios >= 0.27)
 * fetch/XHR surfaces them as:
 *   - error.name  === 'AbortError'
 */
export function isRequestCancellation(error) {
  if (!error) return false;
  return (
    error.name === 'CanceledError' ||
    error.name === 'AbortError' ||
    error.code === 'ERR_CANCELED' ||
    // Axios re-throws as ApiError with message 'canceled' when
    // the underlying axios request was cancelled via AbortSignal
    error.message === 'canceled'
  );
}

/**
 * Normalizes any genuine (non-cancellation) error into a clear human-readable
 * string. Always call isRequestCancellation() first and skip formatErrorMessage
 * for cancellations.
 */
export function formatErrorMessage(error) {
  if (!error) return 'An unexpected error occurred. Please try again.';

  if (typeof error === 'string') return error;

  // Safety net: should have been filtered before calling this, but guard anyway
  if (isRequestCancellation(error)) return '';

  if (error.message === 'Failed to fetch' || error.message?.includes('NetworkError')) {
    return 'Unable to reach the server. Check that the Ignite Buddy backend is running.';
  }

  if (error.message?.includes('Network Error') || error.message?.includes('ECONNREFUSED')) {
    return 'Cannot connect to the backend. Check that the Django server is running on port 8765.';
  }

  if (error.details) {
    if (typeof error.details === 'string') {
      const isHtml = /<!DOCTYPE|<html|<head|<body/i.test(error.details);
      if (isHtml) {
        if (error.details.includes('Page not found') || error.status === 404) {
          return 'Backend endpoint not found (404). Verify the Ignite Buddy Django backend is running.';
        }
        return `Backend returned an unexpected HTML response (HTTP ${error.status || 'unknown'}). Check backend server logs.`;
      }
      return error.details;
    }
    if (error.details.detail) return error.details.detail;
    // DRF field errors dictionary { field: ['error message'] }
    if (typeof error.details === 'object') {
      const messages = Object.entries(error.details)
        .map(([field, errs]) => {
          const text = Array.isArray(errs) ? errs.join(' ') : String(errs);
          return `${field}: ${text}`;
        })
        .filter(Boolean);
      if (messages.length) return messages.join(' | ');
    }
  }

  if (error.status === 401) {
    return 'Session expired. Please sign in again.';
  }

  if (error.status === 403) {
    return 'You do not have permission to perform this action.';
  }

  if (error.status === 404) {
    return 'The requested resource was not found (404). Verify the backend endpoint exists.';
  }

  if (error.status >= 500) {
    return `Server error (${error.status}). Please try again or check the backend logs.`;
  }

  return error.message || 'Request failed. Please try again.';
}
