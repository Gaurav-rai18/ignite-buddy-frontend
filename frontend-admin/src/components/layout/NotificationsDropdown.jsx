import React, { useEffect, useRef, useState } from 'react';
import { Bell, CheckCircle2, Megaphone, CalendarClock, Bot } from 'lucide-react';

export function NotificationsDropdown({ isOpen, onClose, broadcasts = [] }) {
  const dropdownRef = useRef(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        onClose();
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const notifications = cleared
    ? []
    : [
        {
          id: 'system-online',
          title: 'System operational',
          time: 'Active now',
          icon: CheckCircle2,
        },
        ...(broadcasts.slice(0, 2).map((b) => ({
          id: `broadcast-${b.id}`,
          title: `Broadcast saved: ${b.title}`,
          time: 'Campus wide',
          icon: Megaphone,
        }))),
      ];

  return (
    <div
      ref={dropdownRef}
      className="dropdown-menu notifications-dropdown"
      role="dialog"
      aria-label="Notifications panel"
    >
      <div className="notifications-header">
        <b>Notifications</b>
        {notifications.length > 0 && (
          <button
            type="button"
            onClick={() => setCleared(true)}
            aria-label="Mark all as read"
          >
            Mark all as read
          </button>
        )}
      </div>

      {notifications.length > 0 ? (
        <div className="notifications-list">
          {notifications.map((item) => {
            const Icon = item.icon;
            return (
              <div className="notification-item" key={item.id}>
                <Icon size={16} color="#014BAA" style={{ flexShrink: 0, marginTop: '2px' }} aria-hidden="true" />
                <div>
                  <p>{item.title}</p>
                  <span>{item.time}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="notifications-empty">
          <Bell size={24} style={{ opacity: 0.3, marginBottom: '6px' }} aria-hidden="true" />
          <div>No unread notifications</div>
        </div>
      )}
    </div>
  );
}
