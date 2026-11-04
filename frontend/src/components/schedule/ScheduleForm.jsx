/**
 * ScheduleForm.jsx — Timetable Creation Form with Mode Switcher & Publish Controls.
 *
 * Provides:
 *  - Mode switcher tab bar:
 *      • 'grid'  -> Native Timetable Grid (interactive table with dynamic batch chips)
 *      • 'excel' -> Excel File Upload (drag-and-drop .xlsx parser with preview)
 *      • 'link'  -> Legacy OneDrive URL sharing
 *  - Common metadata: Schedule Title (max 160 chars)
 *  - Unified Timetable Preview component (displays all configured slots for both grid & Excel)
 *  - Publishing Schedule settings: date picker (min = today), time picker,
 *    and quick shortcuts (Today, Tomorrow, Next Week).
 *  - Submits via JSON (grid) or multipart FormData (Excel) to Django backend.
 */

import React, { useState } from 'react';
import {
  CalendarClock,
  Link2,
  Grid3X3,
  Calendar,
  Clock,
  FileSpreadsheet,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { Field } from '../ui/Field';
import { VALIDATION_LIMITS } from '../../constants';
import { ScheduleGridBuilder } from './ScheduleGridBuilder';
import { ExcelUpload } from './ExcelUpload';
import { UnifiedTimetablePreview } from './UnifiedTimetablePreview';

export function ScheduleForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onCancel,
  onSubmit,
  activeTab: controlledTab,
  onTabChange: setControlledTab,
  config,
  onAddBatch,
  onRemoveBatch,
  onAddSubBatch,
  onRemoveSubBatch,
  onAddTimeSlot,
  onEditTimeSlot,
  onRemoveTimeSlot,
  onExcelSelect,
  onExcelRemove,
}) {
  const initialActive = controlledTab !== undefined
    ? controlledTab
    : form.schedule_type === 'excel' || form.excel_file
    ? 'excel'
    : form.schedule_type === 'grid'
    ? 'grid'
    : form.content_data
    ? 'grid'
    : form.onedrive_url !== undefined
    ? 'link'
    : 'grid';

  const [internalTab, setInternalTab] = useState(initialActive);

  const activeTab = controlledTab !== undefined ? controlledTab : internalTab;

  const handleTabChange = (tab) => {
    if (setControlledTab) {
      setControlledTab(tab);
    } else {
      setInternalTab(tab);
    }
    onChangeField('schedule_type', tab);
    if (tab === 'grid' && !form.content_data) {
      onChangeField('content_data', { day: 'Monday', grid: {} });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const isGridEmpty = () => {
    if (!form.content_data?.grid) return true;
    const entries = Object.values(form.content_data.grid).flatMap((timeSlot) =>
      Object.values(timeSlot)
    );
    return entries.length === 0 || entries.every((cell) => !cell.topic?.trim() && (!cell.subbatches || cell.subbatches.length === 0));
  };

  const isFormIncomplete =
    !form.title.trim() ||
    (activeTab === 'link'
      ? !form.onedrive_url.trim()
      : activeTab === 'excel'
      ? !form.excel_file && isGridEmpty()
      : isGridEmpty()) ||
    !form.publish_date ||
    !form.publish_time;

  const todayDate = new Date().toISOString().slice(0, 10);

  const setDateShortcut = (offsetDays) => {
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    const dateStr = d.toISOString().slice(0, 10);
    onChangeField('publish_date', dateStr);
    if (!form.publish_time) {
      onChangeField('publish_time', '09:00');
    }
  };

  const handleExcelFileSelect = (excelDetails) => {
    if (onExcelSelect) {
      onExcelSelect(excelDetails);
    } else {
      onChangeField('excel_file', excelDetails.file);
      onChangeField('excel_file_name', excelDetails.fileName);
      onChangeField('excel_file_size', excelDetails.fileSize);
      if (excelDetails.parsedData) {
        onChangeField('content_data', {
          day: excelDetails.parsedData.selected_day || 'Monday',
          grid: excelDetails.parsedData.grid || {},
          days_data: excelDetails.parsedData.days_data || {},
        });
      }
    }
  };

  const handleExcelFileRemove = () => {
    if (onExcelRemove) {
      onExcelRemove();
    } else {
      onChangeField('excel_file', null);
      onChangeField('excel_file_name', '');
      onChangeField('excel_file_size', null);
      onChangeField('content_data', { day: 'Monday', grid: {} });
    }
  };

  return (
    <section className="panel form-panel schedule-form-panel">
      {/* Panel Heading */}
      <div className="panel-heading">
        <div>
          <h3>Create scheduled item</h3>
          <p>Choose between building a native lab timetable grid or uploading an Excel schedule spreadsheet.</p>
        </div>
        <div className="stat-icon warning" aria-hidden="true">
          <CalendarClock size={18} />
        </div>
      </div>

      {/* Segmented Type Switcher */}
      <div className="schedule-type-toggle" role="tablist" aria-label="Schedule type">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'grid'}
          className={`schedule-type-btn ${activeTab === 'grid' ? 'active' : ''}`}
          onClick={() => handleTabChange('grid')}
        >
          <Grid3X3 size={15} aria-hidden="true" />
          <span className="type-title">Native Timetable Grid</span>
          <span className="type-badge">Interactive</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'excel'}
          className={`schedule-type-btn ${activeTab === 'excel' ? 'active' : ''}`}
          onClick={() => handleTabChange('excel')}
        >
          <FileSpreadsheet size={15} aria-hidden="true" />
          <span className="type-title">Excel File Upload</span>
          <span className="type-badge">Spreadsheet</span>
        </button>

        {/* Backward compatible hidden/conditional link tab if onedrive_url was passed */}
        {activeTab === 'link' && (
          <button
            type="button"
            role="tab"
            aria-selected={true}
            className="schedule-type-btn active"
            onClick={() => handleTabChange('link')}
          >
            <Link2 size={15} aria-hidden="true" />
            <span className="type-title">OneDrive Sharing Link</span>
            <span className="type-badge">URL</span>
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="form-layout" noValidate>
        {/* Schedule Title */}
        <Field
          label="Schedule title"
          htmlFor="schedule-title"
          error={formErrors.title}
          helpText={`Give this timetable or resource an identifiable title (${form.title ? form.title.length : 0}/${VALIDATION_LIMITS.SCHEDULE_TITLE_MAX})`}
        >
          <input
            id="schedule-title"
            required
            maxLength={VALIDATION_LIMITS.SCHEDULE_TITLE_MAX}
            placeholder="e.g. Week 14 Schedule - Batch 50"
            value={form.title}
            onChange={(e) => onChangeField('title', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.title)}
          />
        </Field>

        {/* Dynamic Content based on Active Tab */}
        {activeTab === 'excel' ? (
          <ExcelUpload
            file={form.excel_file}
            fileName={form.excel_file_name}
            fileSize={form.excel_file_size}
            parsedData={form.content_data}
            onFileSelect={handleExcelFileSelect}
            onFileRemove={handleExcelFileRemove}
            disabled={isSubmitting}
          />
        ) : activeTab === 'link' ? (
          <Field
            label="OneDrive sharing link"
            htmlFor="schedule-url"
            error={formErrors.onedrive_url}
            helpText="Ensure the OneDrive resource URL has proper viewing permissions for students."
          >
            <div className="input-with-icon">
              <Link2 size={16} aria-hidden="true" />
              <input
                id="schedule-url"
                required
                type="url"
                placeholder="https://1drv.ms/..."
                value={form.onedrive_url}
                onChange={(e) => onChangeField('onedrive_url', e.target.value)}
                disabled={isSubmitting}
                aria-invalid={Boolean(formErrors.onedrive_url)}
              />
            </div>
          </Field>
        ) : (
          <div className="grid-builder-container">
            <div className="grid-builder-label-row">
              <label className="field-label" style={{ display: 'block', fontSize: '12px', fontWeight: '700' }}>
                Schedule Grid Builder
              </label>
              <span className="grid-builder-hint">
                Plan lab topics and assign sub-batches across all 7 locations
              </span>
            </div>
            <ScheduleGridBuilder
              value={form.content_data}
              onChange={(val) => onChangeField('content_data', val)}
              disabled={isSubmitting}
              config={config}
              onAddBatch={onAddBatch}
              onRemoveBatch={onRemoveBatch}
              onAddSubBatch={onAddSubBatch}
              onRemoveSubBatch={onRemoveSubBatch}
              onAddTimeSlot={onAddTimeSlot}
              onEditTimeSlot={onEditTimeSlot}
              onRemoveTimeSlot={onRemoveTimeSlot}
            />
          </div>
        )}

        {/* Unified Timetable Preview (shows all schedule data for both Native Grid & Excel Upload) */}
        <UnifiedTimetablePreview
          contentData={form.content_data}
          config={config}
          title={form.title}
        />

        {/* Publish Date & Time Settings */}
        <div className="publish-settings-card">
          <div className="publish-settings-head">
            <CalendarClock size={15} className="text-primary" aria-hidden="true" />
            <span>Publishing Schedule</span>
            <div className="quick-date-shortcuts">
              <button
                type="button"
                className="date-shortcut-btn"
                onClick={() => setDateShortcut(0)}
                disabled={isSubmitting}
              >
                Today
              </button>
              <button
                type="button"
                className="date-shortcut-btn"
                onClick={() => setDateShortcut(1)}
                disabled={isSubmitting}
              >
                Tomorrow
              </button>
              <button
                type="button"
                className="date-shortcut-btn"
                onClick={() => setDateShortcut(7)}
                disabled={isSubmitting}
              >
                Next Week
              </button>
            </div>
          </div>

          <div className="date-time-grid">
            <Field
              label="Publish date"
              htmlFor="schedule-date"
              error={formErrors.publish_date}
            >
              <div className="input-with-icon">
                <Calendar size={15} aria-hidden="true" />
                <input
                  id="schedule-date"
                  required
                  type="date"
                  min={todayDate}
                  value={form.publish_date}
                  onChange={(e) => onChangeField('publish_date', e.target.value)}
                  disabled={isSubmitting}
                  aria-invalid={Boolean(formErrors.publish_date)}
                />
              </div>
            </Field>

            <Field
              label="Publish time"
              htmlFor="schedule-time"
              error={formErrors.publish_time}
            >
              <div className="input-with-icon">
                <Clock size={15} aria-hidden="true" />
                <input
                  id="schedule-time"
                  required
                  type="time"
                  value={form.publish_time}
                  onChange={(e) => onChangeField('publish_time', e.target.value)}
                  disabled={isSubmitting}
                  aria-invalid={Boolean(formErrors.publish_time)}
                />
              </div>
            </Field>
          </div>
        </div>

        {/* Note Callout */}
        <div className="schedule-note">
          <CalendarClock size={16} color="var(--color-primary)" aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>
            <b>Automated scheduling</b>
            <small>
              Your schedule is stored safely. Upon reaching the chosen date and time, the timetable becomes accessible to campus students.
            </small>
          </span>
        </div>

        {/* Form Footer Actions */}
        <div className="form-foot">
          <span className="foot-resource-indicator">
            {activeTab === 'excel' ? (
              <><FileSpreadsheet size={14} aria-hidden="true" /> Excel spreadsheet timetable</>
            ) : activeTab === 'link' ? (
              <><Link2 size={14} aria-hidden="true" /> OneDrive resource</>
            ) : (
              <><Grid3X3 size={14} aria-hidden="true" /> Native timetable grid</>
            )}
          </span>

          <div className="form-foot-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
              disabled={isSubmitting || (!form.title && !form.onedrive_url && !form.excel_file && !form.publish_date && !form.publish_time && isGridEmpty())}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting || isFormIncomplete}
            >
              <CalendarClock size={15} aria-hidden="true" />
              {isSubmitting
                ? 'Saving...'
                : activeTab === 'excel'
                ? 'Publish timetable'
                : activeTab === 'link'
                ? 'Schedule link'
                : 'Save schedule grid'}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
