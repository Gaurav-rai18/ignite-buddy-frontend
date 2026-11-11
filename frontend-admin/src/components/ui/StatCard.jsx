import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export function StatCard({ icon: Icon, tone = 'primary', label, value, note, onClick }) {
  const Component = onClick ? 'button' : 'div';

  return (
    <Component
      type={onClick ? 'button' : undefined}
      className={`stat-card ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="stat-top">
        <div className={`stat-icon ${tone}`}>
          <Icon size={19} aria-hidden="true" />
        </div>
        <span className="stat-trend" aria-hidden="true">
          <ArrowUpRight size={15} />
        </span>
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-note">{note}</div>
    </Component>
  );
}
