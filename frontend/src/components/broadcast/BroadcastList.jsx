import React from 'react';
import { Megaphone, Users, Send } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

export function BroadcastList({ broadcasts = [], loading = false, onCreateClick }) {
  return (
    <section className="panel list-panel">
      <div className="panel-heading">
        <div>
          <h3>Announcement history</h3>
          <p>{broadcasts.length} saved announcements</p>
        </div>
        <span className="count-badge" aria-label={`${broadcasts.length} announcements`}>
          {broadcasts.length}
        </span>
      </div>

      {loading && broadcasts.length === 0 ? (
        <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '11.5px' }}>
          Loading announcements...
        </div>
      ) : broadcasts.length > 0 ? (
        broadcasts.map((item) => (
          <article className="list-entry" key={item.id}>
            <div className="entry-top">
              <span className="entry-icon" aria-hidden="true">
                <Megaphone size={15} />
              </span>
              <span className="published-tag">Saved</span>
            </div>
            <h4>{item.title}</h4>
            <p>{item.message}</p>
            <div className="entry-meta">
              <span>
                <Users size={13} aria-hidden="true" />
                {item.audience}
              </span>
              <span>{formatDate(item.created_at)}</span>
            </div>
          </article>
        ))
      ) : (
        <EmptyState
          icon={Send}
          title="No announcements yet"
          text="Your published announcements will appear here."
          action={onCreateClick ? 'Create announcement' : undefined}
          onClick={onCreateClick}
        />
      )}
    </section>
  );
}
