/**
 * @file RecipientSelector.jsx
 * @description Multi-select user picker for targeted broadcast delivery. Fetches
 *              the full user list from the Django REST API on mount, then provides
 *              search/filter, select-all, and individual toggle functionality.
 *
 * Data flow: Calls `usersService.getUsers()` once on mount to populate the local
 *            user list. Selected users are managed by the parent via `onToggle`
 *            (single user) and `onSetRecipients` (bulk add/remove).
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Search, Users, X, Check, RotateCw, AlertCircle } from 'lucide-react';
import { usersService } from '../../services/usersService';

/**
 * Search + multi-select picker for broadcast recipients.
 * Uses the existing users API (GET /users/).
 */
export function RecipientSelector({
  selectedUsers = [],
  onToggle,
  onSetRecipients,
  disabled = false,
}) {
  const [users, setUsers] = useState([]);       // Full user list from API
  const [loading, setLoading] = useState(false); // True while the API call is in-flight
  const [loadError, setLoadError] = useState(''); // Error message if the fetch fails
  const [query, setQuery] = useState('');         // Current search/filter query string
  const loadedRef = useRef(false);                // Guards against duplicate API calls (React StrictMode)

  // Fetch all users once on mount. The `loadedRef` prevents duplicate calls
  // caused by React StrictMode's double-invoke in development.
  useEffect(() => {
    let active = true;
    if (loadedRef.current) return undefined;

    loadedRef.current = true;
    setLoading(true);
    setLoadError('');

    usersService
      .getUsers()
      .then((data) => {
        if (active) setUsers(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        if (active) setLoadError(err.message || 'Failed to load users.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // Build a Set of selected user IDs for O(1) lookup in the list rendering
  const selectedIds = useMemo(
    () => new Set(selectedUsers.map((u) => u.id)),
    [selectedUsers]
  );

  // Filter users by the search query — matches against username, email, batch, or subbatch
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(
      (u) =>
        (u.username || '').toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q) ||
        (u.batch || '').toLowerCase().includes(q) ||
        (u.subbatch || '').toLowerCase().includes(q)
    );
  }, [users, query]);

  // True when every user in the current filtered view is already selected
  const allFilteredSelected =
    filtered.length > 0 && filtered.every((u) => selectedIds.has(u.id));

  /**
   * Toggles select-all for the currently visible (filtered) users.
   * If all filtered users are selected, they are removed from the selection.
   * Otherwise, the filtered users are merged into the existing selection
   * using a Map to avoid duplicates.
   */
  const handleSelectAllFiltered = () => {
    if (allFilteredSelected) {
      const filteredIds = new Set(filtered.map((u) => u.id));
      if (onSetRecipients) {
        onSetRecipients(selectedUsers.filter((u) => !filteredIds.has(u.id)));
      }
    } else {
      const byId = new Map(selectedUsers.map((u) => [u.id, u]));
      filtered.forEach((u) => byId.set(u.id, u));
      if (onSetRecipients) onSetRecipients(Array.from(byId.values()));
    }
  };

  return (
    <div className="recipient-selector">
      <div className="table-search-bar" style={{ marginBottom: '10px' }}>
        <div className="search-input-wrap">
          <Search size={16} aria-hidden="true" />
          <input
            type="text"
            placeholder="Search by username or email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={disabled}
            aria-label="Search users by username or email"
          />
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={handleSelectAllFiltered}
          disabled={disabled || filtered.length === 0}
          style={{ whiteSpace: 'nowrap' }}
        >
          <Check size={14} aria-hidden="true" />
          {allFilteredSelected ? 'Unselect' : 'Select'} all ({filtered.length})
        </button>
      </div>

      {loading && (
        <div className="recipient-status">
          <RotateCw size={14} className="spin" aria-hidden="true" /> Loading users...
        </div>
      )}

      {loadError && !loading && (
        <div className="recipient-status error">
          <AlertCircle size={14} aria-hidden="true" /> {loadError}
        </div>
      )}

      {!loading && !loadError && (
        <div className="recipient-list" role="listbox" aria-multiselectable="true">
          {filtered.length === 0 ? (
            <div className="recipient-status">No users match your search.</div>
          ) : (
            filtered.map((user) => {
              const isSelected = selectedIds.has(user.id);
              return (
                <label
                  key={user.id}
                  className={`recipient-row ${isSelected ? 'selected' : ''}`}
                  role="option"
                  aria-selected={isSelected}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggle && onToggle(user)}
                    disabled={disabled}
                  />
                  <span className="recipient-avatar" aria-hidden="true">
                    {(user.username || 'U').slice(0, 2).toUpperCase()}
                  </span>
                  <span className="recipient-info">
                    <b>{user.username}</b>
                    <small>{user.email || 'No email'}</small>
                  </span>
                  <span className="recipient-role" title="Role is not exposed by the users API yet">
                    {user.role || '—'}
                  </span>
                </label>
              );
            })
          )}
        </div>
      )}

      <div className="recipient-selector-foot">
        <span>
          <Users size={13} aria-hidden="true" /> {selectedUsers.length} selected
        </span>
        {selectedUsers.length > 0 && (
          <button
            type="button"
            className="link-button"
            onClick={() => onSetRecipients && onSetRecipients([])}
            disabled={disabled}
          >
            <X size={13} aria-hidden="true" /> Clear all
          </button>
        )}
      </div>
    </div>
  );
}
