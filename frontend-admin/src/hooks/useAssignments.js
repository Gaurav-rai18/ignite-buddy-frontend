import { useState, useEffect, useCallback, useRef } from 'react';
import { assignmentService } from '../services/assignmentService';
import { isRequestCancellation, formatErrorMessage } from '../utils/error';
import { RECIPIENT_MODES, DEFAULT_RECIPIENT_MODE } from '../constants';

const INITIAL_FORM = {
  topic: '',
  subject: '',
  platform_link: '',
  start_date: '',
  deadline: '',
  deadline_time: '23:59',
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

function buildDeadlineAt(dateStr, timeStr) {
  if (!dateStr) return null;
  const time = (timeStr || '23:59').slice(0, 5);
  const dt = new Date(`${dateStr}T${time}:00`);
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toISOString();
}

function validateAssignmentForm(form) {
  const errors = {};
  if (!form.topic.trim()) errors.topic = 'Topic is required.';
  if (!form.subject.trim()) errors.subject = 'Subject is required.';
  if (!form.start_date) errors.start_date = 'Start date is required.';
  if (!form.deadline) errors.deadline = 'Deadline is required.';
  if (form.start_date && form.deadline && form.deadline <= form.start_date) {
    errors.deadline = 'Deadline must be after the start date.';
  }
  if (!form.message.trim()) errors.message = 'Assignment message / instructions are required.';
  const mode = form.recipientMode || DEFAULT_RECIPIENT_MODE;
  if (!RECIPIENT_MODES.includes(mode)) {
    errors.recipients = 'Invalid recipient type.';
  } else if (mode === 'By role' && !form.role) {
    errors.recipients = 'Please select a role to send to.';
  } else if (mode === 'Specific users' && (!Array.isArray(form.selectedUsers) || form.selectedUsers.length === 0)) {
    errors.recipients = 'Select at least one recipient.';
  }
  return { isValid: Object.keys(errors).length === 0, errors };
}

export function useAssignments() {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [form, setForm] = useState(INITIAL_FORM);
  const [historyFilter, setHistoryFilter] = useState('mine'); // 'mine' | 'others'
  const [deadlineUpdating, setDeadlineUpdating] = useState({});
  const [publishingId, setPublishingId] = useState(null);
  const [submissionsAssignmentId, setSubmissionsAssignmentId] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [evaluationSaving, setEvaluationSaving] = useState({});
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  const fetchAssignments = useCallback(async (signal) => {
    setLoading(true);
    setError('');
    try {
      const data = await assignmentService.getAssignments({}, { signal });
      if (isMountedRef.current) setAssignments(data);
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
    } finally {
      if (isMountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchAssignments(controller.signal);
    return () => controller.abort();
  }, [fetchAssignments]);

  const updateFormField = useCallback((field, value) => {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (field === 'recipientMode') {
        if (value === 'By role') {
          next.audience = prev.role || '';
        } else if (value === 'Specific users') {
          next.audience = `Selected users (${(prev.selectedUsers || []).length})`;
        } else {
          next.audience = 'All students';
        }
        if (value !== 'By role') next.role = '';
      }
      if (field === 'role') next.audience = value;
      return next;
    });
    setFormErrors((prev) => {
      const updated = { ...prev };
      delete updated[field];
      delete updated.recipients;
      return updated;
    });
  }, []);

  const toggleRecipient = useCallback((user) => {
    setForm((prev) => {
      const list = prev.selectedUsers || [];
      const exists = list.some((u) => u.username === user.username);
      const selectedUsers = exists
        ? list.filter((u) => u.username !== user.username)
        : [...list, user];
      return {
        ...prev,
        selectedUsers,
        audience: prev.recipientMode === 'Specific users'
          ? `Selected users (${selectedUsers.length})`
          : prev.audience,
      };
    });
    setFormErrors((prev) => {
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
        audience: prev.recipientMode === 'Specific users'
          ? `Selected users (${selectedUsers.length})`
          : prev.audience,
      };
    });
    setFormErrors((prev) => {
      const updated = { ...prev };
      delete updated.recipients;
      return updated;
    });
  }, []);

  const submitAssignment = useCallback(async (onSuccess, options = {}) => {
    if (isSubmitting) return false;
    const publish = options.publish !== false;
    const validation = validateAssignmentForm(form);
    if (!validation.isValid) {
      setFormErrors(validation.errors);
      return false;
    }
    setIsSubmitting(true);
    setError('');
    setFormErrors({});
    try {
      let payload = {
        topic: form.topic.trim(),
        subject: form.subject.trim(),
        platform_link: form.platform_link.trim() || null,
        start_date: form.start_date,
        deadline: form.deadline,
        deadline_at: buildDeadlineAt(form.deadline, form.deadline_time),
        message: form.message.trim(),
        is_published: publish,
      };
      const mode = form.recipientMode || DEFAULT_RECIPIENT_MODE;
      if (mode === 'All users') {
        payload.recipient_type = 'ALL';
      } else if (mode === 'By role') {
        payload.recipient_type = 'ROLE';
        payload.target_role = form.role;
      } else if (mode === 'By cohort') {
        payload.recipient_type = 'COHORT';
        payload.cohort_id = parseInt(form.cohort_id, 10);
      } else if (mode === 'By batch') {
        payload.recipient_type = 'BATCH';
        const bIds = form.selectedBatchIds.length > 0
          ? form.selectedBatchIds.map((id) => parseInt(id, 10))
          : (form.batch_id ? [parseInt(form.batch_id, 10)] : []);
        payload.batch_ids = bIds;
        payload.batch_id = bIds[0] || null;
      } else if (mode === 'By sub-batch') {
        payload.recipient_type = 'SUB_BATCH';
        const sbIds = form.selectedSubBatchIds.length > 0
          ? form.selectedSubBatchIds.map((id) => parseInt(id, 10))
          : (form.sub_batch_id ? [parseInt(form.sub_batch_id, 10)] : []);
        payload.sub_batch_ids = sbIds;
        payload.sub_batch_id = sbIds[0] || null;
      } else if (mode === 'Specific users') {
        payload.recipient_type = 'USERS';
        payload.target_usernames = form.selectedUsers.map((u) => u.username);
      }
      await assignmentService.createAssignment(payload);
      if (isMountedRef.current) setForm(INITIAL_FORM);
      await fetchAssignments();
      if (onSuccess) {
        onSuccess(publish ? 'Assignment published successfully' : 'Draft saved successfully');
      }
      return true;
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
      return false;
    } finally {
      if (isMountedRef.current) setIsSubmitting(false);
    }
  }, [form, isSubmitting, fetchAssignments]);

  const publishAssignment = useCallback(async (id, onSuccess) => {
    setPublishingId(id);
    setError('');
    try {
      await assignmentService.publishAssignment(id);
      setAssignments((prev) =>
        prev.map((a) => (String(a.id) === String(id) ? { ...a, is_published: true } : a))
      );
      if (onSuccess) onSuccess('Assignment published and students notified');
      return true;
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
      return false;
    } finally {
      setPublishingId(null);
    }
  }, []);

  const openSubmissions = useCallback(async (id) => {
    setSubmissionsAssignmentId(id);
    setSubmissions([]);
    setSubmissionsLoading(true);
    setError('');
    try {
      const data = await assignmentService.getSubmissions(id);
      if (isMountedRef.current) setSubmissions(Array.isArray(data) ? data : []);
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
    } finally {
      if (isMountedRef.current) setSubmissionsLoading(false);
    }
  }, []);

  const closeSubmissions = useCallback(() => {
    setSubmissionsAssignmentId(null);
    setSubmissions([]);
  }, []);

  const evaluateSubmission = useCallback(async (recipientId, evaluationData, onSuccess) => {
    if (!submissionsAssignmentId) return false;
    setEvaluationSaving((prev) => ({ ...prev, [recipientId]: true }));
    setError('');
    try {
      const updated = await assignmentService.evaluateSubmission(
        submissionsAssignmentId,
        recipientId,
        evaluationData,
      );
      setSubmissions((prev) =>
        prev.map((s) => (String(s.id) === String(recipientId) ? { ...s, ...updated } : s))
      );
      if (onSuccess) onSuccess('Evaluation saved and student notified');
      return true;
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
      return false;
    } finally {
      setEvaluationSaving((prev) => ({ ...prev, [recipientId]: false }));
    }
  }, [submissionsAssignmentId]);

  const updateDeadline = useCallback(async (id, deadline, onSuccess) => {
    setDeadlineUpdating((prev) => ({ ...prev, [id]: true }));
    try {
      await assignmentService.updateAssignmentDeadline(id, deadline);
      setAssignments((prev) =>
        prev.map((a) => (String(a.id) === String(id) ? { ...a, deadline } : a))
      );
      if (onSuccess) onSuccess('Deadline updated successfully');
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
    } finally {
      setDeadlineUpdating((prev) => ({ ...prev, [id]: false }));
    }
  }, []);

  return {
    assignments,
    loading,
    isSubmitting,
    error,
    formErrors,
    form,
    historyFilter,
    deadlineUpdating,
    publishingId,
    submissionsAssignmentId,
    submissions,
    submissionsLoading,
    evaluationSaving,
    setHistoryFilter,
    updateFormField,
    toggleRecipient,
    setRecipients,
    submitAssignment,
    publishAssignment,
    updateDeadline,
    openSubmissions,
    closeSubmissions,
    evaluateSubmission,
    refetch: fetchAssignments,
    clearError: () => setError(''),
  };
}
