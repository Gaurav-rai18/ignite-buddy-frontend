import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardService } from '../services/dashboardService';
import { broadcastService } from '../services/broadcastService';
import { buddyService } from '../services/buddyService';
import { formatErrorMessage } from '../utils/error';

export function useDashboard() {
  const [summary, setSummary] = useState({
    broadcast_count: 0,
    scheduled_count: 0,
    upcoming_count: 0,
    buddy_enabled: true,
  });
  const [recentBroadcasts, setRecentBroadcasts] = useState([]);
  const [buddy, setBuddy] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isTogglingBuddy, setIsTogglingBuddy] = useState(false);

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchDashboardData = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const [sumData, bData, budData] = await Promise.all([
        dashboardService.getSummary({ signal }),
        broadcastService.getBroadcasts({ signal }),
        buddyService.getBuddySetting({ signal }),
      ]);

      if (isMountedRef.current) {
        setSummary(sumData);
        setRecentBroadcasts(bData);
        setBuddy(budData?.enabled ?? true);
      }
    } catch (err) {
      if (isMountedRef.current && err.name !== 'AbortError') {
        setError(formatErrorMessage(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboardData(controller.signal);
    return () => controller.abort();
  }, [fetchDashboardData]);

  const toggleBuddy = useCallback(async (onSuccess) => {
    if (isTogglingBuddy) return;
    setIsTogglingBuddy(true);
    setError('');

    try {
      const nextState = !buddy;
      const res = await buddyService.updateBuddySetting(nextState);
      if (isMountedRef.current) {
        setBuddy(res.enabled);
        setSummary((prev) => ({ ...prev, buddy_enabled: res.enabled }));
      }
      if (onSuccess) {
        onSuccess(res.enabled);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(formatErrorMessage(err));
      }
    } finally {
      if (isMountedRef.current) {
        setIsTogglingBuddy(false);
      }
    }
  }, [buddy, isTogglingBuddy]);

  return {
    summary,
    recentBroadcasts,
    buddy,
    loading,
    error,
    isTogglingBuddy,
    refetch: fetchDashboardData,
    toggleBuddy,
    clearError: () => setError(''),
  };
}
