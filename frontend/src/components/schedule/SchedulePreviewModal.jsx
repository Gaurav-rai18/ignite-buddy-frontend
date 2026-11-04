/**
 * @file SchedulePreviewModal.jsx
 * @description Modal dialog previewing a selected schedule item.
 * Displays details (title, type, publish time, content / Excel file) before or after publishing.
 */
import React, { useState, useEffect } from 'react';
import {
  X,
  Calendar,
  Clock,
  MapPin,
  Grid3X3,
  ExternalLink,
  BookOpen,
  Users,
  FileSpreadsheet,
} from 'lucide-react';
import {
  DEFAULT_SCHEDULE_LOCATIONS,
  DEFAULT_SCHEDULE_TIME_SLOTS,
} from '../../constants';
import { formatDate } from '../../utils/date';

export function SchedulePreviewModal({ isOpen, onClose, schedule, config }) {
  const [activeDay, setActiveDay] = useState('');

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !schedule) return null;

  let contentData = null;
  try {
    contentData = typeof schedule.content_data === 'string'
      ? JSON.parse(schedule.content_data)
      : schedule.content_data;
  } catch (e) {
    console.error('Failed to parse schedule content_data', e);
  }

  const isGrid = Boolean(contentData);
  const isExcel = schedule.schedule_type === 'excel' || Boolean(schedule.excel_file || schedule.file_name);
  const isLink = Boolean(schedule.onedrive_url) && !isGrid && !isExcel;

  // Days available in contentData
  const daysData = contentData?.days_data || {};
  const daysKeys = Object.keys(daysData);
  const defaultDay = contentData?.day || (daysKeys.length > 0 ? daysKeys[0] : 'Monday');
  const currentDay = activeDay || defaultDay;

  const currentGrid = daysData[currentDay] || contentData?.grid || {};

  // Dynamic locations from config or discovered in grid
  const locations =
    config?.locations?.length > 0
      ? config.locations.map((l) => (typeof l === 'string' ? l : l.name))
      : DEFAULT_SCHEDULE_LOCATIONS;

  // Dynamic time slots
  const gridTimeSlots = Object.keys(currentGrid);
  const timeSlots =
    gridTimeSlots.length > 0
      ? gridTimeSlots
      : config?.time_slots?.length > 0
      ? config.time_slots.map((t) => (typeof t === 'string' ? t : t.label || `${t.start_time} – ${t.end_time}`))
      : DEFAULT_SCHEDULE_TIME_SLOTS;

  const getBatchClass = (sb) => {
    const char = sb.charAt(0).toLowerCase();
    if (char === 'a') return 'batch-a';
    if (char === 'b') return 'batch-b';
    if (char === 'c') return 'batch-c';
    if (char === 'd') return 'batch-d';
    if (char === 'e') return 'batch-e';
    return '';
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="schedule-preview-title"
      onClick={onClose}
    >
      <div
        className="modal-card schedule-preview-modal"
        style={{ maxWidth: isGrid ? '1060px' : '540px', width: '96%' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              className="entry-icon"
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                display: 'grid',
                placeItems: 'center',
              }}
              aria-hidden="true"
            >
              {isExcel ? <FileSpreadsheet size={18} /> : isGrid ? <Grid3X3 size={18} /> : <ExternalLink size={18} />}
            </span>
            <div>
              <h3 id="schedule-preview-title" style={{ margin: 0, fontSize: '15px' }}>
                {schedule.title}
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                {isExcel
                  ? `Excel Spreadsheet Schedule (${schedule.file_name || 'Uploaded timetable'})`
                  : isGrid
                  ? `${currentDay} Timetable Grid (${locations.length} Locations)`
                  : 'OneDrive Resource'}{' '}
                &bull; Publish: {formatDate(schedule.publish_at)}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close preview modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* Day tabs if schedule has multiple days */}
        {daysKeys.length > 1 && (
          <div style={{ display: 'flex', gap: '6px', margin: '14px 0 0', overflowX: 'auto' }}>
            {daysKeys.map((d) => (
              <button
                key={d}
                type="button"
                className={`preview-day-pill ${d === currentDay ? 'active' : ''}`}
                onClick={() => setActiveDay(d)}
                style={{
                  padding: '4px 12px',
                  borderRadius: '16px',
                  border: '1px solid var(--color-border)',
                  background: d === currentDay ? '#014BAA' : '#FFF',
                  color: d === currentDay ? '#FFF' : 'var(--color-text-primary)',
                  fontSize: '11.5px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                {d}
              </button>
            ))}
          </div>
        )}

        <div className="schedule-preview-body" style={{ marginTop: '16px' }}>
          {isGrid ? (
            <div
              className="preview-grid-wrapper"
              style={{
                overflowX: 'auto',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                maxHeight: '440px',
              }}
            >
              <table
                className="schedule-builder-table schedule-preview-table"
                style={{ width: '100%', minWidth: '1180px' }}
              >
                <colgroup>
                  <col style={{ width: '155px', minWidth: '155px' }} />
                  {locations.map((loc) => (
                    <col key={loc} style={{ width: '145px', minWidth: '145px' }} />
                  ))}
                </colgroup>
                <thead>
                  <tr>
                    <th className="sticky-col time-header-th" style={{ width: '155px' }}>Time / Location</th>
                    {locations.map((loc) => (
                      <th key={loc}>{loc}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {timeSlots.map((time) => (
                    <tr key={time}>
                      <td className="time-cell">
                        <Clock size={13} aria-hidden="true" />
                        <span>{time}</span>
                      </td>
                      {locations.map((loc) => {
                        const cell = currentGrid[time]?.[loc] || { topic: '', subbatches: [] };
                        const hasTopic = Boolean(cell.topic?.trim());
                        const hasBatches = Array.isArray(cell.subbatches) && cell.subbatches.length > 0;
                        const isEmpty = !hasTopic && !hasBatches;

                        return (
                          <td
                            key={loc}
                            style={{
                              padding: '8px',
                              verticalAlign: 'top',
                              background: isEmpty ? 'var(--color-white)' : 'var(--color-primary-light)',
                            }}
                          >
                            {isEmpty ? (
                              <div
                                style={{
                                  color: 'var(--color-text-secondary)',
                                  fontSize: '10.5px',
                                  fontStyle: 'italic',
                                  padding: '6px 4px',
                                }}
                              >
                                Unassigned
                              </div>
                            ) : (
                              <div style={{ display: 'grid', gap: '6px' }}>
                                {hasTopic && (
                                  <div
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '5px',
                                      fontWeight: '700',
                                      fontSize: '11.5px',
                                      color: 'var(--color-text-primary)',
                                    }}
                                  >
                                    <BookOpen size={12} color="var(--color-primary)" />
                                    <span>{cell.topic}</span>
                                  </div>
                                )}
                                {hasBatches && (
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                                    {cell.subbatches.map((sb) => (
                                      <span
                                        key={sb}
                                        className={`sb-chip active ${getBatchClass(sb)}`}
                                        style={{ fontSize: '9px', padding: '2px 5px', pointerEvents: 'none' }}
                                      >
                                        {sb.toUpperCase()}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : isLink ? (
            <div
              style={{
                padding: '16px',
                background: 'var(--color-bg-cream)',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                display: 'grid',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ExternalLink size={16} color="var(--color-primary)" />
                <span style={{ fontSize: '12px', fontWeight: '600' }}>OneDrive Resource URL:</span>
              </div>
              <a
                href={schedule.onedrive_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  wordBreak: 'break-all',
                  fontSize: '12px',
                  color: 'var(--color-primary)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {schedule.onedrive_url}
              </a>
            </div>
          ) : (
            <div
              style={{
                padding: '20px',
                textAlign: 'center',
                color: 'var(--color-text-secondary)',
                fontSize: '12px',
              }}
            >
              No content data available for this schedule item.
            </div>
          )}
        </div>

        <div className="modal-actions" style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
