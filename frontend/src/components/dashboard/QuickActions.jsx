/**
 * @file QuickActions.jsx
 * @description Dashboard panel with large shortcut buttons that navigate admins
 *              directly to the three core workflows: Broadcast, Schedule, and
 *              Buddy management. Each button uses `react-router-dom`'s
 *              `useNavigate` for client-side routing.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Link2, Bot, ArrowUpRight } from 'lucide-react';

/**
 * Renders a set of quick-action navigation buttons on the Dashboard.
 * No props required — routes are hard-coded to the app's internal paths.
 */
export function QuickActions() {
  const navigate = useNavigate();

  return (
    <section className="panel quick-panel">
      <div className="panel-heading">
        <div>
          <h3>Quick actions</h3>
          <p>Jump straight into your workflow</p>
        </div>
      </div>

      <button
        type="button"
        className="quick-action"
        onClick={() => navigate('/broadcast')}
      >
        <div className="quick-icon blue">
          <Send size={17} aria-hidden="true" />
        </div>
        <div>
          <b>Send a broadcast</b>
          <small>Share an update with students</small>
        </div>
        <ArrowUpRight size={16} aria-hidden="true" />
      </button>

      <button
        type="button"
        className="quick-action"
        onClick={() => navigate('/schedule')}
      >
        <div className="quick-icon cream">
          <Link2 size={17} aria-hidden="true" />
        </div>
        <div>
          <b>Schedule a OneDrive link</b>
          <small>Choose a link and publish time</small>
        </div>
        <ArrowUpRight size={16} aria-hidden="true" />
      </button>

      <button
        type="button"
        className="quick-action"
        onClick={() => navigate('/buddy')}
      >
        <div className="quick-icon green">
          <Bot size={17} aria-hidden="true" />
        </div>
        <div>
          <b>Manage Buddy</b>
          <small>Control exam-time availability</small>
        </div>
        <ArrowUpRight size={16} aria-hidden="true" />
      </button>
    </section>
  );
}
