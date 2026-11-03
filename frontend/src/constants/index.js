export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

// Schedule Grid Defaults
export const SCHEDULE_TIME_SLOTS = ['9:00 AM', '11:30 AM', '2:00 PM', '4:30 PM'];
export const SCHEDULE_LOCATIONS = ['Lab 1', 'Lab 2', 'Lab 3', 'Lab 4', 'Incubator'];
export const SCHEDULE_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// Recipient targeting modes for the Broadcast composer
export const RECIPIENT_MODES = ['All users', 'By role', 'Specific users'];

export const DEFAULT_RECIPIENT_MODE = 'All users';

// Role-based targeting uses the existing Broadcast `audience` label.
export const ROLE_OPTIONS = ['All Trainees', 'All Admins'];

// The backend Broadcast model now supports a recipients field.
export const SPECIFIC_RECIPIENTS_SUPPORTED = true;

export const VALIDATION_LIMITS = {
  BROADCAST_TITLE_MAX: 160,
  BROADCAST_MESSAGE_MAX: 2000,
  SCHEDULE_TITLE_MAX: 160,
};

export const REQUEST_TIMEOUT_MS = 15000;
