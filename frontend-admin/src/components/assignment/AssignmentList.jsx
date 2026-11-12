import React, { useState } from 'react';
import { BookOpen, Users, Send, Calendar, Clock, Link, Check, UploadCloud, ClipboardList } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

export function AssignmentList({
  assignments = [],
  loading = false,
  historyFilter = 'mine',
  onFilterChange,
  onCreateClick,
  deadlineUpdating = {},
  onUpdateDeadline,
  onPublish,
  publishingId = null,
  onViewSubmissions,
}) {
  // Local state for editable deadlines per card: { [id]: dateString }
  const [editDeadlines, setEditDeadlines] = useState({});

  const formatAudience = (item) => {
    if (item.recipient_type === 'COHORT') return `Cohort: ${item.target_cohort_code || 'Targeted'}`;
    if (item.recipient_type === 'BATCH') return `Batch: ${item.target_batch_code || 'Targeted'}`;
    if (item.recipient_type === 'SUB_BATCH') return `Sub-Batch: ${item.target_sub_batch_code || 'Targeted'}`;
    if (item.recipient_type === 'ROLE') return `Role: ${item.target_role || 'Targeted'}`;
    if (item.recipient_type === 'USERS' || item.recipient_type === 'USER')
      return `Specific: ${item.target_username || 'Selected users'}`;
    return item.audience || 'All students';
  };

  // Filter logic: "mine" shows posted_by_me === true, "others" shows the rest
  // If the backend doesn't send posted_by_me, show all in "mine" tab
  const filteredAssignments = assignments.filter((a) => {
    if (historyFilter === 'mine') return a.posted_by_me !== false;
    return a.posted_by_me === false;
  });

  const handleDeadlineChange = (id, value) => {
    setEditDeadlines((prev) => ({ ...prev, [id]: value }));
  };

  const handleDeadlineSave = (item) => {
    const newDeadline = editDeadlines[item.id] ?? item.deadline;
    if (!newDeadline) return;
    if (onUpdateDeadline) onUpdateDeadline(item.id, newDeadline);
  };

  const getDeadlineValue = (item) => {
    if (editDeadlines[item.id] !== undefined) return editDeadlines[item.id];
    // Normalize ISO date to YYYY-MM-DD for <input type="date">
    if (!item.deadline) return '';
    try {
      return new Date(item.deadline).toISOString().slice(0, 10);
    } catch {
      return item.deadline;
    }
  };

  return (
    <section className="panel list-panel">
      <div className="panel-heading">
        <div>
          <h3>Assignment history</h3>
          <p>{filteredAssignments.length} assignment{filteredAssignments.length !== 1 ? 's' : ''}</p>
        </div>
        <span className="count-badge" aria-label={`${assignments.length} total assignments`}>
          {assignments.length}
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="assignment-history-tabs" role="tablist" aria-label="Assignment history filter">
        <button
          type="button"
          role="tab"
          aria-selected={historyFilter === 'mine'}
          className={`assignment-tab-btn ${historyFilter === 'mine' ? 'active' : ''}`}
          onClick={() => onFilterChange && onFilterChange('mine')}
        >
          Posted by Me
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={historyFilter === 'others'}
          className={`assignment-tab-btn ${historyFilter === 'others' ? 'active' : ''}`}
          onClick={() => onFilterChange && onFilterChange('others')}
        >
          Posted by Others
        </button>
      </div>

      {/* Content */}
      {loading && assignments.length === 0 ? (
        <div
          style={{
            padding: '36px',
            textAlign: 'center',
            color: 'var(--color-text-secondary)',
            fontSize: '11.5px',
          }}
        >
          Loading assignments...
        </div>
      ) : filteredAssignments.length > 0 ? (
        filteredAssignments.map((item) => (
          <article className="list-entry assignment-entry" key={item.id}>
            <div className="entry-top">
              <span className="entry-icon" aria-hidden="true">
                <BookOpen size={15} />
              </span>
              <span className={`published-tag ${item.is_published === false ? 'draft-tag' : ''}`}>
                {item.is_published === false ? 'Draft' : 'Published'}
              </span>
            </div>

            {/* Topic & Subject */}
            <h4>{item.topic || item.title || '—'}</h4>
            {item.subject && (
              <p className="assignment-entry-subject">
                <strong>Subject:</strong> {item.subject}
              </p>
            )}

            {/* Platform link */}
            {item.platform_link && (
              <p className="assignment-entry-link">
                <Link size={11} aria-hidden="true" />
                <a href={item.platform_link} target="_blank" rel="noreferrer noopener">
                  {item.platform_link}
                </a>
              </p>
            )}

            {/* Meta: audience + start date */}
            <div className="entry-meta">
              <span style={{ fontWeight: 600 }}>
                <Users size={13} aria-hidden="true" />
                {formatAudience(item)}
              </span>
              {item.start_date && (
                <span>
                  <Calendar size={12} aria-hidden="true" />
                  Start: {formatDate(item.start_date)}
                </span>
              )}
            </div>

            {/* Editable Deadline */}
            <div className="deadline-editable-row">
              <label
                className="deadline-label"
                htmlFor={`deadline-input-${item.id}`}
              >
                <Clock size={12} aria-hidden="true" />
                Deadline:
              </label>
              <input
                id={`deadline-input-${item.id}`}
                type="date"
                className="deadline-date-input"
                value={getDeadlineValue(item)}
                onChange={(e) => handleDeadlineChange(item.id, e.target.value)}
                aria-label="Assignment deadline"
              />
              <button
                type="button"
                className="deadline-save-btn"
                disabled={deadlineUpdating[item.id]}
                onClick={() => handleDeadlineSave(item)}
                title="Save updated deadline"
              >
                {deadlineUpdating[item.id] ? (
                  '...'
                ) : (
                  <>
                    <Check size={12} aria-hidden="true" /> Update
                  </>
                )}
              </button>
            </div>

            {/* Actions: publish draft / review submissions */}
            <div className="assignment-entry-actions">
              {item.is_published === false && onPublish && (
                <button
                  type="button"
                  className="primary-button compact-button"
                  disabled={publishingId === item.id}
                  onClick={() => onPublish(item.id)}
                  title="Publish this draft and notify students"
                >
                  <UploadCloud size={13} aria-hidden="true" />
                  {publishingId === item.id ? 'Publishing...' : 'Publish'}
                </button>
              )}
              {onViewSubmissions && (
                <button
                  type="button"
                  className="secondary-button compact-button"
                  onClick={() => onViewSubmissions(item.id)}
                  title="Review and evaluate submissions"
                >
                  <ClipboardList size={13} aria-hidden="true" />
                  Submissions
                  {typeof item.submissions_count === 'number' && item.recipients_count
                    ? ` (${item.submissions_count}/${item.recipients_count})`
                    : ''}
                </button>
              )}
            </div>
          </article>
        ))
      ) : (
        <EmptyState
          icon={Send}
          title={
            historyFilter === 'mine'
              ? 'No assignments posted yet'
              : 'No assignments from others'
          }
          text={
            historyFilter === 'mine'
              ? 'Your published assignments will appear here.'
              : 'Assignments posted by other admins will appear here.'
          }
          action={historyFilter === 'mine' && onCreateClick ? 'Create assignment' : undefined}
          onClick={onCreateClick}
        />
      )}
    </section>
  );
}
