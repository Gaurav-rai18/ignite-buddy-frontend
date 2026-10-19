import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { Broadcast } from '../pages/Broadcast/Broadcast';
import { Schedule } from '../pages/Schedule/Schedule';
import { BuddyControl } from '../pages/BuddyControl/BuddyControl';
import { NotFound } from '../pages/NotFound/NotFound';
import { broadcastService } from '../services/broadcastService';

export function App() {
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
        path="/"
        element={
          <AppLayout
            broadcastCount={broadcastCount}
            toastMessage={toastMessage}
            onNotify={notify}
          />
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
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
