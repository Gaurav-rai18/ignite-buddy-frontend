/**
 * @file useAuth.jsx
 * @description Authentication context provider and hook for the Ignite Buddy app.
 *
 * Uses React Context to share auth state (user object, login/logout functions)
 * across the entire component tree. The AuthProvider wraps the app in App.jsx
 * and reads persisted credentials from authService on mount.
 *
 * Data flow:
 *   Login page → useAuth().login() → authService.login() → Django /api/login/
 *   Any component → useAuth() → { user, isAuthenticated, login, logout }
 *
 * @exports {Function} AuthProvider - Context provider component.
 * @exports {Function} useAuth      - Hook to consume auth context.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authService.getCurrentUser());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial verification
    const active = authService.getCurrentUser();
    setUser(active);
    setLoading(false);
  }, []);

  const login = useCallback(async ({ email, password, rememberMe }) => {
    const loggedInUser = await authService.login({ email, password, rememberMe });
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const value = {
    user,
    isAuthenticated: Boolean(user && user.token),
    loading,
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
