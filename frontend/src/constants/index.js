/**
 * @file constants/index.js
 * @description Application-wide constants for the Ignite Buddy admin panel.
 *
 * Centralizes configuration values used by both the schedule module
 * and the broadcast module so they can be changed in one place.
 *
 * Categories:
 *   - API_BASE_URL:           Backend API root (configurable via .env).
 *   - Schedule defaults:      Locations, days, time slots, batch groups.
 *   - Broadcast settings:     Recipient modes, role options, audiences.
 *   - Validation limits:      Max lengths and file sizes.
 *   - REQUEST_TIMEOUT_MS:     Global fetch timeout.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

// Schedule Defaults (Five-day working schedule & seven locations)
export const DEFAULT_SCHEDULE_LOCATIONS = [
  'Lab 1',
  'Lab 2',
  'Lab 3',
  'Lab 4',
  'Work Area',
  'TR1',
  'TR2',
];

export const SCHEDULE_LOCATIONS = DEFAULT_SCHEDULE_LOCATIONS;

export const DEFAULT_LAB_METADATA = {
  'Lab 1': { badge: 'Hardware', color: '#014BAA' },
  'Lab 2': { badge: 'Software', color: '#0284C7' },
  'Lab 3': { badge: 'Data & AI', color: '#7C3AED' },
  'Lab 4': { badge: 'Cloud Ops', color: '#059669' },
  'Work Area': { badge: 'Work Area', color: '#D97706' },
  'TR1': { badge: 'TR1', color: '#EC4899' },
  'TR2': { badge: 'TR2', color: '#8B5CF6' },
};

export const DEFAULT_SCHEDULE_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
export const SCHEDULE_DAYS = DEFAULT_SCHEDULE_DAYS;

export const DEFAULT_SCHEDULE_TIME_SLOTS = [
  '9:00 AM – 11:00 AM',
  '11:30 AM – 1:30 PM',
  '2:00 PM – 4:00 PM',
  '4:30 PM – 6:00 PM',
];
export const SCHEDULE_TIME_SLOTS = DEFAULT_SCHEDULE_TIME_SLOTS;

export const DEFAULT_BATCH_GROUPS = {
  A: ['a1', 'a2', 'a3', 'a4'],
  B: ['b1', 'b2', 'b3', 'b4'],
  C: ['c1', 'c2', 'c3', 'c4'],
};

// Recipient targeting modes for the Broadcast composer
export const RECIPIENT_MODES = ['All users', 'By role', 'Specific users'];
export const DEFAULT_RECIPIENT_MODE = 'All users';

// Role-based targeting uses the existing Broadcast `audience` label.
export const ROLE_OPTIONS = ['All Trainees', 'All Admins'];
export const VALID_AUDIENCES = ['All students', 'All faculty', 'All staff', 'All users', 'All campus members'];

export const SPECIFIC_RECIPIENTS_SUPPORTED = true;

export const VALIDATION_LIMITS = {
  BROADCAST_TITLE_MAX: 160,
  BROADCAST_MESSAGE_MAX: 2000,
  SCHEDULE_TITLE_MAX: 160,
  EXCEL_FILE_MAX_SIZE_BYTES: 15 * 1024 * 1024, // 15MB
};

export const REQUEST_TIMEOUT_MS = 15000;
