import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);
const IDLE_TIMEOUT_MS = 15 * 60 * 1000; // 15-minute Zero Trust inactivity timeout

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authService.getCurrentUser());
  const [loading, setLoading] = useState(false);
  const [sessionTimeoutNotice, setSessionTimeoutNotice] = useState(false);

  // Synchronize state with in-memory authService changes
  useEffect(() => {
    const unsubscribe = authService.subscribe((updatedUser) => {
      setUser(updatedUser);
      if (!updatedUser) {
        setLoading(false);
      }
    });
    return unsubscribe;
  }, []);

  // Zero Trust Inactivity Monitor: auto-lock after 15 minutes of inactivity
  useEffect(() => {
    if (!user) return;

    let timeoutId;

    const resetTimer = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        // Session idle timeout reached: log out and require credentials
        authService.logout();
        setSessionTimeoutNotice(true);
      }, IDLE_TIMEOUT_MS);
    };

    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];
    activityEvents.forEach((evt) => window.addEventListener(evt, resetTimer, { passive: true }));
    resetTimer();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      activityEvents.forEach((evt) => window.removeEventListener(evt, resetTimer));
    };
  }, [user]);

  const login = useCallback(async ({ email, password }) => {
    setSessionTimeoutNotice(false);
    const loggedInUser = await authService.login({ email, password });
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const clearNotice = useCallback(() => {
    setSessionTimeoutNotice(false);
  }, []);

  const value = {
    user,
    isAuthenticated: Boolean(user && user.access),
    loading,
    sessionTimeoutNotice,
    clearNotice,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
