import React from 'react';
import { X, BookOpen, Users, Calendar, Clock, Link } from 'lucide-react';
import { formatDate } from '../../utils/date';

export function AssignmentPreviewModal({ isOpen, onClose, form }) {
  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Assignment preview"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="modal-box">
        <div className="modal-head">
          <div>
            <span className="eyebrow" style={{ fontSize: '10px', letterSpacing: '1px', color: 'var(--color-text-secondary)', fontWeight: 700 }}>
              PREVIEW
            </span>
            <h3 style={{ margin: '4px 0 0', fontSize: '15px' }}>Assignment Details</h3>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close preview">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="preview-assignment-card">
            <div className="preview-label-row">
              <BookOpen size={14} aria-hidden="true" />
              <span className="published-tag">Assignment</span>
            </div>

            <h4 className="preview-topic">{form.topic || '—'}</h4>
            <p className="preview-subject-line">
              <strong>Subject:</strong> {form.subject || '—'}
            </p>

            {form.platform_link && (
              <p className="preview-link-line">
                <Link size={12} aria-hidden="true" />
                <a href={form.platform_link} target="_blank" rel="noreferrer noopener">
                  {form.platform_link}
                </a>
              </p>
            )}

            <div className="preview-dates">
              <span>
                <Calendar size={12} aria-hidden="true" />
                <strong>Start:</strong> {form.start_date || '—'}
              </span>
              <span>
                <Clock size={12} aria-hidden="true" />
                <strong>Deadline:</strong> {form.deadline || '—'}
              </span>
            </div>

            <div className="preview-message-block">
              <strong>Instructions:</strong>
              <p>{form.message || '—'}</p>
            </div>

            <div className="preview-audience">
              <Users size={12} aria-hidden="true" />
              Assigned to: <strong>{form.audience || 'All students'}</strong>
            </div>
          </div>
        </div>

        <div className="modal-foot">
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
