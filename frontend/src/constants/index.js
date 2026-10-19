export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const AUDIENCE_OPTIONS = [
  'All students',
  'First year',
  'Second year',
  'Third year',
  'Final year',
];

export const VALIDATION_LIMITS = {
  BROADCAST_TITLE_MAX: 160,
  BROADCAST_MESSAGE_MAX: 2000,
  SCHEDULE_TITLE_MAX: 160,
};

export const REQUEST_TIMEOUT_MS = 15000;
