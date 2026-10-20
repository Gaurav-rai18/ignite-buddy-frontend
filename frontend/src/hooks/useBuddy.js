import { useState, useEffect, useCallback, useRef } from 'react';
import { buddyService } from '../services/buddyService';
import { formatErrorMessage } from '../utils/error';

export function useBuddy() {
  const [buddy, setBuddy] = useState(true);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState('');

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchBuddySetting = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const data = await buddyService.getBuddySetting({ signal });
      if (isMountedRef.current) {
        setBuddy(data?.enabled ?? true);
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
    fetchBuddySetting(controller.signal);
    return () => controller.abort();
  }, [fetchBuddySetting]);

  const toggleBuddy = useCallback(async (onSuccess) => {
    if (isUpdating) return;
    setIsUpdating(true);
    setError('');

    try {
      const nextState = !buddy;
      const res = await buddyService.updateBuddySetting(nextState);
      if (isMountedRef.current) {
        setBuddy(res.enabled);
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
        setIsUpdating(false);
      }
    }
  }, [buddy, isUpdating]);

  return {
    buddy,
    loading,
    isUpdating,
    error,
    toggleBuddy,
    refetch: fetchBuddySetting,
    clearError: () => setError(''),
  };
}
