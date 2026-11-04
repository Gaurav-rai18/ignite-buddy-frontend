/**
 * @file StatsGrid.jsx
 * @description Dashboard statistics grid that shows four KPI cards: total broadcasts,
 *              scheduled links, Buddy control toggle, and system status. Uses the
 *              reusable `StatCard` component for the first two metrics and renders
 *              custom inline cards for the Buddy toggle and the system health indicator.
 *
 * Data flow: Receives `summary` (from `GET /api/summary/`), `buddy` state, and
 *            the `onToggleBuddy` callback from the Dashboard page.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Megaphone, CalendarClock, Bot, Database, ArrowUpRight } from 'lucide-react';
import { StatCard } from '../ui/StatCard';

/**
 * Renders the four-column statistics grid on the Dashboard.
 *
 * @param {Object}   props
 * @param {Object}   props.summary          - API summary with `broadcast_count` and `scheduled_count`.
 * @param {boolean}  props.buddy            - Whether the Buddy chatbot is currently enabled.
 * @param {Function} props.onToggleBuddy    - Callback to toggle the Buddy state.
 * @param {boolean}  props.isTogglingBuddy  - True while the toggle API call is pending.
 */
export function StatsGrid({ summary, buddy, onToggleBuddy, isTogglingBuddy }) {
  const navigate = useNavigate();

  return (
    <div className="stats-grid">
      <StatCard
        icon={Megaphone}
        tone="primary"
        label="Total broadcasts"
        value={summary?.broadcast_count ?? 0}
        note="Click to manage announcements"
        onClick={() => navigate('/broadcast')}
      />

      <StatCard
        icon={CalendarClock}
        tone="warning"
        label="Scheduled links"
        value={summary?.scheduled_count ?? 0}
        note="Click to manage OneDrive links"
        onClick={() => navigate('/schedule')}
      />

      <div className="stat-card">
        <div className="stat-top">
          <div className="stat-icon success">
            <Bot size={19} aria-hidden="true" />
          </div>
          <span className={`mini-status ${buddy ? 'on' : 'off'}`}>
            <i aria-hidden="true" />
            {buddy ? 'ACTIVE' : 'PAUSED'}
          </span>
        </div>
        <div className="stat-label">Buddy control</div>
        <div className="stat-value">{buddy ? 'Enabled' : 'Disabled'}</div>
        <div className="stat-note">Exam-time availability</div>
        <button
          type="button"
          className="inline-toggle"
          onClick={onToggleBuddy}
          disabled={isTogglingBuddy}
          aria-label={buddy ? 'Turn off Buddy' : 'Turn on Buddy'}
        >
          {isTogglingBuddy ? 'Updating...' : buddy ? 'Turn off Buddy' : 'Turn on Buddy'}
          <ArrowUpRight size={13} aria-hidden="true" />
        </button>
      </div>

      <div className="stat-card">
        <div className="stat-top">
          <div className="stat-icon primary">
            <Database size={19} aria-hidden="true" />
          </div>
          <span className="mini-status on">
            <i aria-hidden="true" /> ONLINE
          </span>
        </div>
        <div className="stat-label">System status</div>
        <div className="stat-value" style={{ fontSize: '20px', marginTop: '8px' }}>
          Operational
        </div>
        <div className="stat-note">SQLite local database active</div>
      </div>
    </div>
  );
}
