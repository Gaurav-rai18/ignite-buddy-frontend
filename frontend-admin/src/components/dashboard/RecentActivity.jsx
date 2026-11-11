import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Megaphone, ArrowUpRight } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { formatDate } from '../../utils/date';

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
