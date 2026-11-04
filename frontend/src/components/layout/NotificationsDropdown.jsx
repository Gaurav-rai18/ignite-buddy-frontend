/**
 * @file NotificationsDropdown.jsx
 * @description Dropdown panel that displays system notifications and recent broadcast
 *              alerts in the Topbar.
 *
 * Behaviour:
 *  - Shows a static "System operational" notification plus up to two recent broadcasts.
 *  - "Mark all as read" sets a local `cleared` flag so the list appears empty.
 *  - Closes on outside click (mousedown) or Escape key press.
 *  - Returns `null` when `isOpen` is false to keep the DOM clean.
 *
 * Data flow:
 *  Topbar ➜ isOpen, onClose, broadcasts[]
 *
 * @exports NotificationsDropdown
 */
import React, { useEffect, useRef, useState } from 'react';
import { Bell, CheckCircle2, Megaphone, CalendarClock, Bot } from 'lucide-react';

/**
 * Notifications flyout panel.
 * @param {Object}   props
 * @param {boolean}  props.isOpen      - Whether the dropdown is visible.
 * @param {Function} props.onClose     - Called to close the dropdown.
 * @param {Array}    props.broadcasts  - Array of broadcast objects from the API.
 */
export function NotificationsDropdown({ isOpen, onClose, broadcasts = [] }) {
  const dropdownRef = useRef(null);
  /** When true, all notifications are hidden (local "read" state — not persisted) */
  const [cleared, setCleared] = useState(false);

  /* ── Close-on-outside-click & Escape key handler ─────────────────────── */
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

  /*
   * Build the notification list:
   * - If the user has cleared them, show an empty array.
   * - Otherwise, include a fixed "system online" item plus the first two broadcasts
   *   (to keep the dropdown compact).
   */
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
