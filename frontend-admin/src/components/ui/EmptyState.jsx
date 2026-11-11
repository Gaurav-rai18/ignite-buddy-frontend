import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export function EmptyState({ icon: Icon, title, text, action, onClick }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Icon size={23} aria-hidden="true" />
      </div>
      <b>{title}</b>
      <p>{text}</p>
      {action && onClick && (
        <button type="button" className="text-button" onClick={onClick}>
          {action} <ArrowUpRight size={14} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
