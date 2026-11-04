/**
 * @file UserTable.jsx
 * @description Renders a table of registered users with role badges, cohort details,
 * and quick action triggers (edit and delete).
 */
import React from 'react';
import { GraduationCap, ShieldCheck, Edit2, Trash2 } from 'lucide-react';

export function UserTable({ users = [], onEdit, onDelete }) {
  if (users.length === 0) {
    return (
      <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
        No matching users found.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="data-table">
        <thead>
          <tr>
            <th>USER</th>
            <th>BATCH</th>
            <th>SUB-BATCH</th>
            <th>STATUS</th>
            <th style={{ textAlign: 'right' }}>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const isActive = user.status?.toLowerCase() === 'active';

            return (
              <tr key={user.id}>
                <td>
                  <div className="user-cell">
                    <div className="user-avatar-pill" aria-hidden="true">
                      {user.username?.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="user-details">
                      <b>{user.username}</b>
                      <small>{user.email}</small>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="department-text">Batch {user.batch}</span>
                </td>
                <td>
                  <span className="department-text">{user.subbatch?.toUpperCase()}</span>
                </td>
                <td>
                  <span className={`status-pill ${isActive ? 'active' : 'inactive'}`}>
                    <i aria-hidden="true" />
                    {user.status}
                  </span>
                </td>
                <td>
                  <div className="action-buttons-cell">
                    <button
                      type="button"
                      className="icon-action-btn"
                      onClick={() => onEdit(user)}
                      title={`Edit ${user.username}`}
                      aria-label={`Edit ${user.username}`}
                    >
                      <Edit2 size={15} aria-hidden="true" />
                    </button>
                    <button
                      type="button"
                      className="icon-action-btn danger"
                      onClick={() => onDelete(user)}
                      title={`Delete ${user.username}`}
                      aria-label={`Delete ${user.username}`}
                    >
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
