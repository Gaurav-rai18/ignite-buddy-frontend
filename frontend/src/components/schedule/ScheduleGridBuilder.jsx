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
} from 'lucide-react';
import { SCHEDULE_TIME_SLOTS, SCHEDULE_LOCATIONS, SCHEDULE_DAYS } from '../../constants';

const LAB_METADATA = {
  'Lab 1': { badge: 'Hardware', color: '#014BAA' },
  'Lab 2': { badge: 'Software', color: '#0284C7' },
  'Lab 3': { badge: 'Data & AI', color: '#7C3AED' },
  'Lab 4': { badge: 'Cloud Ops', color: '#059669' },
  'Incubator': { badge: 'Project Hall', color: '#D97706' },
};

const BATCH_GROUPS = {
  A: ['a1', 'a2', 'a3', 'a4'],
  B: ['b1', 'b2', 'b3', 'b4'],
  C: ['c1', 'c2', 'c3', 'c4'],
};

export function ScheduleGridBuilder({ value, onChange, disabled }) {
  const gridData = value?.grid || {};
  const selectedDay = value?.day || 'Monday';
  const scrollRef = useRef(null);
  const [isScrolling, setIsScrolling] = useState(false);

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
  }, []);

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

  const toggleBatchGroup = (time, location, groupKey) => {
    const groupItems = BATCH_GROUPS[groupKey] || [];
    const current = gridData[time]?.[location]?.subbatches || [];
    const allSelected = groupItems.every((item) => current.includes(item));

    let next;
    if (allSelected) {
      // Unselect all in this group
      next = current.filter((item) => !groupItems.includes(item));
    } else {
      // Add all missing in this group
      const additions = groupItems.filter((item) => !current.includes(item));
      next = [...current, ...additions];
    }
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
    SCHEDULE_TIME_SLOTS.forEach((time) => {
      SCHEDULE_LOCATIONS.forEach((loc) => {
        const cell = gridData[time]?.[loc];
        if (cell && (cell.topic?.trim() || (cell.subbatches && cell.subbatches.length > 0))) {
          count++;
        }
      });
    });
    return count;
  };

  const scheduledSlotsCount = countScheduledSlots();
  const totalSlots = SCHEDULE_TIME_SLOTS.length * SCHEDULE_LOCATIONS.length;

  return (
    <div className="schedule-grid-builder">
      {/* Top Header: Day Pill Navigation & Actions */}
      <div className="builder-top-bar">
        <div className="day-pills-bar" role="tablist" aria-label="Select schedule day">
          {SCHEDULE_DAYS.map((day) => {
            const isActive = day === selectedDay;
            // Short label for smaller screens
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
          <div className="slot-count-badge" title="Filled slots in timetable">
            <CheckCircle2 size={13} aria-hidden="true" />
            <span>
              <b>{scheduledSlotsCount}</b> / {totalSlots} slots assigned
            </span>
          </div>

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
            Click <b>All A / B / C</b> to assign an entire batch group, or toggle individual sub-batches (A1–C4).
          </span>
        </div>
        <div className="batch-legend">
          <span className="legend-item batch-a"><span className="legend-dot" /> Batch A</span>
          <span className="legend-item batch-b"><span className="legend-dot" /> Batch B</span>
          <span className="legend-item batch-c"><span className="legend-dot" /> Batch C</span>
        </div>
      </div>

      {/* Main Timetable Table Container */}
      <div
        className={`grid-scroll-container ${isScrolling ? 'is-scrolling' : ''}`}
        ref={scrollRef}
      >
        <table className="schedule-builder-table">
          <thead>
            <tr>
              <th className="sticky-col time-header-th">
                <div className="th-content">
                  <Clock size={13} aria-hidden="true" />
                  <span>Time / Lab</span>
                </div>
              </th>
              {SCHEDULE_LOCATIONS.map((loc) => {
                const meta = LAB_METADATA[loc] || { badge: 'Lab', color: '#014BAA' };
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
            {SCHEDULE_TIME_SLOTS.map((time) => (
              <tr key={time}>
                <td className="time-cell sticky-col">
                  <div className="time-cell-inner">
                    <Clock size={14} className="time-icon" aria-hidden="true" />
                    <span className="time-label">{time}</span>
                  </div>
                </td>
                {SCHEDULE_LOCATIONS.map((loc) => {
                  const cell = gridData[time]?.[loc] || { topic: '', subbatches: [] };
                  const subbatches = cell.subbatches || [];
                  const hasContent = Boolean(cell.topic?.trim() || subbatches.length > 0);

                  const isGroupAAll = BATCH_GROUPS.A.every((s) => subbatches.includes(s));
                  const isGroupBAll = BATCH_GROUPS.B.every((s) => subbatches.includes(s));
                  const isGroupCAll = BATCH_GROUPS.C.every((s) => subbatches.includes(s));

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

                        {/* Batch Quick-Actions (All A, All B, All C, Clear) */}
                        <div className="batch-presets-bar">
                          <button
                            type="button"
                            className={`batch-preset-btn batch-a ${isGroupAAll ? 'active' : ''}`}
                            onClick={() => toggleBatchGroup(time, loc, 'A')}
                            disabled={disabled}
                            title="Toggle all Batch A sub-batches (A1-A4)"
                          >
                            {isGroupAAll ? '✓ All A' : '+ All A'}
                          </button>
                          <button
                            type="button"
                            className={`batch-preset-btn batch-b ${isGroupBAll ? 'active' : ''}`}
                            onClick={() => toggleBatchGroup(time, loc, 'B')}
                            disabled={disabled}
                            title="Toggle all Batch B sub-batches (B1-B4)"
                          >
                            {isGroupBAll ? '✓ All B' : '+ All B'}
                          </button>
                          <button
                            type="button"
                            className={`batch-preset-btn batch-c ${isGroupCAll ? 'active' : ''}`}
                            onClick={() => toggleBatchGroup(time, loc, 'C')}
                            disabled={disabled}
                            title="Toggle all Batch C sub-batches (C1-C4)"
                          >
                            {isGroupCAll ? '✓ All C' : '+ All C'}
                          </button>

                          {subbatches.length > 0 && (
                            <button
                              type="button"
                              className="batch-preset-btn clear"
                              onClick={() => clearCellBatches(time, loc)}
                              disabled={disabled}
                              title="Clear all sub-batches for this cell"
                            >
                              Clear
                            </button>
                          )}
                        </div>

                        {/* Sub-batch Chips Grid (Organized in 3 clear rows for Batch A, B, C) */}
                        <div className="subbatch-selector">
                          {/* Row A */}
                          <div className="sb-row batch-a-row">
                            {BATCH_GROUPS.A.map((sb) => {
                              const isActive = subbatches.includes(sb);
                              return (
                                <button
                                  key={sb}
                                  type="button"
                                  className={`sb-chip batch-a ${isActive ? 'active' : ''}`}
                                  onClick={() => toggleSubbatch(time, loc, sb)}
                                  disabled={disabled}
                                  title={`Toggle ${sb.toUpperCase()}`}
                                >
                                  {sb.toUpperCase()}
                                </button>
                              );
                            })}
                          </div>

                          {/* Row B */}
                          <div className="sb-row batch-b-row">
                            {BATCH_GROUPS.B.map((sb) => {
                              const isActive = subbatches.includes(sb);
                              return (
                                <button
                                  key={sb}
                                  type="button"
                                  className={`sb-chip batch-b ${isActive ? 'active' : ''}`}
                                  onClick={() => toggleSubbatch(time, loc, sb)}
                                  disabled={disabled}
                                  title={`Toggle ${sb.toUpperCase()}`}
                                >
                                  {sb.toUpperCase()}
                                </button>
                              );
                            })}
                          </div>

                          {/* Row C */}
                          <div className="sb-row batch-c-row">
                            {BATCH_GROUPS.C.map((sb) => {
                              const isActive = subbatches.includes(sb);
                              return (
                                <button
                                  key={sb}
                                  type="button"
                                  className={`sb-chip batch-c ${isActive ? 'active' : ''}`}
                                  onClick={() => toggleSubbatch(time, loc, sb)}
                                  disabled={disabled}
                                  title={`Toggle ${sb.toUpperCase()}`}
                                >
                                  {sb.toUpperCase()}
                                </button>
                              );
                            })}
                          </div>
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
    </div>
  );
}
