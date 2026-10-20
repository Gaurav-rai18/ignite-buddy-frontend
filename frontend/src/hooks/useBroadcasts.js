import { useState, useEffect, useCallback, useRef } from 'react';
import { broadcastService } from '../services/broadcastService';
import { validateBroadcastForm } from '../utils/validation';
import { formatErrorMessage } from '../utils/error';

const INITIAL_FORM = {
  title: '',
  message: '',
  audience: 'All students',
};

export function useBroadcasts() {
  const [broadcasts, setBroadcasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [form, setForm] = useState(INITIAL_FORM);

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchBroadcasts = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const data = await broadcastService.getBroadcasts({ signal });
      if (isMountedRef.current) {
        setBroadcasts(data);
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
    fetchBroadcasts(controller.signal);
    return () => controller.abort();
  }, [fetchBroadcasts]);

  const updateFormField = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear field-specific error as user types
    setFormErrors((prev) => {
      if (!prev[field]) return prev;
      const updated = { ...prev };
      delete updated[field];
      return updated;
    });
  }, []);

  const submitBroadcast = useCallback(async (onSuccess) => {
    if (isSubmitting) return false;

    const validation = validateBroadcastForm(form);
    if (!validation.isValid) {
      setFormErrors(validation.errors);
      return false;
    }

    setIsSubmitting(true);
    setError('');
    setFormErrors({});

    try {
      const payload = {
        title: form.title.trim(),
        message: form.message.trim(),
        audience: form.audience.trim(),
      };
      await broadcastService.createBroadcast(payload);

      if (isMountedRef.current) {
        setForm(INITIAL_FORM);
      }

      await fetchBroadcasts();

      if (onSuccess) {
        onSuccess('Broadcast saved successfully');
      }
      return true;
    } catch (err) {
      if (isMountedRef.current) {
        setError(formatErrorMessage(err));
      }
      return false;
    } finally {
      if (isMountedRef.current) {
        setIsSubmitting(false);
      }
    }
  }, [form, isSubmitting, fetchBroadcasts]);

  return {
    broadcasts,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    submitBroadcast,
    refetch: fetchBroadcasts,
    clearError: () => setError(''),
  };
}
