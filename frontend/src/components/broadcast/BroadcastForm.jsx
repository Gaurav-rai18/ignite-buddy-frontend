import React, { useState } from 'react';
import { Megaphone, Users, Send, Eye } from 'lucide-react';
import { Field } from '../ui/Field';
import { AUDIENCE_OPTIONS, VALIDATION_LIMITS } from '../../constants';
import { BroadcastPreviewModal } from './BroadcastPreviewModal';

export function BroadcastForm({
  form,
  formErrors = {},
  isSubmitting = false,
  onChangeField,
  onSubmit,
}) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  const isFormIncomplete = !form.title.trim() || !form.message.trim();

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

        <Field
          label="Audience"
          htmlFor="broadcast-audience"
          error={formErrors.audience}
        >
          <select
            id="broadcast-audience"
            value={form.audience}
            onChange={(e) => onChangeField('audience', e.target.value)}
            disabled={isSubmitting}
            aria-invalid={Boolean(formErrors.audience)}
          >
            {AUDIENCE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </Field>

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
            <Users size={14} aria-hidden="true" /> Visible to: <b>{form.audience}</b>
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
