/**
 * @file BroadcastList.jsx
 * @description Displays the history of saved broadcast announcements in a scrollable list.
 *              Shows a loading placeholder while data is being fetched, an empty-state CTA
 *              when no broadcasts exist, or a list of broadcast cards with title, message,
 *              audience, and creation date.
 *
 * Data flow: Receives the `broadcasts` array from the parent Broadcast page, which fetches
 *            it from the Django REST API via `broadcastService.getBroadcasts()`.
 */
import React from 'react';
import { Megaphone, Users, Send } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

/**
 * Renders the announcement history panel.
 *
 * @param {Object}   props
 * @param {Array}    props.broadcasts   - Array of broadcast objects from the API.
 * @param {boolean}  props.loading      - Whether the parent is still fetching data.
 * @param {Function} [props.onCreateClick] - Callback to open the create-broadcast form; drives the empty-state CTA.
 */
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

      {/* Three-state rendering: loading spinner → broadcast cards → empty state */}
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
