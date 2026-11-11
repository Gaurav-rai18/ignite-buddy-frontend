import { useState, useEffect, useCallback, useRef } from 'react';
import { broadcastService } from '../services/broadcastService';
import { validateBroadcastForm } from '../utils/validation';
import { formatErrorMessage, isRequestCancellation } from '../utils/error';
import { SPECIFIC_RECIPIENTS_SUPPORTED } from '../constants';

const INITIAL_FORM = {
  title: '',
  message: '',
  recipientMode: 'All users',
  role: '',
  cohort_id: '',
  batch_id: '',
  sub_batch_id: '',
  selectedBatchIds: [],
  selectedSubBatchIds: [],
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
      const validSignal =
        signal && typeof signal.addEventListener === 'function' ? signal : undefined;
      const data = await broadcastService.getBroadcasts(
        validSignal ? { signal: validSignal } : {}
      );
      if (isMountedRef.current) {
        setBroadcasts(data);
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
      const exists = list.some((u) => u.username === user.username);
      const selectedUsers = exists ? list.filter((u) => u.username !== user.username) : [...list, user];
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

    if (
      form.recipientMode === 'Specific users' &&
      !SPECIFIC_RECIPIENTS_SUPPORTED
    ) {
      setError(
        'Sending to specific users is not available yet.'
      );
      return false;
    }

    setIsSubmitting(true);
    setError('');
    setFormErrors({});

    try {
      let payload = {
        title: form.title.trim(),
        message: form.message.trim(),
      };

      if (form.recipientMode === 'All users') {
        payload.recipient_type = 'ALL';
      } else if (form.recipientMode === 'By role') {
        payload.recipient_type = 'ROLE';
        payload.target_role = form.role;
      } else if (form.recipientMode === 'By cohort') {
        payload.recipient_type = 'COHORT';
        payload.cohort_id = parseInt(form.cohort_id, 10);
      } else if (form.recipientMode === 'By batch') {
        payload.recipient_type = 'BATCH';
        const bIds = (form.selectedBatchIds && form.selectedBatchIds.length > 0)
          ? form.selectedBatchIds.map((id) => parseInt(id, 10))
          : (form.batch_id ? [parseInt(form.batch_id, 10)] : []);
        payload.batch_ids = bIds;
        payload.batch_id = bIds[0] || null;
      } else if (form.recipientMode === 'By sub-batch') {
        payload.recipient_type = 'SUB_BATCH';
        const sbIds = (form.selectedSubBatchIds && form.selectedSubBatchIds.length > 0)
          ? form.selectedSubBatchIds.map((id) => parseInt(id, 10))
          : (form.sub_batch_id ? [parseInt(form.sub_batch_id, 10)] : []);
        payload.sub_batch_ids = sbIds;
        payload.sub_batch_id = sbIds[0] || null;
      } else if (form.recipientMode === 'Specific users') {
        payload.recipient_type = 'USERS';
        payload.target_usernames = form.selectedUsers.map((user) => user.username);
      }

      console.log(
        'recipientMode =',
        form.recipientMode
      );

      console.log(
        'payload =',
        payload
      );

      await broadcastService.createBroadcast(
        payload
      );

      if (isMountedRef.current) {
        setForm(INITIAL_FORM);
      }

      await fetchBroadcasts();

      if (onSuccess) {
        onSuccess(
          'Broadcast saved successfully'
        );
      }

      return true;

    } catch (err) {

      if (isMountedRef.current) {
        setError(
          formatErrorMessage(err)
        );
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
    refetch: () => fetchBroadcasts(),
    clearError: () => setError(''),
  };
}
