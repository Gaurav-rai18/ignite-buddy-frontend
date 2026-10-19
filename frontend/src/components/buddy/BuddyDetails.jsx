import React from 'react';
import { Bot, Info } from 'lucide-react';

export function BuddyDetails({ buddy, isUpdating, onToggleBuddy }) {
  return (
    <section className="panel control-info">
      <div className="panel-heading">
        <div>
          <h3>Control details</h3>
          <p>Current saved configuration stored in SQLite</p>
        </div>
        <div className="stat-icon primary" aria-hidden="true">
          <Bot size={18} />
        </div>
      </div>

      <div className="setting-row">
        <div>
          <b>Buddy availability</b>
          <small>Master ON/OFF setting</small>
        </div>
        <button
          type="button"
          className={`switch ${buddy ? 'switch-on' : ''}`}
          role="switch"
          aria-checked={buddy}
          aria-label="Toggle Buddy availability"
          disabled={isUpdating}
          onClick={onToggleBuddy}
        >
          <span />
        </button>
      </div>

      <div className="setting-row">
        <div>
          <b>Current state</b>
          <small>Database value confirmed</small>
        </div>
        <span className={`state-label ${buddy ? 'state-on' : 'state-off'}`}>
          <i aria-hidden="true" />
          {buddy ? 'Enabled' : 'Disabled'}
        </span>
      </div>

      <div className="info-note" style={{ marginTop: '16px' }}>
        <Info size={16} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: '2px' }} aria-hidden="true" />
        <p>
          This toggle updates the Django backend database. External student apps connect to this setting via <code>/api/settings/buddy/</code> to determine exam period availability.
        </p>
      </div>
    </section>
  );
}
