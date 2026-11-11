import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  MapPin,
  User as UserIcon,
  X,
  Check,
  RefreshCw,
  Code,
  Copy,
  Sparkles,
  ShieldAlert,
  Search,
  Filter,
  Layers,
  Send,
  HelpCircle,
  Trash2,
  Plus,
  Eye,
  CheckCircle,
  Tag,
  Building2,
} from 'lucide-react';
import { scheduleService } from '../../services/scheduleService';
import { usersService } from '../../services/usersService';

const WEEKDAYS = [
  { code: 'mon', label: 'Monday' },
  { code: 'tue', label: 'Tuesday' },
  { code: 'wed', label: 'Wednesday' },
  { code: 'thu', label: 'Thursday' },
  { code: 'fri', label: 'Friday' },
];

const TIME_SLOT_LABELS = [
  '08:30 - 09:30',
  '09:30 - 10:30',
  '10:30 - 11:30',
  '11:30 - 12:30',
  '01:30 - 02:30',
  '02:30 - 03:30',
  '03:30 - 04:30',
  '04:30 - 05:30',
];

function getSlotVariantClass(slot) {
  if (!slot) return 'slot-variant-selfstudy';
  if (slot.is_test) return 'slot-variant-test';
  if (slot.session_type === 'stream') return 'slot-variant-stream';
  if (slot.session_type === 'in_place') return 'slot-variant-inplace';
  if (slot.session_type === 'faculty') return 'slot-variant-faculty';
  return 'slot-variant-selfstudy';
}

