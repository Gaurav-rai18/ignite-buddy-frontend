import React from 'react';
import { CalendarClock, Link2 } from 'lucide-react';
import { Field } from '../ui/Field';
import { VALIDATION_LIMITS } from '../../constants';

export function ScheduleForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onCancel,
  onSubmit,
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const isFormIncomplete =
    !form.title.trim() ||
    !form.onedrive_url.trim() ||
    !form.publish_date ||
    !form.publish_time;

  const todayDate = new Date().toISOString().slice(0, 10);

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h3>New scheduled item</h3>
          <p>The link and publish time will be saved in SQLite.</p>
        </div>
        <div className="stat-icon warning" aria-hidden="true">
          <CalendarClock size={18} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form-layout" noValidate>
        <Field
          label="Schedule title"
          htmlFor="schedule-title"
          error={formErrors.title}
        >
          <input
            id="schedule-title"
            required
            maxLength={VALIDATION_LIMITS.SCHEDULE_TITLE_MAX}
            placeholder="e.g. Semester 5 notes"
            value={form.title}
            onChange={(e) => onChangeField('title', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.title)}
          />
        </Field>

        <Field
          label="OneDrive sharing link"
          htmlFor="schedule-url"
          error={formErrors.onedrive_url}
          helpText="Make sure the OneDrive link has the sharing permissions you need."
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

        <div className="date-time-grid">
          <Field
            label="Publish date"
            htmlFor="schedule-date"
            error={formErrors.publish_date}
          >
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
          </Field>

          <Field
            label="Publish time"
            htmlFor="schedule-time"
            error={formErrors.publish_time}
          >
            <input
              id="schedule-time"
              required
              type="time"
              value={form.publish_time}
              onChange={(e) => onChangeField('publish_time', e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(formErrors.publish_time)}
            />
          </Field>
        </div>

        <div className="schedule-note">
          <CalendarClock size={16} color="var(--color-primary)" aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>
            <b>Scheduling note</b>
            <small>
              This starter saves your chosen time. Automatic publishing requires a background scheduler and is not enabled yet.
            </small>
          </span>
        </div>

        <div className="form-foot">
          <span>
            <Link2 size={14} aria-hidden="true" /> OneDrive resource
          </span>

          <div className="form-foot-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
              disabled={isSubmitting || (!form.title && !form.onedrive_url && !form.publish_date && !form.publish_time)}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting || isFormIncomplete}
            >
              <CalendarClock size={15} aria-hidden="true" />
              {isSubmitting ? 'Saving...' : 'Schedule link'}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
