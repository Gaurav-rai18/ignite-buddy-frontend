import { useState, useEffect, useCallback, useRef } from 'react';
import { scheduleService } from '../services/scheduleService';
import { validateScheduleForm } from '../utils/validation';
import { formatErrorMessage, isRequestCancellation } from '../utils/error';

const INITIAL_FORM = {
  title: '',
  cohort_id: '',
  batch_id: '',
  sub_batch_id: '',
  schedule_type: 'WEEKLY',
  file: null,
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

  const fetchSchedules = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const validSignal =
        signal && typeof signal.addEventListener === 'function' ? signal : undefined;
      const data = await scheduleService.getSchedules(
        {},
        validSignal ? { signal: validSignal } : {}
      );
      if (isMountedRef.current) {
        setSchedules(data);
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
    fetchSchedules(controller.signal);
    return () => controller.abort();
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
    if (isSubmitting) return;

    const validation = validateScheduleForm(form);
    if (!validation.isValid) {
      setFormErrors(validation.errors);
      return;
    }

    setIsSubmitting(true);
    setError('');
    setFormErrors({});

    try {
      const formData = new FormData();
      formData.append('title', form.title.trim());
      formData.append('cohort_id', form.cohort_id);
      formData.append('batch_id', form.batch_id);
      if (form.sub_batch_id) {
        formData.append('sub_batch_id', form.sub_batch_id);
      }
      formData.append('schedule_type', form.schedule_type);
      if (form.file) {
        formData.append('file', form.file);
      }

      await scheduleService.createSchedule(formData);

      if (isMountedRef.current) {
        setForm(INITIAL_FORM);
      }

      await fetchSchedules();

      if (onSuccess) {
        onSuccess('Schedule published successfully');
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(formatErrorMessage(err));
      }
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
    refetch: () => fetchSchedules(),
    clearError: () => setError(''),
  };
}
