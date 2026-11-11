/**
 * Formats a date value into en-IN localized display string.
 * Gracefully handles invalid dates, null, or undefined.
 */
export function formatDate(value) {
  if (!value) return '';
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return String(value);
  }
}

/**
 * Returns current local time formatted for <input type="datetime-local">
 * e.g. YYYY-MM-DDTHH:mm
 */
export function getMinDateTimeLocal() {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 16);
}

/**
 * Converts a datetime-local input string (YYYY-MM-DDTHH:mm) to an ISO string
 */
export function toIsoUtcString(datetimeLocalValue) {
  if (!datetimeLocalValue) return null;
  const d = new Date(datetimeLocalValue);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}
