export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';



// Recipient targeting modes for the Broadcast composer
export const RECIPIENT_MODES = ['All users', 'By role', 'By cohort', 'By batch', 'By sub-batch', 'Specific users'];

export const DEFAULT_RECIPIENT_MODE = 'All users';

// Role-based targeting uses the existing Broadcast `audience` label.
export const ROLE_OPTIONS = ['TRAINEE','TA','HR','MANAGER','ADMIN'];

// The backend Broadcast model only stores a single `audience` label (max 40
// chars) and exposes no recipient relation, so delivering to specific users
// cannot be persisted yet. Set this to true once the backend adds a
// recipients field (e.g. Broadcast.recipients / BroadcastRecipient).
export const SPECIFIC_RECIPIENTS_SUPPORTED = true;

export const VALIDATION_LIMITS = {
  BROADCAST_TITLE_MAX: 160,
  BROADCAST_MESSAGE_MAX: 2000,
  SCHEDULE_TITLE_MAX: 160,
};

export const REQUEST_TIMEOUT_MS = 15000;
