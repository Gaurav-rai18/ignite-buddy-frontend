import React from 'react';
import { Bot, Power, CheckCircle2 } from 'lucide-react';

export function BuddyHero({ buddy, isUpdating, onToggleBuddy }) {
  return (
    <section className="buddy-hero-banner">
      <div className="buddy-status-wrap">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className={`mini-status ${buddy ? 'on' : 'off'}`}>
            <i aria-hidden="true" />
            {buddy ? 'ACTIVE' : 'PAUSED'}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>
            Exam Period Control
          </span>
        </div>

        <h2>{buddy ? 'Buddy is ready to go' : 'Buddy is currently off'}</h2>

        <p>
          {buddy
            ? 'Buddy is currently available during exam periods. Switch it off during exams when needed.'
            : 'Buddy is disabled in the saved settings. Turn it back on whenever it is appropriate.'}
        </p>
      </div>

      <div>
        <button
          type="button"
          className={`primary-button ${buddy ? 'danger-button' : ''}`}
          onClick={onToggleBuddy}
          disabled={isUpdating}
          aria-label={buddy ? 'Turn Buddy OFF' : 'Turn Buddy ON'}
          style={{ minWidth: '150px' }}
        >
          {buddy ? (
            <Power size={16} aria-hidden="true" />
          ) : (
            <CheckCircle2 size={16} aria-hidden="true" />
          )}
          {isUpdating ? 'Updating...' : `Turn Buddy ${buddy ? 'OFF' : 'ON'}`}
        </button>
      </div>
    </section>
  );
}
