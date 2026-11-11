import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Megaphone, CalendarClock, Bot, GraduationCap, ArrowUpRight } from 'lucide-react';
import { StatCard } from '../ui/StatCard';

export function StatsGrid({ summary, buddy, onToggleBuddy, isTogglingBuddy }) {
  const navigate = useNavigate();

  const hierarchySummary = summary?.total_cohorts !== undefined
    ? `${summary.total_cohorts} Cohorts · ${summary.total_batches} Batches · ${summary.total_sub_batches} Labs`
    : 'Click to manage trainees';

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
        label="Weekly schedule"
        value={summary?.scheduled_count ?? 0}
        note="Click to manage timetables"
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

      <StatCard
        icon={GraduationCap}
        tone="primary"
        label="Trainee roster"
        value={summary?.total_trainees ?? summary?.total_users ?? 0}
        note={hierarchySummary}
        onClick={() => navigate('/users')}
      />
    </div>
  );
}
