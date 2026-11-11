import { useState, useEffect, useCallback, useRef } from 'react';
import { buddyService } from '../services/buddyService';
import { formatErrorMessage, isRequestCancellation } from '../utils/error';

const DEFAULT_BUDDY_SETTINGS = {
  enabled: true,
  exam_mode: false,
  ai_provider: 'gemini',
  ai_model: 'gemini-1.5-flash',
  temperature: 0.7,
  max_tokens: 1024,
  allow_voice: true,
  allow_vision: true,
  daily_question_limit: 100,
  rate_limit_rpm: 30,
  block_during_exams: true,
  restrict_to_syllabus: true,
  require_session_auth: true,
  debug_mode: false,
};

export function useBuddy() {
  const [settings, setSettings] = useState(DEFAULT_BUDDY_SETTINGS);
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
      const validSignal =
        signal && typeof signal.addEventListener === 'function' ? signal : undefined;
      const data = await buddyService.getBuddySetting(
        validSignal ? { signal: validSignal } : {}
      );
      if (isMountedRef.current && data) {
        setSettings({
          ...DEFAULT_BUDDY_SETTINGS,
          ...data,
          enabled: Boolean(data.enabled),
          exam_mode: Boolean(data.exam_mode),
        });
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
    fetchBuddySetting(controller.signal);
    return () => controller.abort();
  }, [fetchBuddySetting]);

  const toggleBuddy = useCallback(async (onSuccess) => {
    if (isUpdating) return;
    setIsUpdating(true);
    setError('');

    try {
      const nextState = !Boolean(settings.enabled);
      const res = await buddyService.updateBuddySetting({ enabled: nextState });
      const updated = Boolean(res?.enabled);
      if (isMountedRef.current) {
        setSettings((prev) => ({ ...prev, enabled: updated }));
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
        setIsUpdating(false);
      }
    }
  }, [settings.enabled, isUpdating]);

  const updateSetting = useCallback(async (key, value, onSuccess) => {
    if (isUpdating) return;
    setIsUpdating(true);
    setError('');

    try {
      const payload = { [key]: value };
      const res = await buddyService.updateBuddySetting(payload);
      if (isMountedRef.current && res) {
        setSettings((prev) => ({
          ...prev,
          ...res,
          enabled: Boolean(res.enabled),
          exam_mode: Boolean(res.exam_mode),
        }));
        if (onSuccess) {
          onSuccess(res);
        }
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
  }, [isUpdating]);

  const saveBatchSettings = useCallback(async (newSettings, onSuccess) => {
    if (isUpdating) return;
    setIsUpdating(true);
    setError('');

    try {
      const res = await buddyService.updateBuddySetting(newSettings);
      if (isMountedRef.current && res) {
        setSettings((prev) => ({
          ...prev,
          ...res,
          enabled: Boolean(res.enabled),
          exam_mode: Boolean(res.exam_mode),
        }));
        if (onSuccess) {
          onSuccess(res);
        }
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
  }, [isUpdating]);

  return {
    buddy: Boolean(settings.enabled),
    settings,
    loading,
    isUpdating,
    error,
    toggleBuddy,
    updateSetting,
    saveBatchSettings,
    refetch: () => fetchBuddySetting(),
    clearError: () => setError(''),
  };
}
