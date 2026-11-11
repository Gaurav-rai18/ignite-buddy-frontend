import React from 'react';
import { CalendarClock, Link2, Clock3, ExternalLink, Users } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';
import { isValidHttpsUrl } from '../../utils/validation';

export function ScheduleList({ schedules = [], loading = false, onCreateClick }) {
  const getTargetBadge = (item) => {
    switch (item.target_type) {
      case 'COHORT':
        return 'Cohort Targeted';
      case 'BATCH':
        return 'Batch Targeted';
      case 'SUB_BATCH':
        return 'Sub-Batch Targeted';
      case 'ALL':
      default:
        return 'All Cohorts';
    }
  };

  return (
    <section className="panel list-panel">
      <div className="panel-heading">
        <div>
          <h3>Upcoming schedule</h3>
          <p>Saved links and their publish times</p>
        </div>
        <span className="count-badge" aria-label={`${schedules.length} schedules`}>
          {schedules.length}
        </span>
      </div>

      {loading && schedules.length === 0 ? (
        <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '11.5px' }}>
          Loading schedules...
        </div>
      ) : schedules.length > 0 ? (
        schedules.map((item) => {
          const isSafeUrl = isValidHttpsUrl(item.onedrive_url);

          return (
            <article className="list-entry" key={item.id}>
              <div className="entry-top">
                <span className="entry-icon" aria-hidden="true">
                  <Link2 size={15} />
                </span>
                <span className="scheduled-tag">
                  <Clock3 size={11} aria-hidden="true" /> {item.status || 'Scheduled'}
                </span>
              </div>
              <h4>{item.title}</h4>
              {isSafeUrl ? (
                <a
                  className="external-link"
                  href={item.onedrive_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open OneDrive link <ExternalLink size={12} aria-hidden="true" />
                </a>
              ) : (
                <span className="external-link" style={{ opacity: 0.6 }}>
                  (Invalid link URL)
                </span>
              )}
              <div className="entry-meta">
                <span style={{ fontWeight: 600 }}>
                  <Users size={13} aria-hidden="true" />
                  {getTargetBadge(item)}
                </span>
                <span>
                  <CalendarClock size={13} aria-hidden="true" />
                  {formatDate(item.publish_at)}
                </span>
              </div>
            </article>
          );
        })
      ) : (
        <EmptyState
          icon={CalendarClock}
          title="No scheduled items yet"
          text="Plan ahead and schedule your OneDrive links here."
          action={onCreateClick ? 'Schedule a link' : undefined}
          onClick={onCreateClick}
        />
      )}
    </section>
  );
}
