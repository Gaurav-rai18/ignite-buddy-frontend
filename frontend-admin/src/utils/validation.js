import {
  ROLE_OPTIONS,
  RECIPIENT_MODES,
  DEFAULT_RECIPIENT_MODE,
  VALIDATION_LIMITS,
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

  // if (!RECIPIENT_MODES.includes(mode)) {
  //   errors.recipients = 'Invalid recipient type.';
  // } else if (mode === 'By role') {
  //   const role = (data.role || '').trim();
  //   if (!role) {
  //     errors.recipients = 'Please select a role to send to.';
  //   } else if (!ROLE_OPTIONS.includes(role)) {
  //     errors.recipients = 'Invalid role selection.';
  //   }
  // } else if (mode === 'Specific users') {
  //   const selected = Array.isArray(data.selectedUsers) ? data.selectedUsers : [];
  //   if (selected.length === 0) {
  //     errors.recipients = 'Select at least one recipient.';
  //   }
  // } else {
  //   // "All users" still maps to the existing audience label used by the backend.
  //   const audience = (data.audience || '').trim();
  //   if (!audience) {
  //     errors.audience = 'Audience is required.';
  //   } else if (audience !== "All Trainee" && !ROLE_OPTIONS.includes(audience)) {
  //     errors.audience = 'Invalid audience selection.';
  //   }
  // }
  if (!RECIPIENT_MODES.includes(mode)) {
    errors.recipients = 'Invalid recipient type.';
  }
  else if (mode === 'By role') {
    const role = (data.role || '').trim();
  
    if (!role) {
      errors.recipients = 'Please select a role to send to.';
    }
  }
  else if (mode === 'Specific users') {
    const selected = Array.isArray(data.selectedUsers)
      ? data.selectedUsers
      : [];
  
    if (selected.length === 0) {
      errors.recipients = 'Select at least one recipient.';
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

  if (!title) {
    errors.title = 'Schedule title is required.';
  } else if (title.length > VALIDATION_LIMITS.SCHEDULE_TITLE_MAX) {
    errors.title = `Title must not exceed ${VALIDATION_LIMITS.SCHEDULE_TITLE_MAX} characters.`;
  }

  if (!onedriveUrl) {
    errors.onedrive_url = 'OneDrive sharing link is required.';
  } else if (!isValidHttpsUrl(onedriveUrl)) {
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
 * Validates buddy setting state
 */
export function validateBuddyState(enabled) {
  return typeof enabled === 'boolean';
}
