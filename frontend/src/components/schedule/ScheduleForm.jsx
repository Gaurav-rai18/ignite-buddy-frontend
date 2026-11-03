import React, { useState } from 'react';
import {
  CalendarClock,
  Link2,
  Grid3X3,
  Calendar,
  Clock,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { Field } from '../ui/Field';
import { VALIDATION_LIMITS } from '../../constants';
import { ScheduleGridBuilder } from './ScheduleGridBuilder';

export function ScheduleForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onCancel,
  onSubmit,
  activeTab: controlledTab,
  onTabChange: setControlledTab,
}) {
  const [internalTab, setInternalTab] = useState(form.content_data ? 'grid' : 'link');

  const activeTab = controlledTab !== undefined ? controlledTab : internalTab;

  const handleTabChange = (tab) => {
    if (setControlledTab) {
      setControlledTab(tab);
    } else {
      setInternalTab(tab);
    }
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
    (activeTab === 'link' ? !form.onedrive_url.trim() : isGridEmpty()) ||
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

  return (
    <section className="panel form-panel schedule-form-panel">
      {/* Panel Heading */}
      <div className="panel-heading">
        <div>
          <h3>Create scheduled item</h3>
          <p>Choose between building a native lab timetable grid or scheduling a OneDrive resource.</p>
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
          aria-selected={activeTab === 'link'}
          className={`schedule-type-btn ${activeTab === 'link' ? 'active' : ''}`}
          onClick={() => handleTabChange('link')}
        >
          <Link2 size={15} aria-hidden="true" />
          <span className="type-title">OneDrive Sharing Link</span>
          <span className="type-badge">URL</span>
        </button>
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
        {activeTab === 'link' ? (
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
                Plan lab topics and assign sub-batches for each slot
              </span>
            </div>
            <ScheduleGridBuilder
              value={form.content_data}
              onChange={(val) => onChangeField('content_data', val)}
              disabled={isSubmitting}
            />
          </div>
        )}

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
              Your schedule is stored safely. Upon reaching the chosen date and time, the resource becomes accessible to campus students.
            </small>
          </span>
        </div>

        {/* Form Footer Actions */}
        <div className="form-foot">
          <span className="foot-resource-indicator">
            {activeTab === 'link' ? (
              <><Link2 size={14} aria-hidden="true" /> OneDrive resource</>
            ) : (
              <><Grid3X3 size={14} aria-hidden="true" /> Native timetable data</>
            )}
          </span>

          <div className="form-foot-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
              disabled={isSubmitting || (!form.title && !form.onedrive_url && !form.publish_date && !form.publish_time && !form.content_data)}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting || isFormIncomplete}
            >
              <CalendarClock size={15} aria-hidden="true" />
              {isSubmitting ? 'Saving...' : activeTab === 'link' ? 'Schedule link' : 'Save schedule grid'}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
