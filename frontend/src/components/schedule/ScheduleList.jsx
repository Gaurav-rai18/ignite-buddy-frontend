/*
  ScheduleList Component
  ----------------------
  Displays a table/list of existing schedules fetched via `useSchedules` hook.
  Provides actions to edit, preview, or delete a schedule entry.
*/

import React from 'react';, { useState } from 'react';
import {
  CalendarClock,
  Link2,
  Clock3,
  ExternalLink,
  Grid3X3,
  FileSpreadsheet,
  Eye,
  Trash2,
  Calendar,
} from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';
import { isValidHttpsUrl } from '../../utils/validation';
import { SchedulePreviewModal } from './SchedulePreviewModal';
import { DeleteScheduleDialog } from './DeleteScheduleDialog';

export function ScheduleList({
  schedules = [],
  loading = false,
  onCreateClick,
  onDeleteSchedule,
  config,
}) {
  const [previewItem, setPreviewItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirmDelete = async () => {
    if (!deleteItem || !onDeleteSchedule) return;
    setIsDeleting(true);
    try {
      await onDeleteSchedule(deleteItem.id);
      setDeleteItem(null);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <section className="panel list-panel schedule-list-panel">
      {/* Panel Heading */}
      <div className="panel-heading">
        <div>
          <h3>Upcoming schedule</h3>
          <p>Saved timetables and their publish times</p>
        </div>
        <span className="count-badge" aria-label={`${schedules.length} schedules`}>
          {schedules.length}
        </span>
      </div>

      {loading && schedules.length === 0 ? (
        <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '11.5px' }}>
          Loading schedules...
        </div>
      ) : schedules.length > 0 ? (
        <div className="schedule-cards-list">
          {schedules.map((item) => {
            let contentData = null;
            try {
              contentData = typeof item.content_data === 'string'
                ? JSON.parse(item.content_data)
                : item.content_data;
            } catch (e) {
              console.error('Failed to parse schedule content_data', e);
            }

            const isExcel = item.schedule_type === 'excel' || Boolean(item.excel_file || item.file_name);
            const isGrid = Boolean(contentData) && !isExcel;
            const isSafeUrl = isValidHttpsUrl(item.onedrive_url);
            const day = contentData?.day || 'Weekly';

            return (
              <article className="list-entry schedule-card-item" key={item.id}>
                <div className="entry-top">
                  <span
                    className={`entry-icon ${isExcel ? 'excel-icon' : isGrid ? 'grid-icon' : 'link-icon'}`}
                    aria-hidden="true"
                  >
                    {isExcel ? <FileSpreadsheet size={15} /> : isGrid ? <Grid3X3 size={15} /> : <Link2 size={15} />}
                  </span>

                  <span className="schedule-type-badge">
                    {isExcel ? 'Excel Schedule' : isGrid ? `${day} Grid` : 'OneDrive Resource'}
                  </span>

                  <span className="scheduled-tag">
                    <Clock3 size={11} aria-hidden="true" /> Scheduled
                  </span>
                </div>

                <h4 className="schedule-item-title">{item.title}</h4>

                <div className="schedule-item-content">
                  {contentData ? (
                    <button
                      type="button"
                      className="view-grid-btn"
                      onClick={() => setPreviewItem(item)}
                      title="Preview full timetable schedule"
                    >
                      <Eye size={13} aria-hidden="true" />
                      <span>{isExcel ? 'View Excel Timetable' : 'View Timetable Grid'}</span>
                    </button>
                  ) : isSafeUrl ? (
                    <a
                      className="external-link"
                      href={item.onedrive_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open OneDrive link <ExternalLink size={12} aria-hidden="true" />
                    </a>
                  ) : (
                    <span className="external-link" style={{ opacity: 0.6 }}>
                      (No content preview available)
                    </span>
                  )}
                </div>

                <div className="entry-meta schedule-card-footer">
                  <span className="publish-time-info">
                    <CalendarClock size={13} aria-hidden="true" />
                    Publish: {formatDate(item.publish_at)}
                  </span>

                  {onDeleteSchedule && (
                    <button
                      type="button"
                      className="schedule-delete-btn"
                      onClick={() => setDeleteItem(item)}
                      title="Delete scheduled item"
                      aria-label={`Delete schedule ${item.title}`}
                    >
                      <Trash2 size={13} aria-hidden="true" />
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={CalendarClock}
          title="No scheduled items yet"
          text="Create a schedule to publish a native timetable grid or upload an Excel timetable."
          action={onCreateClick ? 'Create schedule' : undefined}
          onClick={onCreateClick}
        />
      )}

      {/* Timetable Preview Modal */}
      <SchedulePreviewModal
        isOpen={Boolean(previewItem)}
        onClose={() => setPreviewItem(null)}
        schedule={previewItem}
        config={config}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteScheduleDialog
        isOpen={Boolean(deleteItem)}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleConfirmDelete}
        schedule={deleteItem}
        isDeleting={isDeleting}
      />
    </section>
  );
}
