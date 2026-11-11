import { apiClient, setAuthTokenGetter, setOnUnauthorized } from './apiClient';

const AUTH_STORAGE_KEY = 'ignite_buddy_auth';

// Pure in-memory session (no storage persistence).
// When the page is refreshed (F5 / reload), the in-memory state is cleared
// and the user is immediately logged out.
let inMemoryUser = null;
const authListeners = new Set();

// Immediately purge any stale tokens or session data from previous versions
try {
  localStorage.removeItem(AUTH_STORAGE_KEY);
  sessionStorage.removeItem(AUTH_STORAGE_KEY);
} catch {}

// Bind in-memory token retrieval directly into apiClient
setAuthTokenGetter(() => inMemoryUser?.access || null);

// Bind auto-invalidation on 401 Unauthorized
setOnUnauthorized(() => {
  authService.clearSession();
});

export const authService = {
  /**
   * Attempt sign in with email and password.
   * Authentication state is kept strictly in-memory during the active page session.
   * Refreshing the browser page resets inMemoryUser to null and logs the user out.
   */
  login: async ({ email, password }) => {
    const trimmedEmail = (email || '').trim();
    if (!trimmedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      throw new Error('Please enter a valid email address.');
    }
    if (!password || password.length < 4) {
      throw new Error('Email or password is incorrect.');
    }

    // Purge any storage before new session starts
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {}

    const response = await apiClient.post('/accounts/login/', {
      email: trimmedEmail,
      password,
    });

    const data = response.data;
    const userRole = (data.role || '').toUpperCase();
    const ALLOWED_ADMIN_ROLES = ['ADMIN', 'MANAGER', 'TA', 'HR'];
    if (userRole === 'TRAINEE' || !ALLOWED_ADMIN_ROLES.includes(userRole)) {
      throw new Error('Access denied. Trainees are not authorized to access the Admin Console.');
    }

    const first = (data.first_name || '').trim();
    const last = (data.last_name || '').trim();
    const compositeName = `${first} ${last}`.trim();

    const user = {
      id: data.id,
      email: data.email,
      username: data.username || '',
      first_name: first,
      last_name: last,
      full_name: data.full_name || compositeName || data.username || data.email,
      role: data.role,
      employee_id: data.employee_id || '',
      phone_number: data.phone_number || '',
      department: data.department || 'TCS Ignite Training',
      designation: data.designation || 'Administrator',
      profile_picture: data.profile_picture || '',
      accops_id: data.accops_id || '',
      sub_batch: data.sub_batch,
      full_batch_name: data.full_batch_name || 'Unassigned',
      is_active: data.is_active ?? true,
      is_staff: data.is_staff ?? true,
      is_superuser: data.is_superuser ?? false,
      date_joined: data.date_joined || null,
      last_login: data.last_login || null,
      access: data.access,
      refresh: data.refresh,
      loginTime: new Date().toISOString(),
    };

    // Kept strictly in memory during the active session.
    // Refreshing the page (F5) discards inMemoryUser, logging the user out.
    inMemoryUser = user;
    authListeners.forEach((fn) => {
      try {
        fn(inMemoryUser);
      } catch {}
    });

    return user;
  },

  /**
   * Update fields on currently logged-in user in memory
   */
  updateCurrentUser: (patch) => {
    if (!inMemoryUser) return null;
    inMemoryUser = {
      ...inMemoryUser,
      ...patch,
      full_name:
        patch.full_name ||
        `${patch.first_name || inMemoryUser.first_name || ''} ${patch.last_name || inMemoryUser.last_name || ''}`.trim() ||
        patch.username ||
        inMemoryUser.username ||
        inMemoryUser.email,
    };
    authListeners.forEach((fn) => {
      try {
        fn(inMemoryUser);
      } catch {}
    });
    return inMemoryUser;
  },

  /**
   * Fetch latest profile from backend /api/accounts/me/
   */
  fetchCurrentUser: async () => {
    if (!inMemoryUser?.access) return null;
    try {
      const res = await apiClient.get('/accounts/me/');
      if (res.data) {
        return authService.updateCurrentUser(res.data);
      }
    } catch {
      // Ignore background sync errors
    }
    return inMemoryUser;
  },

  /**
   * Log out, invalidate backend refresh token, and destroy in-memory session
   */
  logout: async () => {
    const currentUser = inMemoryUser;
    authService.clearSession();

    if (currentUser?.refresh) {
      try {
        await apiClient.post('/accounts/logout/', {
          refresh: currentUser.refresh,
        });
      } catch {
        // Silently catch server logout errors
      }
    }
  },

  /**
   * Destroy in-memory session and ensure no disk artifacts exist
   */
  clearSession: () => {
    inMemoryUser = null;
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {}
    authListeners.forEach((fn) => {
      try {
        fn(null);
      } catch {}
    });
  },

  /**
   * Get currently active in-memory user
   */
  getCurrentUser: () => inMemoryUser,

  /**
   * Get active access token from in-memory session
   */
  getAccessToken: () => inMemoryUser?.access || null,

  /**
   * Check if user is actively authenticated in this runtime session
   */
  isAuthenticated: () => Boolean(inMemoryUser && inMemoryUser.access),

  /**
   * Subscribe to in-memory auth changes
   */
  subscribe: (fn) => {
    authListeners.add(fn);
    return () => authListeners.delete(fn);
  },
};
