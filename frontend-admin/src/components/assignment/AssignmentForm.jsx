import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Users,
  Send,
  Eye,
  AlertTriangle,
  X,
  Link,
  Calendar,
  Clock,
} from 'lucide-react';
import { Field } from '../ui/Field';
import {
  VALIDATION_LIMITS,
  RECIPIENT_MODES,
  DEFAULT_RECIPIENT_MODE,
  ROLE_OPTIONS,
  SPECIFIC_RECIPIENTS_SUPPORTED,
} from '../../constants';
import { RecipientSelector } from '../broadcast/RecipientSelector';
import { usersService } from '../../services/usersService';
import { AssignmentPreviewModal } from './AssignmentPreviewModal';

export function AssignmentForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onSubmit,
  onToggleRecipient,
  onSetRecipients,
}) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [cohorts, setCohorts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [subBatches, setSubBatches] = useState([]);

  useEffect(() => {
    usersService.getCohorts().then(setCohorts).catch(() => setCohorts([]));
    usersService.getBatches().then(setBatches).catch(() => setBatches([]));
    usersService.getSubBatches().then(setSubBatches).catch(() => setSubBatches([]));
  }, []);

  const selectedUsers = Array.isArray(form.selectedUsers) ? form.selectedUsers : [];
  const selectedBatchIds = Array.isArray(form.selectedBatchIds)
    ? form.selectedBatchIds
    : form.batch_id ? [form.batch_id] : [];
  const selectedSubBatchIds = Array.isArray(form.selectedSubBatchIds)
    ? form.selectedSubBatchIds
    : form.sub_batch_id ? [form.sub_batch_id] : [];
  const mode = form.recipientMode || DEFAULT_RECIPIENT_MODE;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ publish: true });
  };

  const handleSaveDraft = () => {
    onSubmit({ publish: false });
  };

  const recipientReady =
    mode === 'Specific users'
      ? selectedUsers.length > 0 && SPECIFIC_RECIPIENTS_SUPPORTED
      : mode === 'By role'
        ? Boolean(form.role)
        : mode === 'By cohort'
          ? Boolean(form.cohort_id)
          : mode === 'By batch'
            ? selectedBatchIds.length > 0
            : mode === 'By sub-batch'
              ? selectedSubBatchIds.length > 0
              : true;

  const isFormIncomplete =
    !form.topic.trim() ||
    !form.subject.trim() ||
    !form.start_date ||
    !form.deadline ||
    !form.message.trim() ||
    !recipientReady;

  const recipientLabel =
    mode === 'By role'
      ? form.role || 'Select a role'
      : mode === 'By cohort'
        ? cohorts.find((c) => String(c.id) === String(form.cohort_id))?.code
          ? `Cohort ${cohorts.find((c) => String(c.id) === String(form.cohort_id))?.code}`
          : 'Select a cohort'
        : mode === 'By batch'
          ? selectedBatchIds.length > 0
            ? `${selectedBatchIds.length} batch(es) selected`
            : 'Select batch(es)'
          : mode === 'By sub-batch'
            ? selectedSubBatchIds.length > 0
              ? `${selectedSubBatchIds.length} sub-batch(es) selected`
              : 'Select sub-batch(es)'
            : mode === 'Specific users'
              ? `${selectedUsers.length} user${selectedUsers.length === 1 ? '' : 's'}`
              : 'All users';

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h3>Compose assignment</h3>
          <p>Provide clear details and instructions for your students.</p>
        </div>
        <div className="stat-icon primary" aria-hidden="true">
          <BookOpen size={18} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form-layout" noValidate>
        {/* Topic */}
        <Field label="Topic *" htmlFor="assignment-topic" error={formErrors.topic}>
          <input
            id="assignment-topic"
            required
            maxLength={160}
            placeholder="e.g. Data Structures — Linked Lists"
            value={form.topic}
            onChange={(e) => onChangeField('topic', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.topic)}
          />
        </Field>

        {/* Subject */}
        <Field label="Subject *" htmlFor="assignment-subject" error={formErrors.subject}>
          <input
            id="assignment-subject"
            required
            maxLength={120}
            placeholder="e.g. Computer Science / Java Programming"
            value={form.subject}
            onChange={(e) => onChangeField('subject', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.subject)}
          />
        </Field>

        {/* Platform Link */}
        <Field
          label="Platform Link"
          htmlFor="assignment-platform-link"
          error={formErrors.platform_link}
          helpText="Optional — paste a HackerEarth, LeetCode, Google Classroom, or any assignment URL."
        >
          <div className="input-with-icon">
            <Link size={14} className="input-icon" aria-hidden="true" />
            <input
              id="assignment-platform-link"
              type="url"
              placeholder="https://..."
              value={form.platform_link}
              onChange={(e) => onChangeField('platform_link', e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(formErrors.platform_link)}
              className="input-padded-left"
            />
          </div>
        </Field>

        {/* Start Date & Deadline — two columns */}
        <div className="date-row">
          <Field label="Start Date *" htmlFor="assignment-start-date" error={formErrors.start_date}>
            <div className="input-with-icon">
              <Calendar size={13} className="input-icon" aria-hidden="true" />
              <input
                id="assignment-start-date"
                type="date"
                required
                value={form.start_date}
                onChange={(e) => onChangeField('start_date', e.target.value)}
                disabled={isSubmitting}
                aria-invalid={Boolean(formErrors.start_date)}
                className="input-padded-left"
              />
            </div>
          </Field>

          <Field label="Deadline / End Date *" htmlFor="assignment-deadline" error={formErrors.deadline}>
            <div className="input-with-icon">
              <Clock size={13} className="input-icon" aria-hidden="true" />
              <input
                id="assignment-deadline"
                type="date"
                required
                value={form.deadline}
                onChange={(e) => onChangeField('deadline', e.target.value)}
                disabled={isSubmitting}
                aria-invalid={Boolean(formErrors.deadline)}
                className="input-padded-left"
              />
            </div>
          </Field>
        </div>

        {/* Deadline time — drives the 24h / 1h reminders */}
        <Field
          label="Deadline Time"
          htmlFor="assignment-deadline-time"
          helpText="Used for the automatic 24-hour and 1-hour deadline reminders. Defaults to end of day."
        >
          <div className="input-with-icon">
            <Clock size={13} className="input-icon" aria-hidden="true" />
            <input
              id="assignment-deadline-time"
              type="time"
              value={form.deadline_time || '23:59'}
              onChange={(e) => onChangeField('deadline_time', e.target.value)}
              disabled={isSubmitting}
              className="input-padded-left"
            />
          </div>
        </Field>

        {/* Recipients */}
        <div className="field">
          <span>Recipients</span>
          <div
            className="recipient-mode-toggle"
            role="group"
            aria-label="Recipient targeting type"
            style={{ flexWrap: 'wrap' }}
          >
            {RECIPIENT_MODES.map((option) => (
              <button
                key={option}
                type="button"
                className={`recipient-mode-btn ${mode === option ? 'active' : ''}`}
                aria-pressed={mode === option}
                onClick={() => onChangeField('recipientMode', option)}
                disabled={isSubmitting}
              >
                {option}
              </button>
            ))}
          </div>
          {formErrors.recipients && (
            <span className="field-error-text" role="alert">
              {formErrors.recipients}
            </span>
          )}
        </div>

        {mode === 'By role' && (
          <Field label="Select role" htmlFor="assignment-role">
            <select
              id="assignment-role"
              value={form.role || ''}
              onChange={(e) => onChangeField('role', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a role...</option>
              {ROLE_OPTIONS.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </Field>
        )}

        {mode === 'By cohort' && (
          <Field label="Select TCS Ignite Cohort" htmlFor="assignment-cohort">
            <select
              id="assignment-cohort"
              value={form.cohort_id || ''}
              onChange={(e) => onChangeField('cohort_id', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a cohort...</option>
              {cohorts.map((cohort) => (
                <option key={cohort.id} value={cohort.id}>
                  {cohort.code} - {cohort.name}
                </option>
              ))}
            </select>
          </Field>
        )}

        {mode === 'By batch' && (
          <div className="multi-recipient-picker">
            <div className="picker-header">
              <label className="picker-title">Select Target Major Batch(es) *</label>
              <div className="picker-quick-actions">
                <button
                  type="button"
                  className="btn-quick-link"
                  onClick={() => {
                    const allIds = batches.map((b) => b.id);
                    onChangeField('selectedBatchIds', allIds);
                    onChangeField('batch_id', allIds[0] || '');
                  }}
                >
                  Select All
                </button>
                <button
                  type="button"
                  className="btn-quick-link"
                  onClick={() => {
                    onChangeField('selectedBatchIds', []);
                    onChangeField('batch_id', '');
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="checkable-pills-grid">
              {batches.map((batch) => {
                const isChecked = selectedBatchIds.some((id) => String(id) === String(batch.id));
                return (
                  <label key={batch.id} className={`checkable-pill ${isChecked ? 'active' : ''}`}>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {
                        const next = isChecked
                          ? selectedBatchIds.filter((id) => String(id) !== String(batch.id))
                          : [...selectedBatchIds, batch.id];
                        onChangeField('selectedBatchIds', next);
                        onChangeField('batch_id', next[0] || '');
                      }}
                    />
                    <span>{batch.full_code || `Batch ${batch.name}`}</span>
                  </label>
                );
              })}
            </div>
            {selectedBatchIds.length > 0 && (
              <span className="selection-count-badge">
                {selectedBatchIds.length} batch(es) selected
              </span>
            )}
          </div>
        )}

        {mode === 'By sub-batch' && (
          <div className="multi-recipient-picker">
            <div className="picker-header">
              <label className="picker-title">Select Target Lab Sub-Batch(es) *</label>
              <div className="picker-quick-actions">
                <button
                  type="button"
                  className="btn-quick-link"
                  onClick={() => {
                    const allIds = subBatches.map((sb) => sb.id);
                    onChangeField('selectedSubBatchIds', allIds);
                    onChangeField('sub_batch_id', allIds[0] || '');
                  }}
                >
                  Select All
                </button>
                <button
                  type="button"
                  className="btn-quick-link"
                  onClick={() => {
                    onChangeField('selectedSubBatchIds', []);
                    onChangeField('sub_batch_id', '');
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="checkable-pills-grid">
              {subBatches.map((sb) => {
                const isChecked = selectedSubBatchIds.some((id) => String(id) === String(sb.id));
                return (
                  <label key={sb.id} className={`checkable-pill ${isChecked ? 'active' : ''}`}>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {
                        const next = isChecked
                          ? selectedSubBatchIds.filter((id) => String(id) !== String(sb.id))
                          : [...selectedSubBatchIds, sb.id];
                        onChangeField('selectedSubBatchIds', next);
                        onChangeField('sub_batch_id', next[0] || '');
                      }}
                    />
                    <span>{sb.full_code || sb.name}</span>
                  </label>
                );
              })}
            </div>
            {selectedSubBatchIds.length > 0 && (
              <span className="selection-count-badge">
                {selectedSubBatchIds.length} sub-batch(es) selected
              </span>
            )}
          </div>
        )}

        {mode === 'Specific users' && (
          <>
            {!SPECIFIC_RECIPIENTS_SUPPORTED && (
              <div className="notice-pending" role="note">
                <AlertTriangle size={15} aria-hidden="true" />
                <div>
                  <strong>Requires backend support</strong>
                  <p>
                    The backend Assignment API cannot store recipients yet. You can build
                    the recipient list here; publishing stays disabled until backend support is added.
                  </p>
                </div>
              </div>
            )}
            <RecipientSelector
              selectedUsers={selectedUsers}
              onToggle={onToggleRecipient}
              onSetRecipients={onSetRecipients}
              disabled={isSubmitting}
            />
            {selectedUsers.length > 0 && (
              <div className="recipient-selected-panel">
                <div className="recipient-selected-head">
                  <span>
                    <Users size={13} aria-hidden="true" /> Send to {selectedUsers.length} user
                    {selectedUsers.length === 1 ? '' : 's'}
                  </span>
                </div>
                <div className="recipient-chips">
                  {selectedUsers.map((user) => (
                    <span className="recipient-chip" key={user.id}>
                      {user.username}
                      <button
                        type="button"
                        aria-label={`Remove ${user.username}`}
                        onClick={() => onToggleRecipient && onToggleRecipient(user)}
                        disabled={isSubmitting}
                      >
                        <X size={12} aria-hidden="true" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Assignment Message / Instructions */}
        <Field
          label="Assignment Message / Instructions *"
          htmlFor="assignment-message"
          error={formErrors.message}
        >
          <textarea
            id="assignment-message"
            required
            rows={7}
            maxLength={VALIDATION_LIMITS.BROADCAST_MESSAGE_MAX}
            placeholder="Describe the assignment, include any submission guidelines, expected outputs, or resources..."
            value={form.message}
            onChange={(e) => onChangeField('message', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.message)}
          />
        </Field>

        {/* Form Footer */}
        <div className="form-foot">
          <span>
            <Users size={14} aria-hidden="true" /> Assign to: <b>{recipientLabel}</b>
          </span>
          <div className="form-foot-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => setIsPreviewOpen(true)}
              disabled={isFormIncomplete}
              title="Preview assignment details"
            >
              <Eye size={15} aria-hidden="true" /> Preview
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={handleSaveDraft}
              disabled={isSubmitting || isFormIncomplete}
              title="Save as draft without notifying students"
            >
              Save as draft
            </button>
            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting || isFormIncomplete}
            >
              <Send size={15} aria-hidden="true" />
              {isSubmitting ? 'Publishing...' : 'Publish assignment'}
            </button>
          </div>
        </div>
      </form>

      <AssignmentPreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        form={form}
      />
    </section>
  );
}
