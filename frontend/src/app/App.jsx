/**
 * @file App.jsx
 * @description Root application component with routing configuration.
 *
 * Structure:
 *   App → AuthProvider → AppRoutes
 *
 * Route layout:
 *   /login       — Public-only login page (redirects to /dashboard if already authenticated).
 *   /            — Protected routes wrapped in AppLayout (sidebar + topbar):
 *     /dashboard   — Dashboard with stats and quick actions.
 *     /broadcast   — Compose and view broadcast announcements.
 *     /schedule    — Create, upload, and manage timetable schedules.
 *     /buddy       — Toggle the Ignite Buddy AI assistant.
 *     /users       — Manage campus users (CRUD).
 *     /documents   — Upload knowledge-base documents for RAG.
 *     *            — 404 Not Found fallback.
 *
 * Also manages:
 *   - Toast notification state (passed as onNotify to child pages).
 *   - Broadcast count for the sidebar badge.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '../hooks/useAuth';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import { AppLayout } from '../components/layout/AppLayout';
import { Login } from '../pages/Login/Login';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { Broadcast } from '../pages/Broadcast/Broadcast';
import { Schedule } from '../pages/Schedule/Schedule';
import { BuddyControl } from '../pages/BuddyControl/BuddyControl';
import { ManageUsers } from '../pages/ManageUsers/ManageUsers';
import { AddDocuments } from '../pages/AddDocuments/AddDocuments';
import { NotFound } from '../pages/NotFound/NotFound';
import { broadcastService } from '../services/broadcastService';

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

function AppRoutes() {
  const [toastMessage, setToastMessage] = useState('');
  const [broadcastCount, setBroadcastCount] = useState(0);

  const notify = useCallback((message) => {
    setToastMessage(message);
    const timer = window.setTimeout(() => {
      setToastMessage('');
    }, 2800);
    return () => window.clearTimeout(timer);
  }, []);

  // Fetch initial broadcast count for the sidebar badge
  useEffect(() => {
    let isMounted = true;
    broadcastService
      .getBroadcasts()
      .then((data) => {
        if (isMounted && Array.isArray(data)) {
          setBroadcastCount(data.length);
        }
      })
      .catch(() => {
        // Silently catch badge count fetch error so UI continues normally
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleUpdateBroadcastCount = useCallback((count) => {
    setBroadcastCount(count);
  }, []);

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login onNotify={notify} />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout
              broadcastCount={broadcastCount}
              toastMessage={toastMessage}
              onNotify={notify}
            />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard onNotify={notify} />} />
        <Route
          path="broadcast"
          element={
            <Broadcast
              onNotify={notify}
              onUpdateBroadcastCount={handleUpdateBroadcastCount}
            />
          }
        />
        <Route path="schedule" element={<Schedule onNotify={notify} />} />
        <Route path="buddy" element={<BuddyControl onNotify={notify} />} />
        <Route path="users" element={<ManageUsers onNotify={notify} />} />
        <Route path="documents" element={<AddDocuments onNotify={notify} />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
