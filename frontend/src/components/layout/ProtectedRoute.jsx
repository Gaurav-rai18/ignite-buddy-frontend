/**
 * @file ProtectedRoute.jsx
 * @description Authentication guard that wraps protected routes.
 *
 * Behaviour:
 *  1. While `useAuth()` is still loading (e.g. verifying a stored token), a
 *     centered spinner is shown so the user never sees a flash of the login page.
 *  2. If the user is NOT authenticated, they are redirected to `/login` using
 *     React Router's `<Navigate>`. The current location is passed via `state.from`
 *     so the login page can redirect back after a successful sign-in.
 *  3. If authenticated, the child components are rendered normally.
 *
 * Usage:
 *   <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>} />
 *
 * @exports ProtectedRoute
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

/**
 * Route-level auth wrapper.
 * @param {Object} props
 * @param {React.ReactNode} props.children - The route elements to protect.
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  /* Show a loading spinner while auth state is being determined */
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="btn-spinner" style={{ width: '28px', height: '28px', borderColor: 'var(--color-primary)' }} />
      </div>
    );
  }

  /* Redirect unauthenticated users to login, preserving the intended destination */
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