export function TimetableGridEditor({ onNotify }) {
  // Master lists
  const [schedulesList, setSchedulesList] = useState([]);
  const [cohortsList, setCohortsList] = useState([]);
  const [schedulesLoading, setSchedulesLoading] = useState(false);

  // Active / Selected schedule state
  const [activeScheduleId, setActiveScheduleId] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [title, setTitle] = useState('TCS Ignite Master Weekly Schedule');
  const [selectedCohortId, setSelectedCohortId] = useState('');
  const [effectiveFrom, setEffectiveFrom] = useState('');
  const [effectiveUntil, setEffectiveUntil] = useState('');
  const [isActiveWeek, setIsActiveWeek] = useState(true);

  // Week Tracker Filter (ALL or specific cohort)
  const [weekTrackerCohortFilter, setWeekTrackerCohortFilter] = useState('ALL');

  // Matrix View Filters
  const [selectedDay, setSelectedDay] = useState('mon');
  const [selectedBatchFilter, setSelectedBatchFilter] = useState('ALL');
  const [spotCheckSubBatch, setSpotCheckSubBatch] = useState('A1');

  // UI Modes: 'matrix', 'spotcheck', 'json'
  const [viewMode, setViewMode] = useState('matrix');
  const [jsonText, setJsonText] = useState('');
  const [jsonCopied, setJsonCopied] = useState(false);

  // Excel Upload State
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Publishing State
  const [isPublishing, setIsPublishing] = useState(false);

  // Slot Editing Modal State
  const [editingCell, setEditingCell] = useState(null);
  const [editForm, setEditForm] = useState({
    title: '',
    location: '',
    session_type: 'self_study',
    is_test: false,
    faculty: '',
  });

  // Load all schedules & cohorts on mount
  useEffect(() => {
    fetchCohorts();
    loadAllSchedules();
  }, []);

  const fetchCohorts = async () => {
    try {
      const cohorts = await usersService.getCohorts();
      setCohortsList(cohorts || []);
    } catch (e) {
      console.error('Failed to load cohorts', e);
    }
  };

  const loadAllSchedules = async () => {
    setSchedulesLoading(true);
    try {
      const schedules = await scheduleService.getSchedules();
      setSchedulesList(schedules || []);
      const active = schedules.find((s) => s.is_active && s.grid_data && Object.keys(s.grid_data).length > 0) || schedules[0];
      if (active) {
        loadScheduleIntoEditor(active);
      }
    } catch (e) {
      console.error('Failed to load schedules', e);
    } finally {
      setSchedulesLoading(false);
    }
  };

  const loadScheduleIntoEditor = (schedule) => {
    if (!schedule) return;
    setActiveScheduleId(schedule.id);
    setTitle(schedule.title || 'TCS Ignite Master Weekly Schedule');
    setIsActiveWeek(Boolean(schedule.is_active));
    setEffectiveFrom(schedule.effective_from || '');
    setEffectiveUntil(schedule.effective_until || '');

    const cohortId = schedule.target_cohort?.id || schedule.target_cohort || '';
    setSelectedCohortId(cohortId);

    if (schedule.grid_data?.sub_batches) {
      setScheduleData(schedule.grid_data);
      setJsonText(JSON.stringify(schedule.grid_data, null, 2));
      const firstSb = Object.keys(schedule.grid_data.sub_batches)[0];
      if (firstSb) {
        setSpotCheckSubBatch(firstSb);
      }
    } else if (schedule.grid_data) {
      const wrapped = {
        cohort: schedule.target_cohort?.code || 'B50',
        sub_batches: {},
        grid_data: schedule.grid_data,
        test_slots: [],
      };
      setScheduleData(wrapped);
      setJsonText(JSON.stringify(wrapped, null, 2));
    }
  };

  const handleStartNewWeek = () => {
    setActiveScheduleId(null);
    setScheduleData(null);
    setJsonText('');
    setTitle('TCS Ignite Week Schedule');
    setIsActiveWeek(true);
    setEffectiveFrom('');
    setEffectiveUntil('');
    onNotify?.('Started new schedule draft. Select cohort and upload your timetable spreadsheet.');
  };

  // Upload & Parse Excel Spreadsheet
  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploadLoading(true);
    setUploadError('');

    try {
      const parsed = await scheduleService.parseExcelSchedule(file);
      if (!parsed.success) {
        throw new Error(parsed.errors?.[0] || 'Failed to parse Excel schedule.');
      }

      // Reset activeScheduleId so saving this uploaded file creates a separate week record
      setActiveScheduleId(null);
      setScheduleData(parsed);
      setJsonText(JSON.stringify(parsed, null, 2));
      const parsedCohort = parsed.cohort || 'B50';
      setTitle(`TCS Ignite ${parsedCohort} - Weekly Master Timetable`);
      setIsActiveWeek(false);

      // Match and pre-select cohort
      if (cohortsList.length > 0 && parsedCohort) {
        const matching = cohortsList.find(
          (c) => (c.code || '').toLowerCase() === parsedCohort.toLowerCase()
        );
        if (matching) {
          setSelectedCohortId(matching.id);
        }
      }

      const availableSubBatches = Object.keys(parsed.sub_batches || {});
      if (availableSubBatches.length > 0) {
        setSpotCheckSubBatch(availableSubBatches[0]);
      }

      onNotify?.(`Schedule parsed successfully! ${parsed.slot_count} slots across ${availableSubBatches.length} sub-batches ready to save.`);
    } catch (err) {
      setUploadError(err.message || 'Error uploading or parsing Excel schedule.');
    } finally {
      setUploadLoading(false);
    }
  };

  // Publish & Save Schedule
  const handlePublishSchedule = async () => {
    if (!scheduleData) {
      alert('No timetable data loaded to save. Please upload a spreadsheet or load an existing week.');
      return;
    }

    setIsPublishing(true);
    try {
      const todayIso = new Date().toISOString().split('T')[0];
      const isFutureEffective = effectiveFrom && effectiveFrom > todayIso;

      const payload = {
        title: title.trim() || 'TCS Ignite Weekly Master Timetable',
        target_type: selectedCohortId ? 'COHORT' : 'ALL',
        target_cohort: selectedCohortId || null,
        effective_from: effectiveFrom || null,
        effective_until: effectiveUntil || null,
        grid_data: scheduleData,
        is_active: isActiveWeek && !isFutureEffective,
        status: isFutureEffective ? 'SCHEDULED' : (isActiveWeek ? 'PUBLISHED' : 'DRAFT'),
      };

      let res;
      if (activeScheduleId) {
        res = await scheduleService.updateSchedule(activeScheduleId, payload);
      } else {
        res = await scheduleService.createSchedule(payload);
        if (res?.data?.id || res?.id) {
          setActiveScheduleId(res.data?.id || res.id);
        }
      }

      // Reload schedules list to reflect latest changes
      const updatedSchedules = await scheduleService.getSchedules();
      setSchedulesList(updatedSchedules);

      if (res?.message) {
        onNotify?.(res.message);
      } else if (isFutureEffective) {
        onNotify?.(`Upcoming week schedule saved for ${effectiveFrom}. It will NOT be broadcasted until activated.`);
      } else if (isActiveWeek) {
        onNotify?.('Active master timetable saved and broadcast to trainees in real time!');
      } else {
        onNotify?.('Schedule draft saved successfully.');
      }
    } catch (err) {
      alert(`Publishing failed: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  // Delete Schedule Handler
  const handleDeleteSchedule = async (scheduleId, e) => {
    if (e) e.stopPropagation();
    if (!scheduleId) return;

    const itemToDelete = schedulesList.find((s) => s.id === scheduleId);
    const scheduleTitle = itemToDelete?.title || `Schedule #${scheduleId}`;
    const wasActive = itemToDelete?.is_active;

    const confirmMsg = wasActive
      ? `Are you sure you want to delete '${scheduleTitle}'?\n\nWARNING: This schedule is currently ACTIVE. Deleting it will remove the timetable from all connected trainee desktop apps.`
      : `Are you sure you want to delete '${scheduleTitle}'?`;

    if (!window.confirm(confirmMsg)) return;

    try {
      await scheduleService.deleteSchedule(scheduleId);
      onNotify?.(`Schedule '${scheduleTitle}' deleted successfully.`);

      const updatedSchedules = await scheduleService.getSchedules();
      setSchedulesList(updatedSchedules);

      if (scheduleId === activeScheduleId) {
        const nextActive = updatedSchedules.find((s) => s.is_active) || updatedSchedules[0] || null;
        if (nextActive) {
          loadScheduleIntoEditor(nextActive);
        } else {
          setActiveScheduleId(null);
          setScheduleData(null);
          setJsonText('');
          setTitle('TCS Ignite Master Weekly Schedule');
        }
      }
    } catch (err) {
      alert(`Failed to delete schedule: ${err.message}`);
    }
  };

  // Set Active Schedule
  const handleSetActiveSchedule = async (scheduleId, e) => {
    if (e) e.stopPropagation();
    try {
      const res = await scheduleService.activateSchedule(scheduleId);
      setIsActiveWeek(true);
      onNotify?.(res?.message || 'Weekly schedule activated and synchronized to all trainees!');
      const updatedSchedules = await scheduleService.getSchedules();
      setSchedulesList(updatedSchedules);
      const active = updatedSchedules.find((s) => s.id === scheduleId);
      if (active) loadScheduleIntoEditor(active);
    } catch (err) {
      alert(`Failed to activate schedule: ${err.message}`);
    }
  };

  // Slot Edit Handlers
  const handleOpenEditSlot = (subBatch, day, slotIndex, slot) => {
    setEditingCell({ subBatch, day, slotIndex, slot });
    setEditForm({
      title: slot?.title || '',
      location: slot?.location || '',
      session_type: slot?.session_type || 'self_study',
      is_test: Boolean(slot?.is_test),
      faculty: slot?.faculty || '',
    });
  };

  const handleSaveEditedSlot = (e) => {
    e.preventDefault();
    if (!editingCell || !scheduleData) return;

    const { subBatch, day, slotIndex, slot } = editingCell;
    const updatedSlot = {
      ...slot,
      title: editForm.title.trim(),
      location: editForm.location.trim() || 'Home Lab',
      session_type: editForm.is_test ? 'test' : editForm.session_type,
      is_test: editForm.is_test,
      faculty: editForm.faculty.trim(),
      color: editForm.is_test ? 'FFFFB74D' : editForm.session_type === 'faculty' ? 'FF64B5F6' : 'none',
    };

    const nextData = { ...scheduleData };
    if (nextData.sub_batches?.[subBatch]?.[day]) {
      nextData.sub_batches[subBatch][day][slotIndex] = updatedSlot;
    }

    setScheduleData(nextData);
    setJsonText(JSON.stringify(nextData, null, 2));
    setEditingCell(null);
    onNotify?.(`Updated ${subBatch} ${day.toUpperCase()} slot: ${updatedSlot.title}`);
  };

  const handleClearSlot = () => {
    if (!editingCell || !scheduleData) return;
    const { subBatch, day, slotIndex } = editingCell;
    const clearedSlot = {
      title: 'Incubator',
      location: 'WA',
      session_type: 'self_study',
      is_test: false,
      faculty: '',
      color: 'none',
      start: editingCell.slot?.start || '09:00',
      end: editingCell.slot?.end || '10:30',
    };
    const nextData = { ...scheduleData };
    if (nextData.sub_batches?.[subBatch]?.[day]) {
      nextData.sub_batches[subBatch][day][slotIndex] = clearedSlot;
    }
    setScheduleData(nextData);
    setJsonText(JSON.stringify(nextData, null, 2));
    setEditingCell(null);
    onNotify?.(`Cleared slot for ${subBatch} on ${day.toUpperCase()}`);
  };

  const subBatchKeys = scheduleData?.sub_batches ? Object.keys(scheduleData.sub_batches) : [];
  const dynamicDerivedBatches = Array.from(
    new Set(subBatchKeys.map((sb) => sb.match(/^[A-Za-z]+/)?.[0] || sb))
  ).filter(Boolean);
  const batchesList = scheduleData?.batches && Object.keys(scheduleData.batches).length > 0
    ? Object.keys(scheduleData.batches)
    : dynamicDerivedBatches.length > 0
    ? dynamicDerivedBatches
    : ['A', 'B', 'C'];

  const filteredSubBatches = subBatchKeys.filter((sb) => {
    if (selectedBatchFilter === 'ALL') return true;
    return sb.startsWith(selectedBatchFilter);
  });

  const filteredSchedulesList = schedulesList.filter((s) => {
    if (weekTrackerCohortFilter === 'ALL') return true;
    const cohortCode = s.target_cohort?.code || s.cohort_detail?.code || '';
    return cohortCode.toLowerCase() === weekTrackerCohortFilter.toLowerCase();
  });

  const todayIso = new Date().toISOString().split('T')[0];
  const isFutureEffective = Boolean(effectiveFrom && effectiveFrom > todayIso);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* 1. WEEK TRACKER: MANAGE & SWITCH SCHEDULES ACROSS WEEKS */}
      <section className="timetable-master-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: '#EEF2FF', color: '#4F46E5', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '10px' }}>
                <Calendar size={18} />
              </span>
              <div>
                <h2 style={{ fontSize: '17px', fontWeight: 800, margin: 0, color: 'var(--color-text-primary)' }}>
                  Weekly Schedules Tracker
                </h2>
                <p style={{ margin: '2px 0 0 0', fontSize: '12.5px', color: 'var(--color-text-secondary)' }}>
                  Track schedules week by week. Select any week to load into the matrix editor, switch the active cohort timetable, or remove obsolete weeks.
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                Filter Cohort:
              </label>
              <select
                value={weekTrackerCohortFilter}
                onChange={(e) => setWeekTrackerCohortFilter(e.target.value)}
                className="form-select"
                style={{ padding: '6px 12px', fontSize: '12.5px', borderRadius: '8px' }}
              >
                <option value="ALL">All Cohorts</option>
                {cohortsList.map((c) => (
                  <option key={c.id} value={c.code}>
                    {c.name || c.code} ({c.code})
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={handleStartNewWeek}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 14px', fontSize: '12.5px' }}
            >
              <Plus size={14} />
              <span>New Week Draft</span>
            </button>
          </div>
        </div>

        {/* Schedules Grid / List */}
        {schedulesLoading ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '12.5px' }}>
            Loading weekly schedules...
          </div>
        ) : filteredSchedulesList.length === 0 ? (
          <div style={{ padding: '28px', textAlign: 'center', background: '#F8FAFC', borderRadius: '10px', border: '1px dashed var(--color-border)' }}>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              No weekly schedules found for this filter. Click <strong>New Week Draft</strong> or upload a timetable below to get started.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {filteredSchedulesList.map((item) => {
              const isSelected = item.id === activeScheduleId;
              const cohortCode = item.target_cohort?.code || item.cohort_detail?.code || (item.grid_data?.cohort) || 'Campus';
              const slotCount = item.grid_data?.slot_count || (item.grid_data?.sub_batches ? Object.values(item.grid_data.sub_batches).reduce((sum, d) => sum + Object.values(d).flat().length, 0) : 0);
              const todayIso = new Date().toISOString().split('T')[0];
              const isFutureSchedule = item.status === 'SCHEDULED' || (item.effective_from && item.effective_from > todayIso);

              return (
                <div
                  key={item.id}
                  onClick={() => loadScheduleIntoEditor(item)}
                  style={{
                    padding: '14px',
                    borderRadius: '10px',
                    border: isSelected ? '2px solid #4F46E5' : '1px solid var(--color-border)',
                    background: isSelected ? '#F5F7FF' : 'var(--color-white)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ fontSize: '10.5px', fontWeight: 800, padding: '2px 8px', borderRadius: '6px', background: '#E0E7FF', color: '#3730A3', textTransform: 'uppercase' }}>
                      Cohort {cohortCode}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {item.is_active ? (
                        <span style={{ fontSize: '10.5px', fontWeight: 700, padding: '2px 8px', borderRadius: '6px', background: '#DCFCE7', color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle size={10} /> Active Week
                        </span>
                      ) : isFutureSchedule ? (
                        <span style={{ fontSize: '10.5px', fontWeight: 700, padding: '2px 8px', borderRadius: '6px', background: '#EEF2FF', color: '#4F46E5', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={10} /> Scheduled
                        </span>
                      ) : (
                        <span style={{ fontSize: '10.5px', fontWeight: 600, padding: '2px 8px', borderRadius: '6px', background: '#F1F5F9', color: '#64748B', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          Archived
                        </span>
                      )}
                    </div>
                  </div>

                  <h4 style={{ margin: 0, fontSize: '13.5px', fontWeight: 700, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.title}
                  </h4>

                  <div style={{ fontSize: '11.5px', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span>{slotCount > 0 ? `${slotCount} slots` : 'Grid available'}</span>
                    <span>·</span>
                    <span>{item.effective_from ? `${item.effective_from} to ${item.effective_until || 'present'}` : 'All week'}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                    <span style={{ fontSize: '11px', color: isSelected ? '#4F46E5' : 'var(--color-text-secondary)', fontWeight: isSelected ? 700 : 500 }}>
                      {isSelected ? 'Currently Loaded' : 'Click to View'}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {!item.is_active && (
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={(e) => handleSetActiveSchedule(item.id, e)}
                          title="Set this week as the active timetable for trainees"
                          style={{ fontSize: '11px', padding: '3px 8px', color: '#16A34A', fontWeight: 600 }}
                        >
                          Activate
                        </button>
                      )}
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={(e) => handleDeleteSchedule(item.id, e)}
                        title="Delete this schedule permanently"
                        style={{ fontSize: '11px', padding: '3px 6px', color: '#DC2626' }}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* 2. CURRENT SCHEDULE CONFIGURATION & ACTIONS BAR */}
      <section className="timetable-master-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                {activeScheduleId ? `Editing: ${title}` : 'Configure Weekly Timetable'}
              </h3>
              {isActiveWeek ? (
                <span style={{ fontSize: '10.5px', fontWeight: 700, padding: '2px 8px', borderRadius: '6px', background: '#DCFCE7', color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle size={11} /> Live Timetable
                </span>
              ) : isFutureEffective ? (
                <span style={{ fontSize: '10.5px', fontWeight: 700, padding: '2px 8px', borderRadius: '6px', background: '#EEF2FF', color: '#4F46E5', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Clock size={11} /> Upcoming Schedule
                </span>
              ) : null}
            </div>
            <p style={{ margin: '3px 0 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              {isFutureEffective && !isActiveWeek
                ? `Upcoming week schedule starting ${effectiveFrom}. Saving will prepare this timetable without broadcasting to trainees now.`
                : isActiveWeek
                ? 'Current live timetable. Saving and publishing will broadcast updates to trainees in real time.'
                : 'Configure timetable details and validity dates.'}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {activeScheduleId && !isActiveWeek && (
              <button
                type="button"
                className="secondary-button"
                onClick={async () => {
                  if (window.confirm(`Are you sure you want to activate '${title}' as the current live timetable for trainees? This will replace the current active timetable and synchronize to trainees immediately.`)) {
                    await handleSetActiveSchedule(activeScheduleId);
                  }
                }}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 15px', fontSize: '12.5px', color: '#16A34A', borderColor: '#86EFAC', background: '#F0FDF4', fontWeight: 700 }}
                title="Activate this week as the current live timetable for trainees"
              >
                <CheckCircle size={15} />
                <span>Activate as Live Timetable</span>
              </button>
            )}

            {activeScheduleId && (
              <button
                type="button"
                className="danger-button"
                onClick={(e) => handleDeleteSchedule(activeScheduleId, e)}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 14px', fontSize: '12.5px' }}
                title="Delete this schedule and un-sync obsolete slots from trainees"
              >
                <Trash2 size={14} />
                <span>Delete Schedule</span>
              </button>
            )}

            <button
              type="button"
              className="primary-button"
              onClick={handlePublishSchedule}
              disabled={isPublishing || !scheduleData}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '9px 18px', fontWeight: 700, fontSize: '13px' }}
            >
              {isFutureEffective && !isActiveWeek ? (
                <>
                  <Clock size={15} />
                  <span>{isPublishing ? 'Saving...' : 'Save Upcoming Week Schedule'}</span>
                </>
              ) : (
                <>
                  <Send size={15} />
                  <span>{isPublishing ? 'Publishing...' : 'Publish & Broadcast Schedule'}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Form Fields: Title, Cohort, Dates */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '5px' }}>
              Schedule / Week Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="text-input"
              placeholder="e.g. Batch 50 - Week 15 Schedule"
              style={{ width: '100%', fontSize: '13px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '5px' }}>
              Target Cohort
            </label>
            <select
              value={selectedCohortId}
              onChange={(e) => setSelectedCohortId(e.target.value)}
              className="form-select"
              style={{ width: '100%', fontSize: '13px', padding: '8px 12px' }}
            >
              <option value="">All Cohorts (Campus-Wide)</option>
              {cohortsList.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || c.code} ({c.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '5px' }}>
              Effective From (Start Date)
            </label>
            <input
              type="date"
              value={effectiveFrom}
              onChange={(e) => setEffectiveFrom(e.target.value)}
              className="text-input"
              style={{ width: '100%', fontSize: '13px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '5px' }}>
              Effective Until (End Date)
            </label>
            <input
              type="date"
              value={effectiveUntil}
              onChange={(e) => setEffectiveUntil(e.target.value)}
              className="text-input"
              style={{ width: '100%', fontSize: '13px' }}
            />
          </div>
        </div>
      </section>

      {/* 3. EXCEL FILE UPLOAD DROPZONE */}
      <section className="timetable-master-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <span style={{ background: '#E8F5EF', color: '#107C41', width: '34px', height: '34px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>
            <FileSpreadsheet size={18} />
          </span>
          <div>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
              Spreadsheet Ingestion & Verification
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Upload your official weekly timetable (.xlsx) to parse all 12 sub-batches, specialization streams, lab venues, and exam time slots.
            </p>
          </div>
        </div>

        <div
          className="timetable-dropzone"
          onClick={() => document.getElementById('master-excel-input')?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
          }}
        >
          <input
            id="master-excel-input"
            type="file"
            accept=".xlsx, .xls"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
            }}
          />

          <div className="timetable-dropzone-icon">
            <Upload size={22} />
          </div>

          <h3>
            {uploadLoading ? 'Parsing & Validating Spreadsheet...' : 'Drop weekly schedule spreadsheet here, or click to browse'}
          </h3>
          <p>
            Supports multi-sheet workbooks containing Schedule, Stream, Stream Faculty, TA mapping, and Proctoring List.
          </p>
        </div>

        {uploadError && (
          <div style={{ marginTop: '14px', padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#DC2626', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{uploadError}</span>
          </div>
        )}

        {/* PARSED METRICS SUMMARY */}
        {scheduleData && (
          <div style={{ marginTop: '20px' }}>
            <div className="timetable-metrics-grid">
              <div className="timetable-metric-box">
                <div className="timetable-metric-label">Target Cohort</div>
                <div className="timetable-metric-value">{scheduleData.cohort || 'B50'}</div>
                <div className="timetable-metric-sub">TCS Ignite Campus</div>
              </div>

              <div className="timetable-metric-box">
                <div className="timetable-metric-label">Sub-Batches Parsed</div>
                <div className="timetable-metric-value">{subBatchKeys.length}</div>
                <div className="timetable-metric-sub">Across 5 Working Days</div>
              </div>

              <div className="timetable-metric-box">
                <div className="timetable-metric-label">Total Slots Loaded</div>
                <div className="timetable-metric-value">{scheduleData.slot_count || subBatchKeys.length * 40}</div>
                <div className="timetable-metric-sub">8 slots / day / sub-batch</div>
              </div>

              <div className="timetable-metric-box">
                <div className="timetable-metric-label">Assessments & Tests</div>
                <div className="timetable-metric-value" style={{ color: '#D97706' }}>
                  {scheduleData.test_slots?.length || 0}
                </div>
                <div className="timetable-metric-sub">Buddy Lock Enabled</div>
              </div>

              <div className="timetable-metric-box">
                <div className="timetable-metric-label">Technical Streams</div>
                <div className="timetable-metric-value">{scheduleData.streams ? Object.keys(scheduleData.streams).length : 0}</div>
                <div className="timetable-metric-sub">Specializations Mapped</div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 4. MASTER INTERACTIVE TIMETABLE MATRIX */}
      {scheduleData && (
        <section className="timetable-master-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                Weekly Timetable Matrix
              </span>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                (Click any cell to edit details or clear the slot)
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Day Selector */}
              <div style={{ display: 'flex', background: '#F1F5F9', padding: '3px', borderRadius: '8px', gap: '3px' }}>
                {WEEKDAYS.map((d) => (
                  <button
                    key={d.code}
                    type="button"
                    onClick={() => setSelectedDay(d.code)}
                    style={{
                      border: 'none',
                      background: selectedDay === d.code ? '#FFFFFF' : 'transparent',
                      color: selectedDay === d.code ? '#0F172A' : '#64748B',
                      fontWeight: selectedDay === d.code ? 700 : 500,
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      boxShadow: selectedDay === d.code ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                      transition: 'all 0.12s ease',
                    }}
                  >
                    {d.label}
                  </button>
                ))}
              </div>

              {/* Batch Filter */}
              <select
                value={selectedBatchFilter}
                onChange={(e) => setSelectedBatchFilter(e.target.value)}
                className="form-select"
                style={{ padding: '5px 10px', fontSize: '12px', borderRadius: '8px' }}
              >
                <option value="ALL">All Batches</option>
                {batchesList.map((b) => (
                  <option key={b} value={b}>Batch {b}</option>
                ))}
              </select>

              {/* View Mode Toggle */}
              <div style={{ display: 'flex', background: '#F1F5F9', padding: '3px', borderRadius: '8px', gap: '3px' }}>
                <button
                  type="button"
                  onClick={() => setViewMode('matrix')}
                  style={{
                    border: 'none',
                    background: viewMode === 'matrix' ? '#FFFFFF' : 'transparent',
                    color: viewMode === 'matrix' ? '#0F172A' : '#64748B',
                    fontWeight: viewMode === 'matrix' ? 700 : 500,
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    cursor: 'pointer',
                  }}
                >
                  Matrix
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('spotcheck')}
                  style={{
                    border: 'none',
                    background: viewMode === 'spotcheck' ? '#FFFFFF' : 'transparent',
                    color: viewMode === 'spotcheck' ? '#0F172A' : '#64748B',
                    fontWeight: viewMode === 'spotcheck' ? 700 : 500,
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    cursor: 'pointer',
                  }}
                >
                  Spot-Check
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('json')}
                  style={{
                    border: 'none',
                    background: viewMode === 'json' ? '#FFFFFF' : 'transparent',
                    color: viewMode === 'json' ? '#0F172A' : '#64748B',
                    fontWeight: viewMode === 'json' ? 700 : 500,
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    cursor: 'pointer',
                  }}
                >
                  JSON
                </button>
              </div>
            </div>
          </div>

          {/* Color Key Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', padding: '10px 14px', background: '#F8FAFC', borderRadius: '8px', marginBottom: '14px', fontSize: '11.5px' }}>
            <span style={{ fontWeight: 700, color: 'var(--color-text-secondary)' }}>Color Key:</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <i style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#64B5F6', display: 'inline-block' }} />
              <span>Faculty Session (TR)</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <i style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#81C784', display: 'inline-block' }} />
              <span>In-Place Lab</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <i style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#FFB74D', display: 'inline-block' }} />
              <span>Test / Exam (Buddy Locked)</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <i style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#E2E8F0', display: 'inline-block' }} />
              <span>Self-Study / Project (WA)</span>
            </span>
          </div>

          {/* MATRIX VIEW */}
          {viewMode === 'matrix' && (
            <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: '10px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '980px', fontSize: '12px' }}>
                <thead>
                  <tr style={{ background: '#F8FAFC', borderBottom: '2px solid var(--color-border)' }}>
                    <th style={{ padding: '10px 14px', fontWeight: 800, width: '110px', color: 'var(--color-text-primary)' }}>
                      Sub-Batch
                    </th>
                    {TIME_SLOT_LABELS.map((slotLabel, idx) => (
                      <th key={idx} style={{ padding: '10px 8px', fontWeight: 700, color: 'var(--color-text-secondary)', textAlign: 'center' }}>
                        <div>Slot {idx + 1}</div>
                        <div style={{ fontSize: '10px', fontWeight: 500, color: '#94A3B8' }}>{slotLabel}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredSubBatches.map((sb) => {
                    const daySlots = scheduleData.sub_batches?.[sb]?.[selectedDay] || [];
                    return (
                      <tr key={sb} style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: '10px 14px', fontWeight: 800, color: '#334155', background: '#FAFAFA' }}>
                          <span style={{ padding: '3px 8px', background: '#E2E8F0', borderRadius: '6px' }}>
                            {sb}
                          </span>
                        </td>
                        {Array.from({ length: 8 }).map((_, slotIdx) => {
                          const slot = daySlots[slotIdx] || { title: 'Self-Study', location: 'WA', session_type: 'self_study' };
                          const variantClass = getSlotVariantClass(slot);
                          return (
                            <td
                              key={slotIdx}
                              onClick={() => handleOpenEditSlot(sb, selectedDay, slotIdx, slot)}
                              className={`timetable-slot-cell ${variantClass}`}
                              style={{
                                padding: '8px 6px',
                                borderLeft: '1px solid var(--color-border)',
                                cursor: 'pointer',
                                verticalAlign: 'top',
                                transition: 'all 0.12s ease',
                              }}
                              title="Click to edit or clear this slot"
                            >
                              <div style={{ fontWeight: 700, fontSize: '11.5px', lineHeight: 1.25, marginBottom: '2px' }}>
                                {slot.title || 'Self-Study'}
                              </div>
                              <div style={{ fontSize: '10px', opacity: 0.85, display: 'flex', alignItems: 'center', gap: '3px' }}>
                                <MapPin size={9} />
                                <span>{slot.location || 'WA'}</span>
                              </div>
                              {slot.is_test && (
                                <span style={{ marginTop: '3px', display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '9px', fontWeight: 800, background: '#DC2626', color: '#FFF', padding: '1px 4px', borderRadius: '3px' }}>
                                  TEST
                                </span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* SPOT-CHECK VIEW */}
          {viewMode === 'spotcheck' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <label style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  Inspect Sub-Batch:
                </label>
                <select
                  value={spotCheckSubBatch}
                  onChange={(e) => setSpotCheckSubBatch(e.target.value)}
                  className="form-select"
                  style={{ padding: '6px 12px', fontSize: '13px', fontWeight: 700 }}
                >
                  {subBatchKeys.map((sb) => (
                    <option key={sb} value={sb}>Sub-Batch {sb}</option>
                  ))}
                </select>
              </div>

              <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: '10px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '860px', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: '#F8FAFC', borderBottom: '2px solid var(--color-border)' }}>
                      <th style={{ padding: '10px 14px', fontWeight: 800, width: '100px' }}>Day</th>
                      {TIME_SLOT_LABELS.map((slotLabel, idx) => (
                        <th key={idx} style={{ padding: '10px 8px', fontWeight: 700, color: 'var(--color-text-secondary)', textAlign: 'center' }}>
                          <div>Slot {idx + 1}</div>
                          <div style={{ fontSize: '10px', color: '#94A3B8' }}>{slotLabel}</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {WEEKDAYS.map((d) => {
                      const daySlots = scheduleData.sub_batches?.[spotCheckSubBatch]?.[d.code] || [];
                      return (
                        <tr key={d.code} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 800, color: '#334155', background: '#FAFAFA' }}>
                            {d.label}
                          </td>
                          {Array.from({ length: 8 }).map((_, slotIdx) => {
                            const slot = daySlots[slotIdx] || { title: 'Self-Study', location: 'WA' };
                            const variantClass = getSlotVariantClass(slot);
                            return (
                              <td
                                key={slotIdx}
                                onClick={() => handleOpenEditSlot(spotCheckSubBatch, d.code, slotIdx, slot)}
                                className={`timetable-slot-cell ${variantClass}`}
                                style={{ padding: '8px 6px', borderLeft: '1px solid var(--color-border)', cursor: 'pointer' }}
                              >
                                <div style={{ fontWeight: 700, fontSize: '11px', lineHeight: 1.2 }}>{slot.title}</div>
                                <div style={{ fontSize: '9.5px', opacity: 0.85 }}>{slot.location}</div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* JSON VIEW */}
          {viewMode === 'json' && (
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 10 }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    navigator.clipboard.writeText(jsonText);
                    setJsonCopied(true);
                    setTimeout(() => setJsonCopied(false), 1500);
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '5px 10px', fontSize: '11px' }}
                >
                  <Copy size={12} />
                  <span>{jsonCopied ? 'Copied' : 'Copy JSON'}</span>
                </button>
              </div>
              <textarea
                value={jsonText}
                readOnly
                rows={20}
                style={{
                  width: '100%',
                  fontFamily: 'monospace',
                  fontSize: '11.5px',
                  padding: '14px',
                  background: '#0F172A',
                  color: '#38BDF8',
                  borderRadius: '10px',
                  border: '1px solid #1E293B',
                  lineHeight: 1.45,
                }}
              />
            </div>
          )}
        </section>
      )}

      {/* 5. EDIT OR CLEAR SLOT MODAL */}
      {editingCell && (
        <div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          onClick={() => setEditingCell(null)}
        >
          <div
            className="modal-card"
            style={{ maxWidth: '440px', width: '92vw' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Edit Lecture Slot ({editingCell.subBatch} · {editingCell.day.toUpperCase()})
              </h3>
              <button
                type="button"
                className="btn-close"
                onClick={() => setEditingCell(null)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveEditedSlot} className="modal-form">
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, display: 'block', marginBottom: '4px', color: 'var(--color-text-primary)' }}>
                  Session / Subject Title
                </label>
                <input
                  type="text"
                  required
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="text-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. Java, Agile, WebTech, Incubator"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, display: 'block', marginBottom: '4px', color: 'var(--color-text-primary)' }}>
                  Venue / Location
                </label>
                <input
                  type="text"
                  required
                  value={editForm.location}
                  onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                  className="text-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. TR1, TR2, WA, Lab 1"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, display: 'block', marginBottom: '4px', color: 'var(--color-text-primary)' }}>
                  Session Type
                </label>
                <select
                  value={editForm.session_type}
                  onChange={(e) => setEditForm({ ...editForm, session_type: e.target.value })}
                  className="form-select"
                  style={{ width: '100%', fontSize: '12.5px' }}
                >
                  <option value="faculty">Faculty-Led Lecture (TR)</option>
                  <option value="in_place">In-Place Lab Session (Lab)</option>
                  <option value="stream">Stream Specialization</option>
                  <option value="self_study">Self-Study / Incubator (WA)</option>
                  <option value="test">Test / Evaluation</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, display: 'block', marginBottom: '4px', color: 'var(--color-text-primary)' }}>
                  Faculty / Instructor (Optional)
                </label>
                <input
                  type="text"
                  value={editForm.faculty}
                  onChange={(e) => setEditForm({ ...editForm, faculty: e.target.value })}
                  className="text-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. Dr. Sharma"
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '4px 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  <input
                    type="checkbox"
                    checked={editForm.is_test}
                    onChange={(e) => setEditForm({ ...editForm, is_test: e.target.checked })}
                    style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
                  />
                  <span>Is this an Assessment / Test? (Triggers automated Buddy lock)</span>
                </label>
              </div>

              <div className="modal-actions" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  className="danger-button"
                  onClick={handleClearSlot}
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '7px 12px', fontSize: '12px' }}
                  title="Remove this lecture and clear this slot"
                >
                  <Trash2 size={13} />
                  <span>Clear Slot</span>
                </button>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setEditingCell(null)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="primary-button"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
