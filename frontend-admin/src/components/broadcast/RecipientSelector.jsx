import React, { useEffect, useMemo, useState } from 'react';
import {
  Search,
  Users,
  X,
  Check,
  RotateCw,
  AlertCircle,
} from 'lucide-react';

import { usersService } from '../../services/usersService';

export function RecipientSelector({
  selectedUsers = [],
  onToggle,
  onSetRecipients,
  disabled = false,
}) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [query, setQuery] = useState('');

  useEffect(() => {
    let active = true;

    async function loadUsers() {
      try {
        setLoading(true);
        setLoadError('');

        const data = await usersService.getUsers();

        const userList = Array.isArray(data)
          ? data
          : data?.results || [];

        console.log('Users loaded:', userList);

        if (active) {
          setUsers(userList);
        }
      } catch (err) {
        console.error(err);

        if (active) {
          setLoadError(
            err.message || 'Failed to load users.'
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadUsers();

    return () => {
      active = false;
    };
  }, []);

  const selectedIds = useMemo(
    () => new Set(selectedUsers.map((u) => u.username)),
    [selectedUsers]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    if (!q) {
      return users;
    }

    return users.filter(
      (user) =>
        (user.username || '')
          .toLowerCase()
          .includes(q) ||
        (user.email || '')
          .toLowerCase()
          .includes(q)
    );
  }, [users, query]);

  const allFilteredSelected =
    filtered.length > 0 &&
    filtered.every((u) =>
      selectedIds.has(u.username)
    );

  const handleSelectAllFiltered = () => {
    if (allFilteredSelected) {
      const filteredIds = new Set(
        filtered.map((u) => u.username)
      );

      onSetRecipients?.(
        selectedUsers.filter(
          (u) => !filteredIds.has(u.username)
        )
      );
    } else {
      const map = new Map();

      selectedUsers.forEach((u) =>
        map.set(u.username, u)
      );

      filtered.forEach((u) =>
        map.set(u.username, u)
      );

      onSetRecipients?.(
        Array.from(map.values())
      );
    }
  };

  return (
    <div className="recipient-selector">
      <div
        className="table-search-bar"
        style={{ marginBottom: '10px' }}
      >
        <div className="search-input-wrap">
          <Search
            size={16}
            aria-hidden="true"
          />

          <input
            type="text"
            placeholder="Search by username or email..."
            value={query}
            onChange={(e) =>
              setQuery(e.target.value)
            }
            disabled={disabled}
          />
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={
            handleSelectAllFiltered
          }
          disabled={
            disabled ||
            filtered.length === 0
          }
        >
          <Check size={14} />

          {allFilteredSelected
            ? 'Unselect'
            : 'Select'}{' '}
          all ({filtered.length})
        </button>
      </div>

      {loading && (
        <div className="recipient-status">
          <RotateCw
            size={14}
            className="spin"
          />
          {' '}Loading users...
        </div>
      )}

      {!loading && loadError && (
        <div className="recipient-status error">
          <AlertCircle size={14} />
          {' '}
          {loadError}
        </div>
      )}

      {!loading && !loadError && (
        <div
          className="recipient-list"
          role="listbox"
          aria-multiselectable="true"
        >
          {filtered.length === 0 ? (
            <div className="recipient-status">
              No users match your search.
            </div>
          ) : (
            filtered.map((user) => {
              const isSelected =
                selectedIds.has(
                  user.username
                );

              return (
                <label
                  key={user.username}
                  className={`recipient-row ${
                    isSelected
                      ? 'selected'
                      : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() =>
                      onToggle?.(user)
                    }
                    disabled={disabled}
                  />

                  <span className="recipient-avatar">
                    {(user.username || 'U')
                      .slice(0, 2)
                      .toUpperCase()}
                  </span>

                  <span className="recipient-info">
                    <b>
                      {user.username}
                    </b>

                    <small>
                      {user.email}
                    </small>
                  </span>

                  <span className="recipient-role">
                    {user.role}
                  </span>
                </label>
              );
            })
          )}
        </div>
      )}

      <div className="recipient-selector-foot">
        <span>
          <Users size={13} />
          {' '}
          {selectedUsers.length}
          {' '}
          selected
        </span>

        {selectedUsers.length > 0 && (
          <button
            type="button"
            className="link-button"
            onClick={() =>
              onSetRecipients?.([])
            }
          >
            <X size={13} />
            {' '}
            Clear all
          </button>
        )}
      </div>
    </div>
  );
}
