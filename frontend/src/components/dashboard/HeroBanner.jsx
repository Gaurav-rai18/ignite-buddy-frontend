import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarClock, ArrowUpRight } from 'lucide-react';

export function HeroBanner({ upcomingCount = 0 }) {
  const navigate = useNavigate();

  return (
    <div className="overview-support-card">
      <div className="overview-support-copy">
        <div className="eyebrow" style={{ marginBottom: '4px' }}>
          <span className="eyebrow-line" aria-hidden="true" />
          CAMPUS WORKSPACE OVERVIEW
        </div>
        <h3>Keep everyone on the same page</h3>
        <p>
          Share campus updates, schedule OneDrive resources for upcoming publish dates,
          and control student Buddy availability during examinations.
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
        <div
          style={{
            background: 'var(--color-bg-cream)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 12px',
            textAlign: 'right',
          }}
        >
          <div style={{ fontSize: '9px', color: 'var(--color-text-secondary)', fontWeight: '700' }}>
            UPCOMING PUBLISHES
          </div>
          <div
            style={{
              fontSize: '15px',
              fontWeight: '800',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <CalendarClock size={16} aria-hidden="true" />
            {upcomingCount} items
          </div>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => navigate('/schedule')}
        >
          Manage schedules <ArrowUpRight size={15} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
