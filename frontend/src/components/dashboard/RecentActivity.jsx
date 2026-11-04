/**
 * @file RecentActivity.jsx
 * @description Dashboard panel that shows the most recent broadcast announcements
 *              (up to 4). Each entry displays the title, target audience, and
 *              creation timestamp. When no broadcasts exist, an empty-state CTA
 *              prompts the admin to create one.
 *
 * Data flow: Receives the `broadcasts` array from the Dashboard page, which
 *            fetches it from `broadcastService.getBroadcasts()`.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Megaphone, ArrowUpRight } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

/**
 * Renders the recent broadcasts activity feed on the Dashboard.
 *
 * @param {Object} props
 * @param {Array}  props.broadcasts - Array of broadcast objects; only the first 4 are displayed.
 */
export function RecentActivity({ broadcasts = [] }) {
  const navigate = useNavigate();

  return (
    <section className="panel activity-panel">
      <div className="panel-heading">
        <div>
          <h3>Recent broadcasts</h3>
          <p>Your latest campus announcements</p>
        </div>
        <button
          type="button"
          className="round-arrow"
          onClick={() => navigate('/broadcast')}
          aria-label="View all broadcasts"
        >
          <ArrowUpRight size={17} aria-hidden="true" />
        </button>
      </div>

      {/* Show at most 4 recent broadcasts; slice prevents rendering a long list */}
      {broadcasts && broadcasts.length > 0 ? (
        broadcasts.slice(0, 4).map((item) => (
          <div className="activity-item" key={item.id}>
            <div className="activity-icon">
              <Megaphone size={17} aria-hidden="true" />
            </div>
            <div className="activity-copy">
              <b>{item.title}</b>
              <span>
                {item.audience} · {formatDate(item.created_at)}
              </span>
            </div>
            <span className="published-tag">Saved</span>
          </div>
        ))
      ) : (
        <EmptyState
          icon={Megaphone}
          title="No broadcasts yet"
          text="Your published announcements will appear here."
          action="Create broadcast"
          onClick={() => navigate('/broadcast')}
        />
      )}
    </section>
  );
}
