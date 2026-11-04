/*
  BroadcastForm Component
  -----------------------
  Provides a form for creating a new broadcast message.
  Handles form state, validation, and submission to the backend via `broadcastService`.
  On successful submission, it triggers a refresh of the broadcast list and closes the modal.
*/

import React, { useState } from 'react';
import { Megaphone, Users, Send, Eye, AlertTriangle, X } from 'lucide-react';
import { Field } from '../ui/Field';
import {
  VALIDATION_LIMITS,
  RECIPIENT_MODES,
  DEFAULT_RECIPIENT_MODE,
  ROLE_OPTIONS,
  SPECIFIC_RECIPIENTS_SUPPORTED,
} from '../../constants';
import { BroadcastPreviewModal } from './BroadcastPreviewModal';
import { RecipientSelector } from './RecipientSelector';

export function BroadcastForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onSubmit,
  onToggleRecipient,
  onSetRecipients,
}) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const selectedUsers = Array.isArray(form.selectedUsers) ? form.selectedUsers : [];
  const mode = form.recipientMode || DEFAULT_RECIPIENT_MODE;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const recipientReady =
    mode === 'Specific users'
      ? selectedUsers.length > 0 && SPECIFIC_RECIPIENTS_SUPPORTED
      : mode === 'By role'
        ? Boolean(form.role)
        : true;

  const isFormIncomplete = !form.title.trim() || !form.message.trim() || !recipientReady;

  const recipientLabel =
    mode === 'By role'
      ? form.role || 'Select a role'
      : mode === 'Specific users'
        ? `${selectedUsers.length} user${selectedUsers.length === 1 ? '' : 's'}`
        : 'All users';

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h3>Compose announcement</h3>
          <p>Keep your message clear and useful for campus students.</p>
        </div>
        <div className="stat-icon primary" aria-hidden="true">
          <Megaphone size={18} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form-layout" noValidate>
        <Field
          label="Announcement title"
          htmlFor="broadcast-title"
          error={formErrors.title}
        >
          <input
            id="broadcast-title"
            required
            maxLength={VALIDATION_LIMITS.BROADCAST_TITLE_MAX}
            placeholder="e.g. Internal exam timetable released"
            value={form.title}
            onChange={(e) => onChangeField('title', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.title)}
          />
        </Field>

        <div className="field">
          <span>Recipients</span>
          <div
            className="recipient-mode-toggle"
            role="group"
            aria-label="Recipient targeting type"
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
          <Field label="Select role" htmlFor="broadcast-role">
            <select
              id="broadcast-role"
              value={form.role || ''}
              onChange={(e) => onChangeField('role', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Choose a role...</option>
              {ROLE_OPTIONS.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </Field>
        )}

        {mode === 'Specific users' && (
          <>
            {!SPECIFIC_RECIPIENTS_SUPPORTED && (
              <div className="notice-pending" role="note">
                <AlertTriangle size={15} aria-hidden="true" />
                <div>
                  <strong>Requires backend support</strong>
                  <p>
                    The backend Broadcast API cannot store recipients yet, so this will not be
                    delivered. You can still build the recipient list here; publishing stays
                    disabled until the backend adds a recipients field.
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

        <Field
          label="Message"
          htmlFor="broadcast-message"
          error={formErrors.message}
        >
          <textarea
            id="broadcast-message"
            required
            rows={7}
            maxLength={VALIDATION_LIMITS.BROADCAST_MESSAGE_MAX}
            placeholder="Write the complete announcement details here..."
            value={form.message}
            onChange={(e) => onChangeField('message', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.message)}
          />
        </Field>

        <div className="form-foot">
          <span>
            <Users size={14} aria-hidden="true" /> Send to: <b>{recipientLabel}</b>
          </span>

          <div className="form-foot-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => setIsPreviewOpen(true)}
              disabled={isFormIncomplete}
              title="Preview announcement format"
            >
              <Eye size={15} aria-hidden="true" /> Preview
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting || isFormIncomplete}
              title={
                mode === 'Specific users' && !SPECIFIC_RECIPIENTS_SUPPORTED
                  ? 'Specific-user delivery requires backend support'
                  : undefined
              }
            >
              <Send size={15} aria-hidden="true" />
              {isSubmitting ? 'Publishing...' : 'Publish broadcast'}
            </button>
          </div>
        </div>
      </form>

      <BroadcastPreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        form={form}
      />
    </section>
  );
}
