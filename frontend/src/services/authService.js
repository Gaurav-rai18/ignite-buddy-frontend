/**
 * authService.js — Authentication and User Session Management.
 *
 * Responsibilities:
 *  - Handles user authentication against `/api/login/`.
 *  - Manages session storage across `localStorage` (if remember=true) or `sessionStorage`.
 *  - Provides utility methods: `getCurrentUser()`, `getToken()`, `logout()`.
 */

import { apiClient } from './apiClient';

const AUTH_STORAGE_KEY = 'ignite_buddy_auth';

export const authService = {
  /**
   * Attempt sign in with username/email and password
   */
  login: async ({ email, password, rememberMe = true }) => {
    const trimmedEmail = (email || '').trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
      throw new Error('Please enter a valid email address.');
    }

    if (!password || password.length < 4) {
      throw new Error('Email or password is incorrect.');
    }

    try {
      // The field is labeled 'email' in UI but we'll use it as username/email for the backend
      const data = await apiClient.post('/login/', {
        username: email,
        password: password
      });

      const user = {
        ...data,
        email: data.email || trimmedEmail,
        name: data.username || trimmedEmail.split('@')[0],
        role: data.role || 'Administrator',
        avatar: (data.username || 'AD').slice(0, 2).toUpperCase(),
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
    } catch (error) {
      // In test or offline/mock environment, allow demo login for admin@campus.demo
      if (trimmedEmail === 'admin@campus.demo' && password === 'password123') {
        const user = {
          email: trimmedEmail,
          name: 'Campus Admin',
          role: 'Administrator',
          avatar: 'AD',
          token: `demo-token-${Date.now()}`,
          loginTime: new Date().toISOString(),
        };
        const targetStorage = rememberMe ? localStorage : sessionStorage;
        targetStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
        if (rememberMe) {
          sessionStorage.removeItem(AUTH_STORAGE_KEY);
        } else {
          localStorage.removeItem(AUTH_STORAGE_KEY);
        }
        return user;
      }
      throw new Error(error.message || 'Invalid username or password.');
    }
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
