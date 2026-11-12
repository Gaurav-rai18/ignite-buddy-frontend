import React, { useEffect, useState } from 'react';
import { X, Users, Clock, Link as LinkIcon, CheckCircle2, FileText, Star } from 'lucide-react';
import { formatDate } from '../../utils/date';

const STATUS_LABELS = {
  PENDING: 'Pending',
  SUBMITTED: 'Submitted',
  EVALUATED: 'Evaluated',
};

function EvaluatorRow({ submission, saving, onEvaluate }) {
  const [grade, setGrade] = useState(submission.grade || '');
  const [feedback, setFeedback] = useState(submission.feedback || '');
  const [resubmission, setResubmission] = useState(Boolean(submission.resubmission_required));

  useEffect(() => {
    setGrade(submission.grade || '');
    setFeedback(submission.feedback || '');
    setResubmission(Boolean(submission.resubmission_required));
  }, [submission.grade, submission.feedback, submission.resubmission_required]);

  const hasSubmission = Boolean(submission.submitted_at) ||
    submission.status === 'SUBMITTED' || submission.status === 'EVALUATED';

  const handleSave = () => {
    if (!grade.trim()) return;
    onEvaluate(submission.id, {
      grade: grade.trim(),
      feedback: feedback.trim(),
      resubmission_required: resubmission,
    });
  };

  return (
    <div className="submission-row">
      <div className="submission-row-head">
        <div>
          <strong>{submission.full_name || submission.username}</strong>
          {submission.employee_id && (
            <span className="submission-employee-id"> · {submission.employee_id}</span>
          )}
        </div>
        <span className={`submission-status submission-status-${submission.status.toLowerCase()}`}>
          {STATUS_LABELS[submission.status] || submission.status}
        </span>
      </div>

      {hasSubmission ? (
        <>
          {submission.submission_link && (
            <p className="submission-link-line">
              <LinkIcon size={12} aria-hidden="true" />
              <a href={submission.submission_link} target="_blank" rel="noreferrer noopener">
                {submission.submission_link}
              </a>
            </p>
          )}
          {submission.submission_text && (
            <p className="submission-text-block">
              <FileText size={12} aria-hidden="true" />
              <span>{submission.submission_text}</span>
            </p>
          )}
          {submission.submitted_at && (
            <p className="submission-meta-line">
              <Clock size={11} aria-hidden="true" />
              Submitted {formatDate(submission.submitted_at)}
            </p>
          )}

          <div className="submission-evaluate-grid">
            <label className="submission-field">
              <span>Grade</span>
              <input
                type="text"
                value={grade}
                maxLength={20}
                placeholder="e.g. A+"
                onChange={(e) => setGrade(e.target.value)}
                disabled={saving}
              />
            </label>
            <label className="submission-field submission-field-wide">
              <span>Feedback</span>
              <textarea
                rows={2}
                value={feedback}
                placeholder="Share feedback with the trainee..."
                onChange={(e) => setFeedback(e.target.value)}
                disabled={saving}
              />
            </label>
          </div>

          <div className="submission-row-actions">
            <label className="submission-resubmit-toggle">
              <input
                type="checkbox"
                checked={resubmission}
                onChange={(e) => setResubmission(e.target.checked)}
                disabled={saving}
              />
              <span>Require resubmission</span>
            </label>
            <button
              type="button"
              className="primary-button"
              onClick={handleSave}
              disabled={saving || !grade.trim()}
            >
              <Star size={13} aria-hidden="true" />
              {saving ? 'Saving...' : submission.status === 'EVALUATED' ? 'Update evaluation' : 'Save evaluation'}
            </button>
          </div>
        </>
      ) : (
        <p className="submission-pending-note">
          <Clock size={12} aria-hidden="true" /> No submission yet — awaiting the trainee.
        </p>
      )}
    </div>
  );
}

export function AssignmentSubmissionsModal({
  isOpen,
  assignment,
  submissions = [],
  loading = false,
  evaluationSaving = {},
  onClose,
  onEvaluate,
}) {
  if (!isOpen) return null;

  const submitted = submissions.filter(
    (s) => s.status === 'SUBMITTED' || s.status === 'EVALUATED'
  ).length;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Assignment submissions"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="modal-card submission-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="eyebrow">SUBMISSIONS</span>
            <h3>{assignment?.topic || 'Assignment'}</h3>
          </div>
          <button type="button" className="btn-close" onClick={onClose} aria-label="Close submissions">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body submission-modal-body">
          <div className="submission-summary">
            <span>
              <Users size={13} aria-hidden="true" />
              {submissions.length} recipient{submissions.length === 1 ? '' : 's'}
            </span>
            <span>
              <CheckCircle2 size={13} aria-hidden="true" />
              {submitted} submitted
            </span>
          </div>

          {loading ? (
            <p className="submission-loading">Loading submissions...</p>
          ) : submissions.length === 0 ? (
            <p className="submission-loading">No recipients for this assignment yet.</p>
          ) : (
            submissions.map((submission) => (
              <EvaluatorRow
                key={submission.id}
                submission={submission}
                saving={Boolean(evaluationSaving[submission.id])}
                onEvaluate={onEvaluate}
              />
            ))
          )}
        </div>

        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
