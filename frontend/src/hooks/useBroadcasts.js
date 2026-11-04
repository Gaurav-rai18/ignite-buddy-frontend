/**
 * @file useBroadcasts.js
 * @description Custom hook for broadcast management state and operations.
 *
 * Manages the full lifecycle of broadcasts: fetching the list, form state
 * for composing new announcements, recipient targeting (all users / by role /
 * specific users), validation, submission, and error handling.
 *
 * Uses AbortController for cleanup on unmount and isMountedRef to prevent
 * state updates on unmounted components.
 *
 * Data flow:
 *   Broadcast page → useBroadcasts() → broadcastService → apiClient → Django API
 *
 * @exports {Function} useBroadcasts - Hook returning broadcasts, form state, and actions.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { broadcastService } from '../services/broadcastService';
import { validateBroadcastForm } from '../utils/validation';
import { formatErrorMessage } from '../utils/error';
import { SPECIFIC_RECIPIENTS_SUPPORTED } from '../constants';

const INITIAL_FORM = {
  title: '',
  message: '',
  recipientMode: 'All users',
  role: '',
  selectedUsers: [],
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
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      // Keep the backend `audience` label in sync with the chosen targeting.
      if (field === 'recipientMode') {
        if (value === 'By role') {
          next.audience = prev.role || '';
        } else if (value === 'Specific users') {
          next.audience = `Selected users (${(prev.selectedUsers || []).length})`;
        } else {
          next.audience = 'All students';
        }
        if (value !== 'By role') {
          next.role = '';
        }
      }
      if (field === 'role') {
        next.audience = value;
      }
      return next;
    });
    // Clear field-specific error as user types
    setFormErrors((prev) => {
      if (!prev[field] && !prev.recipients && !prev.audience) return prev;
      const updated = { ...prev };
      delete updated[field];
      delete updated.recipients;
      if (field === 'recipientMode' || field === 'role') {
        delete updated.audience;
      }
      return updated;
    });
  }, []);

  const toggleRecipient = useCallback((user) => {
    setForm((prev) => {
      const list = prev.selectedUsers || [];
      const exists = list.some((u) => u.id === user.id);
      const selectedUsers = exists ? list.filter((u) => u.id !== user.id) : [...list, user];
      return {
        ...prev,
        selectedUsers,
        audience:
          prev.recipientMode === 'Specific users'
            ? `Selected users (${selectedUsers.length})`
            : prev.audience,
      };
    });
    setFormErrors((prev) => {
      if (!prev.recipients) return prev;
      const updated = { ...prev };
      delete updated.recipients;
      return updated;
    });
  }, []);

  const setRecipients = useCallback((users) => {
    setForm((prev) => {
      const selectedUsers = Array.isArray(users) ? users : [];
      return {
        ...prev,
        selectedUsers,
        audience:
          prev.recipientMode === 'Specific users'
            ? `Selected users (${selectedUsers.length})`
            : prev.audience,
      };
    });
    setFormErrors((prev) => {
      if (!prev.recipients) return prev;
      const updated = { ...prev };
      delete updated.recipients;
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

    if (form.recipientMode === 'Specific users' && !SPECIFIC_RECIPIENTS_SUPPORTED) {
      setError(
        'Sending to specific users is not available yet. The backend Broadcast API cannot store recipients, so this cannot be delivered. Please use "All users" or "By role".'
      );
      return false;
    }

    setIsSubmitting(true);
    setError('');
    setFormErrors({});

    try {
      const payload = {
        title: form.title.trim(),
        message: form.message.trim(),
        audience: form.recipientMode === 'By role' ? form.role : 'All students',
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
    toggleRecipient,
    setRecipients,
    submitBroadcast,
    refetch: fetchBroadcasts,
    clearError: () => setError(''),
  };
}
