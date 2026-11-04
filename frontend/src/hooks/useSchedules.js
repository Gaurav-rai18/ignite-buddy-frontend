/**
 * useSchedules.js — Central State Management Hook for the Schedule Feature.
 *
 * Responsibilities:
 *  1. Initial data fetching:
 *     - Fetches complete schedule configuration (locations, batches, time slots, weekdays)
 *       via `scheduleService.getConfig()` on mount.
 *     - Falls back to `FALLBACK_CONFIG` if backend is unreachable (offline resiliency).
 *     - Fetches saved schedule records via `scheduleService.getSchedules()`.
 *  2. Form State Management:
 *     - Manages active tab ('grid' vs 'excel' vs 'link'), title, publish date/time.
 *     - Tracks timetable grid data in `content_data.grid` (single-day) or `content_data.days_data` (multi-day Excel).
 *  3. Dynamic Configuration Mutations:
 *     - `addBatch`, `removeBatch`, `addSubBatch`, `removeSubBatch` (calls API + updates local config state).
 *     - `addTimeSlot`, `editTimeSlot`, `removeTimeSlot` (calls API + updates local config state).
 *  4. Excel Parsing & Upload:
 *     - Coordinates `parseExcelFile()`, updating form state with structured preview data.
 *  5. Publishing / Submission:
 *     - Validates form with `validateScheduleForm()`.
 *     - Packages payload as JSON (native grid) or FormData (Excel upload).
 *     - Converts local date/time into ISO 8601 UTC string (`publish_at`).
 *     - Refetches schedule list on success.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { scheduleService } from '../services/scheduleService';
import { validateScheduleForm } from '../utils/validation';
import { toIsoUtcString } from '../utils/date';
import { formatErrorMessage } from '../utils/error';
import {
  DEFAULT_SCHEDULE_LOCATIONS,
  DEFAULT_LAB_METADATA,
  DEFAULT_SCHEDULE_DAYS,
  DEFAULT_SCHEDULE_TIME_SLOTS,
  DEFAULT_BATCH_GROUPS,
} from '../constants';

const INITIAL_FORM = {
  title: '',
  onedrive_url: '',
  schedule_type: 'grid', // 'grid' | 'excel' | 'link'
  excel_file: null,
  excel_file_name: '',
  excel_file_size: null,
  publish_date: '',
  publish_time: '',
  content_data: { day: 'Monday', grid: {} },
};

// Fallback initial config built from defaults
const FALLBACK_CONFIG = {
  locations: DEFAULT_SCHEDULE_LOCATIONS.map((name, i) => ({
    id: i + 1,
    name,
    badge: DEFAULT_LAB_METADATA[name]?.badge || '',
    color: DEFAULT_LAB_METADATA[name]?.color || '#014BAA',
    order: i + 1,
  })),
  batches: [
    {
      id: 1,
      name: 'Batch A',
      code: 'A',
      order: 1,
      subbatches: DEFAULT_BATCH_GROUPS.A.map((c, i) => ({
        id: i + 1,
        code: c,
        name: c.toUpperCase(),
        order: i + 1,
      })),
    },
    {
      id: 2,
      name: 'Batch B',
      code: 'B',
      order: 2,
      subbatches: DEFAULT_BATCH_GROUPS.B.map((c, i) => ({
        id: i + 5,
        code: c,
        name: c.toUpperCase(),
        order: i + 1,
      })),
    },
    {
      id: 3,
      name: 'Batch C',
      code: 'C',
      order: 3,
      subbatches: DEFAULT_BATCH_GROUPS.C.map((c, i) => ({
        id: i + 9,
        code: c,
        name: c.toUpperCase(),
        order: i + 1,
      })),
    },
  ],
  time_slots: DEFAULT_SCHEDULE_TIME_SLOTS.map((label, i) => {
    const parts = label.split('–').map((s) => s.trim());
    return {
      id: i + 1,
      start_time: parts[0] || '9:00 AM',
      end_time: parts[1] || '11:00 AM',
      label,
      order: i + 1,
    };
  }),
  weekdays: DEFAULT_SCHEDULE_DAYS.map((name, i) => ({
    id: i + 1,
    name,
    code: name.slice(0, 3).toLowerCase(),
    order: i + 1,
  })),
};

export function useSchedules() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [configLoading, setConfigLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [form, setForm] = useState(INITIAL_FORM);
  const [config, setConfig] = useState(FALLBACK_CONFIG);

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchConfig = useCallback(async (signal) => {
    setConfigLoading(true);
    try {
      const data = await scheduleService.getConfig({ signal });
      if (isMountedRef.current && data) {
        setConfig((prev) => ({
          locations: Array.isArray(data.locations) && data.locations.length ? data.locations : prev.locations,
          batches: Array.isArray(data.batches) && data.batches.length ? data.batches : prev.batches,
          time_slots: Array.isArray(data.time_slots) && data.time_slots.length ? data.time_slots : prev.time_slots,
          weekdays: Array.isArray(data.weekdays) && data.weekdays.length ? data.weekdays : prev.weekdays,
        }));
      }
    } catch (err) {
      // Use fallback config if API unreachable (e.g. offline testing)
      console.warn('Using fallback schedule configuration:', err.message);
    } finally {
      if (isMountedRef.current) {
        setConfigLoading(false);
      }
    }
  }, []);

  const fetchSchedules = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const data = await scheduleService.getSchedules({ signal });
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
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchConfig(controller.signal);
    fetchSchedules(controller.signal);
    return () => controller.abort();
  }, [fetchConfig, fetchSchedules]);

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

  // Dynamic Batch CRUD
  const addBatch = useCallback(async (batchData) => {
    try {
      const newBatch = await scheduleService.createBatch(batchData);
      if (newBatch && isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          batches: [...prev.batches, newBatch],
        }));
      }
      return newBatch;
    } catch (err) {
      throw err;
    }
  }, []);

  const removeBatch = useCallback(async (batchId) => {
    try {
      await scheduleService.deleteBatch(batchId);
      if (isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          batches: prev.batches.filter((b) => b.id !== batchId),
        }));
      }
      return true;
    } catch (err) {
      throw err;
    }
  }, []);

  const addSubBatch = useCallback(async (subBatchData) => {
    try {
      const newSub = await scheduleService.createSubBatch(subBatchData);
      if (newSub && isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          batches: prev.batches.map((b) => {
            if (b.id === Number(subBatchData.batch)) {
              return {
                ...b,
                subbatches: [...(b.subbatches || []), newSub],
              };
            }
            return b;
          }),
        }));
      }
      return newSub;
    } catch (err) {
      throw err;
    }
  }, []);

  const removeSubBatch = useCallback(async (subBatchId, batchId) => {
    try {
      await scheduleService.deleteSubBatch(subBatchId);
      if (isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          batches: prev.batches.map((b) => {
            if (b.id === batchId) {
              return {
                ...b,
                subbatches: (b.subbatches || []).filter((s) => s.id !== subBatchId),
              };
            }
            return b;
          }),
        }));
      }
      return true;
    } catch (err) {
      throw err;
    }
  }, []);

  // Dynamic Time Slot CRUD
  const addTimeSlot = useCallback(async (slotData) => {
    try {
      const newSlot = await scheduleService.createTimeSlot(slotData);
      if (newSlot && isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          time_slots: [...prev.time_slots, newSlot].sort((a, b) => (a.order || 0) - (b.order || 0)),
        }));
      }
      return newSlot;
    } catch (err) {
      throw err;
    }
  }, []);

  const editTimeSlot = useCallback(async (id, slotData) => {
    try {
      const updated = await scheduleService.updateTimeSlot(id, slotData);
      if (updated && isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          time_slots: prev.time_slots.map((s) => (s.id === id ? updated : s)),
        }));
      }
      return updated;
    } catch (err) {
      throw err;
    }
  }, []);

  const removeTimeSlot = useCallback(async (id) => {
    try {
      await scheduleService.deleteTimeSlot(id);
      if (isMountedRef.current) {
        setConfig((prev) => ({
          ...prev,
          time_slots: prev.time_slots.filter((s) => s.id !== id),
        }));
      }
      return true;
    } catch (err) {
      throw err;
    }
  }, []);

  // Excel Upload & Parse
  const parseExcelFile = useCallback(async (file) => {
    try {
      const result = await scheduleService.parseExcel(file);
      if (result?.success) {
        setForm((prev) => ({
          ...prev,
          schedule_type: 'excel',
          excel_file: file,
          excel_file_name: result.file_name || file.name,
          excel_file_size: result.file_size || file.size,
          content_data: {
            day: result.selected_day || 'Monday',
            grid: result.grid || {},
            days_data: result.days_data || {},
          },
        }));
      }
      return result;
    } catch (err) {
      throw err;
    }
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
      let payload;
      if (form.excel_file) {
        const formData = new FormData();
        formData.append('title', form.title.trim());
        formData.append('excel_file', form.excel_file);
        formData.append('file_name', form.excel_file_name || form.excel_file.name);
        formData.append('file_size', String(form.excel_file_size || form.excel_file.size));
        formData.append('schedule_type', 'excel');
        formData.append('publish_at', isoDate);
        if (form.content_data) {
          formData.append('content_data', JSON.stringify(form.content_data));
        }
        payload = formData;
      } else {
        payload = {
          title: form.title.trim(),
          onedrive_url: form.onedrive_url ? form.onedrive_url.trim() : '',
          schedule_type: form.onedrive_url ? 'link' : 'grid',
          content_data: form.content_data ? JSON.stringify(form.content_data) : null,
          publish_at: isoDate,
        };
      }

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

  const deleteSchedule = useCallback(async (id, onSuccess) => {
    try {
      await scheduleService.deleteSchedule(id);
      await fetchSchedules();
      if (onSuccess) {
        onSuccess('Schedule deleted successfully.');
      }
      return true;
    } catch (err) {
      if (isMountedRef.current) {
        setError(formatErrorMessage(err));
      }
      return false;
    }
  }, [fetchSchedules]);

  return {
    schedules,
    loading,
    configLoading,
    config,
    isSubmitting,
    error,
    formErrors,
    form,
    updateFormField,
    resetForm,
    submitSchedule,
    deleteSchedule,
    refetch: fetchSchedules,
    refetchConfig: fetchConfig,
    clearError: () => setError(''),
    // Dynamic Management
    addBatch,
    removeBatch,
    addSubBatch,
    removeSubBatch,
    addTimeSlot,
    editTimeSlot,
    removeTimeSlot,
    parseExcelFile,
  };
}
