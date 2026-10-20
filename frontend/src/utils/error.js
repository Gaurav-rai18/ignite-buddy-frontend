/**
 * Normalizes any error or API response into a clear human-readable string.
 */
export function formatErrorMessage(error) {
  if (!error) return 'An unexpected error occurred. Please try again.';

  if (typeof error === 'string') return error;

  if (error.name === 'AbortError') {
    return 'The request timed out or was cancelled. Please try again.';
  }

  if (error.message === 'Failed to fetch' || error.message?.includes('NetworkError')) {
    return 'Unable to reach the server. Please check that the Django backend is running at http://127.0.0.1:8000.';
  }

  if (error.details) {
    if (typeof error.details === 'string') {
      const isHtml = /<!DOCTYPE|<html|<head|<body/i.test(error.details);
      if (isHtml) {
        if (error.details.includes('Page not found') || error.status === 404) {
          return 'Backend endpoint not found (404). Please verify that the Ignite Buddy Django backend is running on http://127.0.0.1:8000 and not another service.';
        }
        return `Backend returned an unexpected HTML response (HTTP ${error.status || 'unknown'}). Please check backend server logs.`;
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

  if (error.status === 404) {
    return 'The requested resource or endpoint was not found (404). Please verify the Django backend is running on http://127.0.0.1:8000.';
  }

  return error.message || 'Request failed. Please try again.';
}
