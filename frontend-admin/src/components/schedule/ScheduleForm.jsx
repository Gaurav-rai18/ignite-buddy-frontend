import React, { useState, useEffect } from 'react';
import { CalendarClock, Link2, Users } from 'lucide-react';
import { Field } from '../ui/Field';
import { VALIDATION_LIMITS } from '../../constants';
import { usersService } from '../../services/usersService';

export function ScheduleForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onCancel,
  onSubmit,
}) {
  const [cohorts, setCohorts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [subBatches, setSubBatches] = useState([]);

  useEffect(() => {
    usersService.getCohorts().then(setCohorts).catch(() => setCohorts([]));
    usersService.getBatches().then(setBatches).catch(() => setBatches([]));
    usersService.getSubBatches().then(setSubBatches).catch(() => setSubBatches([]));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const targetType = form.target_type || 'ALL';

  const isFormIncomplete =
    !form.title.trim() ||
    !form.onedrive_url.trim() ||
    !form.publish_date ||
    !form.publish_time ||
    (targetType === 'COHORT' && !form.target_cohort) ||
    (targetType === 'BATCH' && !form.target_batch) ||
    (targetType === 'SUB_BATCH' && !form.target_sub_batch);

  const todayDate = new Date().toISOString().slice(0, 10);

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h3>New scheduled item</h3>
          <p>The link, target audience, and publish time will be saved in the database.</p>
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
            placeholder="e.g. Semester 5 notes or Lab Schedule"
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
              placeholder="https://1drv.ms/... or https://onedrive.live.com/..."
              value={form.onedrive_url}
              onChange={(e) => onChangeField('onedrive_url', e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(formErrors.onedrive_url)}
            />
          </div>
        </Field>

        <div className="field">
          <span>Target audience</span>
          <select
            value={targetType}
            onChange={(e) => {
              onChangeField('target_type', e.target.value);
              onChangeField('target_cohort', '');
              onChangeField('target_batch', '');
              onChangeField('target_sub_batch', '');
            }}
            disabled={isSubmitting}
          >
            <option value="ALL">All Cohorts (Campus-wide)</option>
            <option value="COHORT">Specific Cohort</option>
            <option value="BATCH">Specific Batch</option>
            <option value="SUB_BATCH">Specific Sub-Batch</option>
          </select>
        </div>

        {targetType === 'COHORT' && (
          <Field label="Select Cohort" htmlFor="schedule-cohort">
            <select
              id="schedule-cohort"
              value={form.target_cohort || ''}
              onChange={(e) => onChangeField('target_cohort', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a cohort...</option>
              {cohorts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </Field>
        )}

        {targetType === 'BATCH' && (
          <Field label="Select Batch" htmlFor="schedule-batch">
            <select
              id="schedule-batch"
              value={form.target_batch || ''}
              onChange={(e) => onChangeField('target_batch', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a batch...</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.cohort_code ? `${b.cohort_code} - ` : ''}Batch {b.name}
                </option>
              ))}
            </select>
          </Field>
        )}

        {targetType === 'SUB_BATCH' && (
          <Field label="Select Sub-Batch" htmlFor="schedule-sub-batch">
            <select
              id="schedule-sub-batch"
              value={form.target_sub_batch || ''}
              onChange={(e) => onChangeField('target_sub_batch', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a sub-batch...</option>
              {subBatches.map((sb) => (
                <option key={sb.id} value={sb.id}>
                  {sb.full_code || `${sb.cohort_code || ''} Batch ${sb.batch_name || ''} - Sub-Batch ${sb.name}`}
                </option>
              ))}
            </select>
          </Field>
        )}

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
              Resources are published to trainee desktop assistants for the selected audience on the chosen date and time.
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
