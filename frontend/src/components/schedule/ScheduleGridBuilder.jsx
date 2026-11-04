/**
 * ScheduleGridBuilder.jsx — Interactive 7-Location Timetable Grid Builder.
 *
 * Features:
 *  - Renders 7 location columns in fixed order:
 *      Lab 1 (Hardware), Lab 2 (Software), Lab 3 (Data & AI), Lab 4 (Cloud Ops),
 *      Work Area, TR1, TR2 (Incubator column removed).
 *  - Working day pills: strictly Monday through Friday.
 *  - Configurable time slot rows: (e.g. 9:00 AM – 11:00 AM, 11:30 AM – 1:30 PM, etc.).
 *  - Grid cells:
 *      • Topic input field: enter lab subject/course title.
 *      • Dynamic batch selector: chips for sub-batches (A1..A4, B1..B4, C1..C4, etc.).
 *      • Clear cell button: removes all assigned sub-batches from that cell.
 *  - Top bar actions:
 *      • Assigned slot counter (e.g., "7 / 28 slots assigned").
 *      • "+ Add Batch" modal button for dynamic cohort creation.
 *      • "+ Add Time Slot" modal button for dynamic period creation.
 *      • "Clear [Day]" button to reset current day's entries.
 *
 * State structure:
 *  value.day: string ('Monday')
 *  value.grid: { [timeSlot]: { [location]: { topic: string, subbatches: string[] } } }
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Clock,
  Calendar,
  Users,
  BookOpen,
  Trash2,
  CheckCircle2,
  Sparkles,
  Info,
  Plus,
  Settings,
  Layers,
} from 'lucide-react';
import {
  DEFAULT_SCHEDULE_LOCATIONS,
  DEFAULT_LAB_METADATA,
  DEFAULT_SCHEDULE_DAYS,
  DEFAULT_SCHEDULE_TIME_SLOTS,
} from '../../constants';
import { BatchManagerModal } from './BatchManagerModal';
import { TimeSlotManagerModal } from './TimeSlotManagerModal';

export function ScheduleGridBuilder({
  value,
  onChange,
  disabled,
  config,
  onAddBatch,
  onRemoveBatch,
  onAddSubBatch,
  onRemoveSubBatch,
  onAddTimeSlot,
  onEditTimeSlot,
  onRemoveTimeSlot,
}) {
  const gridData = value?.grid || {};
  const selectedDay = value?.day || 'Monday';
  const scrollRef = useRef(null);
  const [isScrolling, setIsScrolling] = useState(false);

  // Modals state
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isTimeSlotModalOpen, setIsTimeSlotModalOpen] = useState(false);

  // Extract dynamic items or fallback to defaults
  const locations =
    config?.locations?.length > 0
      ? config.locations.map((l) => (typeof l === 'string' ? l : l.name))
      : DEFAULT_SCHEDULE_LOCATIONS;

  const weekdays =
    config?.weekdays?.length > 0
      ? config.weekdays.map((w) => (typeof w === 'string' ? w : w.name)).filter((d) => !['Saturday', 'Sunday'].includes(d))
      : DEFAULT_SCHEDULE_DAYS;

  const timeSlots =
    config?.time_slots?.length > 0
      ? config.time_slots.map((t) => (typeof t === 'string' ? t : t.label || `${t.start_time} – ${t.end_time}`))
      : DEFAULT_SCHEDULE_TIME_SLOTS;

  // Dynamic Batches
  const batchGroups = {};
  if (config?.batches?.length > 0) {
    config.batches.forEach((b) => {
      batchGroups[b.code] = (b.subbatches || []).map((s) => s.code.toLowerCase());
    });
  } else {
    batchGroups['A'] = ['a1', 'a2', 'a3', 'a4'];
    batchGroups['B'] = ['b1', 'b2', 'b3', 'b4'];
    batchGroups['C'] = ['c1', 'c2', 'c3', 'c4'];
  }

  const batchGroupKeys = Object.keys(batchGroups);

  // Color & Badge lookup for locations
  const getLocationMeta = (locName) => {
    if (config?.locations) {
      const found = config.locations.find((l) => (typeof l === 'string' ? l : l.name) === locName);
      if (found && found.badge) {
        return { badge: found.badge, color: found.color || '#014BAA' };
      }
    }
    return DEFAULT_LAB_METADATA[locName] || { badge: locName, color: '#014BAA' };
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      const canScroll = el.scrollWidth > el.clientWidth;
      const isAtEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 8;
      setIsScrolling(canScroll && !isAtEnd);
    };

    el.addEventListener('scroll', handleScroll);
    handleScroll();

    window.addEventListener('resize', handleScroll);
    return () => {
      el.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [locations.length, timeSlots.length]);

  const handleDayChange = (day) => {
    onChange({ ...value, day });
  };

  const handleCellChange = (time, location, field, val) => {
    const newGrid = { ...gridData };
    if (!newGrid[time]) newGrid[time] = {};
    if (!newGrid[time][location]) newGrid[time][location] = { topic: '', subbatches: [] };

    newGrid[time][location] = {
      ...newGrid[time][location],
      [field]: val,
    };
    onChange({ ...value, grid: newGrid });
  };

  const toggleSubbatch = (time, location, subbatch) => {
    const current = gridData[time]?.[location]?.subbatches || [];
    const next = current.includes(subbatch)
      ? current.filter((s) => s !== subbatch)
      : [...current, subbatch];
    handleCellChange(time, location, 'subbatches', next);
  };

  const clearCellBatches = (time, location) => {
    handleCellChange(time, location, 'subbatches', []);
  };

  const clearCurrentDayGrid = () => {
    if (window.confirm(`Are you sure you want to clear all scheduled slots for ${selectedDay}?`)) {
      onChange({ ...value, grid: {} });
    }
  };

  // Count how many slots on current day have content
  const countScheduledSlots = () => {
    let count = 0;
    timeSlots.forEach((time) => {
      locations.forEach((loc) => {
        const cell = gridData[time]?.[loc];
        if (cell && (cell.topic?.trim() || (cell.subbatches && cell.subbatches.length > 0))) {
          count++;
        }
      });
    });
    return count;
  };

  const scheduledSlotsCount = countScheduledSlots();
  const totalSlots = timeSlots.length * locations.length;

  const getBatchChipClass = (groupKey) => {
    const k = groupKey.toUpperCase();
    if (k === 'A') return 'batch-a';
    if (k === 'B') return 'batch-b';
    if (k === 'C') return 'batch-c';
    if (k === 'D') return 'batch-d';
    if (k === 'E') return 'batch-e';
    return 'batch-custom';
  };

  return (
    <div className="schedule-grid-builder">
      {/* Top Header: Day Pill Navigation & Dynamic Controls */}
      <div className="builder-top-bar">
        <div className="day-pills-bar" role="tablist" aria-label="Select schedule day">
          {weekdays.map((day) => {
            const isActive = day === selectedDay;
            const shortDay = day.slice(0, 3);
            return (
              <button
                key={day}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`day-pill-btn ${isActive ? 'active' : ''}`}
                onClick={() => handleDayChange(day)}
                disabled={disabled}
              >
                <span className="day-pill-full">{day}</span>
                <span className="day-pill-short">{shortDay}</span>
              </button>
            );
          })}
        </div>

        <div className="builder-top-actions">
          {/* Slot Count Badge */}
          <div className="slot-count-badge" title="Filled slots in timetable">
            <CheckCircle2 size={13} aria-hidden="true" />
            <span>
              <b>{scheduledSlotsCount}</b> / {totalSlots} slots assigned
            </span>
          </div>

          {/* Dynamic Configuration Buttons */}
          <button
            type="button"
            className="config-tool-btn"
            onClick={() => setIsBatchModalOpen(true)}
            disabled={disabled}
            title="Configure dynamic batches and sub-batches"
          >
            <Users size={13} aria-hidden="true" />
            <span>+ Add Batch</span>
          </button>

          <button
            type="button"
            className="config-tool-btn"
            onClick={() => setIsTimeSlotModalOpen(true)}
            disabled={disabled}
            title="Configure dynamic time slots"
          >
            <Clock size={13} aria-hidden="true" />
            <span>+ Add Time Slot</span>
          </button>

          {scheduledSlotsCount > 0 && (
            <button
              type="button"
              className="clear-day-btn"
              onClick={clearCurrentDayGrid}
              disabled={disabled}
              title={`Clear all slots for ${selectedDay}`}
            >
              <Trash2 size={13} aria-hidden="true" />
              <span>Clear {selectedDay}</span>
            </button>
          )}
        </div>
      </div>

      {/* Helper Bar */}
      <div className="builder-helper-bar">
        <div className="builder-instructions">
          <Users size={14} className="helper-icon" aria-hidden="true" />
          <span>
            Select individual sub-batches (A1–C4...) for each scheduled lab slot across 5 working days.
          </span>
        </div>
        <div className="batch-legend">
          {batchGroupKeys.map((k) => (
            <span key={k} className={`legend-item ${getBatchChipClass(k)}`}>
              <span className="legend-dot" /> Batch {k}
            </span>
          ))}
        </div>
      </div>

      {/* Main Timetable Table Container */}
      <div
        className={`grid-scroll-container ${isScrolling ? 'is-scrolling' : ''}`}
        ref={scrollRef}
      >
        <table className="schedule-builder-table">
          <colgroup>
            <col style={{ width: '155px', minWidth: '155px' }} />
            {locations.map((loc) => (
              <col key={loc} style={{ width: '145px', minWidth: '145px' }} />
            ))}
          </colgroup>
          <thead>
            <tr>
              <th className="sticky-col time-header-th">
                <div className="th-content">
                  <Clock size={13} aria-hidden="true" />
                  <span>Time / Lab</span>
                </div>
              </th>
              {locations.map((loc) => {
                const meta = getLocationMeta(loc);
                return (
                  <th key={loc} className="lab-header-th">
                    <div className="lab-header-inner">
                      <span className="lab-name">{loc}</span>
                      <span className="lab-badge">{meta.badge}</span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((time) => (
              <tr key={time}>
                <td className="time-cell sticky-col">
                  <div className="time-cell-inner">
                    <Clock size={14} className="time-icon" aria-hidden="true" />
                    <span className="time-label">{time}</span>
                  </div>
                </td>
                {locations.map((loc) => {
                  const cell = gridData[time]?.[loc] || { topic: '', subbatches: [] };
                  const subbatches = cell.subbatches || [];
                  const hasContent = Boolean(cell.topic?.trim() || subbatches.length > 0);

                  return (
                    <td key={loc} className={`content-cell ${hasContent ? 'has-content' : ''}`}>
                      <div className="cell-inner">
                        {/* Topic Input with Icon */}
                        <div className="cell-topic-wrapper">
                          <BookOpen size={13} className="topic-field-icon" aria-hidden="true" />
                          <input
                            type="text"
                            placeholder="Enter lab topic / subject..."
                            value={cell.topic || ''}
                            onChange={(e) => handleCellChange(time, loc, 'topic', e.target.value)}
                            disabled={disabled}
                            className="topic-input"
                            aria-label={`${time} in ${loc} topic`}
                          />
                        </div>

                        {/* Sub-batch Header with Selected Count & Clear action */}
                        {subbatches.length > 0 && (
                          <div className="cell-subbatch-bar">
                            <span className="selected-count-badge">
                              {subbatches.length} {subbatches.length === 1 ? 'batch' : 'batches'}
                            </span>
                            <button
                              type="button"
                              className="clear-cell-btn"
                              onClick={() => clearCellBatches(time, loc)}
                              disabled={disabled}
                              title="Clear selected sub-batches"
                            >
                              Clear
                            </button>
                          </div>
                        )}

                        {/* Individual Sub-batch Chips Organized by Batch Groups */}
                        <div className="subbatch-selector">
                          {batchGroupKeys.map((groupKey) => {
                            const groupSubs = batchGroups[groupKey] || [];
                            const chipClass = getBatchChipClass(groupKey);

                            return (
                              <div key={groupKey} className={`sb-row ${chipClass}-row`}>
                                {groupSubs.map((sb) => {
                                  const isActive = subbatches.includes(sb);
                                  return (
                                    <button
                                      key={sb}
                                      type="button"
                                      className={`sb-chip ${chipClass} ${isActive ? 'active' : ''}`}
                                      onClick={() => toggleSubbatch(time, loc, sb)}
                                      disabled={disabled}
                                      title={`Toggle ${sb.toUpperCase()}`}
                                    >
                                      {sb.toUpperCase()}
                                    </button>
                                  );
                                })}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Batch Management Modal */}
      <BatchManagerModal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        config={config}
        onAddBatch={onAddBatch}
        onRemoveBatch={onRemoveBatch}
        onAddSubBatch={onAddSubBatch}
        onRemoveSubBatch={onRemoveSubBatch}
      />

      {/* Time Slot Management Modal */}
      <TimeSlotManagerModal
        isOpen={isTimeSlotModalOpen}
        onClose={() => setIsTimeSlotModalOpen(false)}
        config={config}
        onAddTimeSlot={onAddTimeSlot}
        onEditTimeSlot={onEditTimeSlot}
        onRemoveTimeSlot={onRemoveTimeSlot}
      />
    </div>
  );
}
