/**
 * @file validation.js
 * @description Client-side validation utilities for forms across the app.
 *
 * Provides pure validation functions (no side effects) that return
 * { isValid, errors } objects. Used by hooks (useBroadcasts, useSchedules)
 * before submitting data to the backend.
 *
 * Validators:
 *   - isValidHttpsUrl        — Ensures URLs use HTTPS protocol.
 *   - validateBroadcastForm  — Title, message, recipient mode validation.
 *   - validateScheduleForm   — Title, content, publish date/time validation.
 *   - timeStringToMinutes    — Parses "9:00 AM" → minutes since midnight.
 *   - validateTimeSlot       — Checks start/end time and overlap detection.
 *   - validateBuddyState     — Simple boolean type check.
 */
import {
  ROLE_OPTIONS,
  RECIPIENT_MODES,
  DEFAULT_RECIPIENT_MODE,
  VALIDATION_LIMITS,
  VALID_AUDIENCES,
} from '../constants';

/**
 * Validates HTTPS URL to prevent XSS or invalid protocols
 */
export function isValidHttpsUrl(urlString) {
  if (!urlString || typeof urlString !== 'string') return false;
  try {
    const parsed = new URL(urlString.trim());
    return parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * Validates broadcast form inputs
 */
export function validateBroadcastForm(data = {}) {
  const errors = {};
  const title = (data.title || '').trim();
  const message = (data.message || '').trim();
  const mode = data.recipientMode || DEFAULT_RECIPIENT_MODE;

  if (!title) {
    errors.title = 'Title is required.';
  } else if (title.length > VALIDATION_LIMITS.BROADCAST_TITLE_MAX) {
    errors.title = `Title must not exceed ${VALIDATION_LIMITS.BROADCAST_TITLE_MAX} characters.`;
  }

  if (!message) {
    errors.message = 'Message is required.';
  } else if (message.length > VALIDATION_LIMITS.BROADCAST_MESSAGE_MAX) {
    errors.message = `Message must not exceed ${VALIDATION_LIMITS.BROADCAST_MESSAGE_MAX} characters.`;
  }

  if (!RECIPIENT_MODES.includes(mode)) {
    errors.recipients = 'Invalid recipient type.';
  } else if (mode === 'By role') {
    const role = (data.role || '').trim();
    if (!role) {
      errors.recipients = 'Please select a role to send to.';
    } else if (!ROLE_OPTIONS.includes(role)) {
      errors.recipients = 'Invalid role selection.';
    }
  } else if (mode === 'Specific users') {
    const selected = Array.isArray(data.selectedUsers) ? data.selectedUsers : [];
    if (selected.length === 0) {
      errors.recipients = 'Select at least one recipient.';
    }
  } else {
    // "All users" mode. Verify audience is in VALID_AUDIENCES.
    const audience = (data.audience || '').trim();
    const allowed = VALID_AUDIENCES || ['All students', 'All faculty', 'All staff', 'All users', 'All campus members'];
    if (!audience) {
      errors.audience = 'Audience is required.';
    } else if (!allowed.includes(audience)) {
      errors.audience = 'Invalid audience selection.';
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Validates schedule form inputs
 */
export function validateScheduleForm(data = {}) {
  const errors = {};
  const title = (data.title || '').trim();
  const onedriveUrl = (data.onedrive_url || '').trim();
  const contentData = data.content_data;
  const excelFile = data.excel_file;

  if (!title) {
    errors.title = 'Schedule title is required.';
  } else if (title.length > VALIDATION_LIMITS.SCHEDULE_TITLE_MAX) {
    errors.title = `Title must not exceed ${VALIDATION_LIMITS.SCHEDULE_TITLE_MAX} characters.`;
  }

  if (!onedriveUrl && !contentData && !excelFile) {
    errors.onedrive_url = 'Schedule Grid data or Excel file is required.';
  } else if (onedriveUrl && !isValidHttpsUrl(onedriveUrl)) {
    errors.onedrive_url = 'Please provide a valid HTTPS URL (e.g. https://1drv.ms/...).';
  }

  const publishDate = (data.publish_date || '').trim();
  const publishTime = (data.publish_time || '').trim();
  const publishAt = (data.publish_at || (publishDate && publishTime ? `${publishDate}T${publishTime}` : '')).trim();

  if (data.publish_date !== undefined || data.publish_time !== undefined) {
    if (!publishDate) {
      errors.publish_date = 'Publish date is required.';
    }
    if (!publishTime) {
      errors.publish_time = 'Publish time is required.';
    }
  } else if (!publishAt) {
    errors.publish_at = 'Publish date and time is required.';
  }

  if (publishAt) {
    const dateObj = new Date(publishAt);
    if (Number.isNaN(dateObj.getTime())) {
      errors.publish_at = 'Invalid publish date and time.';
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Convert time string like '9:00 AM' or '09:00' to minutes from midnight
 */
export function timeStringToMinutes(timeStr) {
  if (!timeStr || typeof timeStr !== 'string') return null;
  const cleaned = timeStr.trim().toUpperCase();
  const isPM = cleaned.includes('PM');
  const isAM = cleaned.includes('AM');
  const match = cleaned.match(/(\d{1,2}):(\d{2})/);
  if (!match) return null;
  let hours = parseInt(match[1], 10);
  const minutes = parseInt(match[2], 10);
  if (isPM && hours < 12) hours += 12;
  if (isAM && hours === 12) hours = 0;
  return hours * 60 + minutes;
}

/**
 * Validates a new or updated time slot
 */
export function validateTimeSlot(startTime, endTime, existingSlots = [], currentId = null) {
  const errors = {};
  if (!startTime) errors.startTime = 'Start time is required.';
  if (!endTime) errors.endTime = 'End time is required.';

  const startMin = timeStringToMinutes(startTime);
  const endMin = timeStringToMinutes(endTime);

  if (startMin !== null && endMin !== null) {
    if (endMin <= startMin) {
      errors.endTime = 'End time must be later than start time.';
    } else {
      // Check for overlap
      const hasOverlap = existingSlots.some((slot) => {
        if (currentId && slot.id === currentId) return false;
        const sMin = timeStringToMinutes(slot.start_time);
        const eMin = timeStringToMinutes(slot.end_time);
        if (sMin === null || eMin === null) return false;
        // Overlap condition: start < otherEnd && end > otherStart
        return startMin < eMin && endMin > sMin;
      });
      if (hasOverlap) {
        errors.overlap = 'This time range overlaps with an existing time slot.';
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Validates buddy setting state
 */
export function validateBuddyState(enabled) {
  return typeof enabled === 'boolean';
}
