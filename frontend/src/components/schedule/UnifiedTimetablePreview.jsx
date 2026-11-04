/**
 * UnifiedTimetablePreview.jsx — Unified Read-Only Timetable Preview.
 *
 * Displays a live, responsive preview of the complete timetable across all
 * 7 locations and Monday–Friday working days, regardless of whether the schedule
 * is being created via the Native Timetable Grid or uploaded via an Excel spreadsheet.
 *
 * Supports:
 *  - Single-day data from `contentData.grid` (native grid builder).
 *  - Multi-day data from `contentData.days_data` (Excel parser output).
 *  - Day tabs with real-time slot counter badges.
 *  - Shows lab topic and colored sub-batch chips in assigned cells.
 *  - Empty state when no schedule entries exist.
 */

import React, { useState } from 'react';
import {
  Eye,
  Clock,
  BookOpen,
  Calendar,
  CheckCircle2,
  CalendarClock,
  Layers,
} from 'lucide-react';
import {
  DEFAULT_SCHEDULE_LOCATIONS,
  DEFAULT_SCHEDULE_DAYS,
  DEFAULT_SCHEDULE_TIME_SLOTS,
} from '../../constants';

export function UnifiedTimetablePreview({ contentData, config, title }) {
  const weekdays =
    config?.weekdays?.length > 0
      ? config.weekdays.map((w) => (typeof w === 'string' ? w : w.name)).filter((d) => !['Saturday', 'Sunday'].includes(d))
      : DEFAULT_SCHEDULE_DAYS;

  const locations =
    config?.locations?.length > 0
      ? config.locations.map((l) => (typeof l === 'string' ? l : l.name))
      : DEFAULT_SCHEDULE_LOCATIONS;

  const [activeDay, setActiveDay] = useState(contentData?.day || weekdays[0] || 'Monday');

  // Multi-day data from Excel upload or single-day from Native Grid
  const daysData = contentData?.days_data || {};
  const currentDayGrid =
    daysData[activeDay] ||
    (contentData?.day === activeDay ? contentData?.grid : {}) ||
    {};

  // Determine all time slots to display
  const gridTimeSlots = Object.keys(currentDayGrid);
  const timeSlots =
    gridTimeSlots.length > 0
      ? gridTimeSlots
      : config?.time_slots?.length > 0
      ? config.time_slots.map((t) => (typeof t === 'string' ? t : t.label || `${t.start_time} – ${t.end_time}`))
      : DEFAULT_SCHEDULE_TIME_SLOTS;

  // Check if current day or any day has scheduled content
  const countAssignedSlots = (grid) => {
    let count = 0;
    Object.values(grid || {}).forEach((locs) => {
      Object.values(locs || {}).forEach((cell) => {
        if (cell?.topic?.trim() || (cell?.subbatches && cell.subbatches.length > 0)) {
          count++;
        }
      });
    });
    return count;
  };

  const currentDayCount = countAssignedSlots(currentDayGrid);

  // Total count across all days
  let totalAllDaysCount = currentDayCount;
  if (Object.keys(daysData).length > 0) {
    totalAllDaysCount = Object.values(daysData).reduce((acc, g) => acc + countAssignedSlots(g), 0);
  } else if (contentData?.grid) {
    totalAllDaysCount = countAssignedSlots(contentData.grid);
  }

  const getBatchChipClass = (sb) => {
    const char = (sb || '').charAt(0).toUpperCase();
    if (char === 'A') return 'batch-a';
    if (char === 'B') return 'batch-b';
    if (char === 'C') return 'batch-c';
    if (char === 'D') return 'batch-d';
    if (char === 'E') return 'batch-e';
    return 'batch-custom';
  };

  return (
    <div className="unified-timetable-preview-card">
      {/* Card Header */}
      <div className="preview-card-header">
        <div className="preview-title-group">
          <span className="preview-icon-badge" aria-hidden="true">
            <Eye size={17} color="var(--color-primary)" />
          </span>
          <div>
            <h4 className="preview-main-title">
              Unified Timetable Preview
              {title?.trim() ? <span className="preview-schedule-title">&bull; {title.trim()}</span> : null}
            </h4>
            <p className="preview-sub-title">
              Live timetable across all {locations.length} locations &bull;{' '}
              {totalAllDaysCount > 0 ? (
                <b>{totalAllDaysCount} total slots configured</b>
              ) : (
                'No slots assigned yet'
              )}
            </p>
          </div>
        </div>

        {/* Day Navigation Tabs */}
        <div className="preview-day-pills-bar" role="tablist" aria-label="Preview working days">
          {weekdays.map((day) => {
            const isSelected = day === activeDay;
            const dayGrid = daysData[day] || (contentData?.day === day ? contentData?.grid : {});
            const daySlotCount = countAssignedSlots(dayGrid);

            return (
              <button
                key={day}
                type="button"
                role="tab"
                aria-selected={isSelected}
                className={`preview-day-pill-btn ${isSelected ? 'active' : ''}`}
                onClick={() => setActiveDay(day)}
              >
                <span>{day}</span>
                {daySlotCount > 0 && <span className="pill-dot-badge">{daySlotCount}</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Preview Table or Informative Empty State */}
      {currentDayCount === 0 && totalAllDaysCount === 0 ? (
        <div className="preview-empty-state">
          <CalendarClock size={32} color="#94A3B8" aria-hidden="true" />
          <h5 className="empty-title">No Timetable Slots Configured Yet</h5>
          <p className="empty-desc">
            Assign topics and sub-batches in the <b>Native Timetable Grid</b> above, or upload an <b>Excel spreadsheet</b> to see your live preview here.
          </p>
        </div>
      ) : (
        <div className="preview-table-scroll-container">
          <table className="schedule-builder-table unified-preview-table">
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
                {locations.map((loc) => (
                  <th key={loc} className="lab-header-th">
                    <div className="lab-header-inner">
                      <span className="lab-name">{loc}</span>
                    </div>
                  </th>
                ))}
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
                    const cell = currentDayGrid[time]?.[loc];
                    const topic = cell?.topic?.trim();
                    const subbatches = Array.isArray(cell?.subbatches) ? cell.subbatches : [];
                    const hasData = Boolean(topic || subbatches.length > 0);

                    return (
                      <td
                        key={loc}
                        className={`content-cell ${hasData ? 'has-content' : 'is-empty'}`}
                      >
                        <div className="cell-inner preview-cell-inner">
                          {hasData ? (
                            <>
                              {topic && (
                                <div className="preview-topic-row">
                                  <BookOpen size={12} color="var(--color-primary)" style={{ flexShrink: 0 }} />
                                  <span className="preview-topic-text">{topic}</span>
                                </div>
                              )}
                              {subbatches.length > 0 && (
                                <div className="preview-chips-row">
                                  {subbatches.map((sb) => (
                                    <span
                                      key={sb}
                                      className={`sb-chip active ${getBatchChipClass(sb)}`}
                                      style={{ pointerEvents: 'none' }}
                                    >
                                      {sb.toUpperCase()}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </>
                          ) : (
                            <span className="preview-unassigned-text">(Unassigned)</span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

