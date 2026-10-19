import { useState, useEffect, useCallback, useRef } from 'react';
import { scheduleService } from '../services/scheduleService';
import { validateScheduleForm } from '../utils/validation';
import { toIsoUtcString } from '../utils/date';
import { formatErrorMessage } from '../utils/error';

const INITIAL_FORM = {
  title: '',
  onedrive_url: '',
  publish_date: '',
  publish_time: '',
};

export function useSchedules() {
  const [schedules, setSchedules] = useState([]);
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

  const fetchSchedules = useCallback(async () => {
    const controller = new AbortController();
    setLoading(true);
    setError('');

    try {
      const data = await scheduleService.getSchedules({ signal: controller.signal });
      if (isMountedRef.current) {
        setSchedules(data);
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

    return () => controller.abort();
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const updateFormField = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFormErrors((prev) => {
      if (!prev[field]) return prev;
      const updated = { ...prev };
      delete updated[field];
      return updated;
    });
  }, []);

  const resetForm = useCallback(() => {
    setForm(INITIAL_FORM);
    setFormErrors({});
  }, []);

  const submitSchedule = useCallback(async (onSuccess) => {
    if (isSubmitting) return false;

    const validation = validateScheduleForm(form);
    if (!validation.isValid) {
      setFormErrors(validation.errors);
      return false;
    }

    const combinedDateTime = `${form.publish_date}T${form.publish_time}`;
    const isoDate = toIsoUtcString(combinedDateTime);
    if (!isoDate) {
      setFormErrors({ publish_date: 'Invalid date or time provided.' });
      return false;
    }

    setIsSubmitting(true);
    setError('');
    setFormErrors({});

    try {
      const payload = {
        title: form.title.trim(),
        onedrive_url: form.onedrive_url.trim(),
        publish_at: isoDate,
      };

      await scheduleService.createSchedule(payload);

      if (isMountedRef.current) {
        setForm(INITIAL_FORM);
      }

      await fetchSchedules();

      if (onSuccess) {
        onSuccess('Schedule saved successfully');
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
  }, [form, isSubmitting, fetchSchedules]);

  return {
    schedules,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    resetForm,
    submitSchedule,
    refetch: fetchSchedules,
    clearError: () => setError(''),
  };
}
