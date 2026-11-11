import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardService } from '../services/dashboardService';
import { broadcastService } from '../services/broadcastService';
import { buddyService } from '../services/buddyService';
import { formatErrorMessage, isRequestCancellation } from '../utils/error';

export function useDashboard() {
  const [summary, setSummary] = useState(null);
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
      const validSignal =
        signal && typeof signal.addEventListener === 'function' ? signal : undefined;
      const options = validSignal ? { signal: validSignal } : {};
      const [sumData, bData, budData] = await Promise.all([
        dashboardService.getSummary(options),
        broadcastService.getBroadcasts(options),
        buddyService.getBuddySetting(options),
      ]);

      if (isMountedRef.current) {
        setSummary(sumData);
        setRecentBroadcasts(bData);
        setBuddy(Boolean(budData?.enabled));
      }
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
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
      const nextState = !Boolean(buddy);
      const res = await buddyService.updateBuddySetting(nextState);
      const updated = Boolean(res?.enabled);
      if (isMountedRef.current) {
        setBuddy(updated);
        if (onSuccess) {
          onSuccess(updated);
        }
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
    refetch: () => fetchDashboardData(),
    toggleBuddy,
    clearError: () => setError(''),
  };
}
