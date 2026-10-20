const AUTH_STORAGE_KEY = 'ignite_buddy_auth';

export const authService = {
  /**
   * Attempt sign in with email and password
   */
  login: async ({ email, password, rememberMe = true }) => {
    // Simulate brief network delay
    await new Promise((resolve) => setTimeout(resolve, 550));

    const trimmedEmail = (email || '').trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
      throw new Error('Please enter a valid email address.');
    }

    if (!password || password.length < 4) {
      throw new Error('Email or password is incorrect.');
    }

    const user = {
      email: trimmedEmail,
      name: trimmedEmail.split('@')[0].replace(/[^a-zA-Z]/g, ' ') || 'Admin',
      role: 'Administrator',
      avatar: 'AD',
      token: `demo-token-${Date.now()}`,
      loginTime: new Date().toISOString(),
    };

    const targetStorage = rememberMe ? localStorage : sessionStorage;
    targetStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));

    // Clear opposite storage
    if (rememberMe) {
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
    } else {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }

    return user;
  },

  /**
   * Log out and clear stored session
   */
  logout: () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
  },

  /**
   * Get currently active session user if any
   */
  getCurrentUser: () => {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY) || sessionStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return null;
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated: () => {
    const user = authService.getCurrentUser();
    return Boolean(user && user.token);
  },
};
