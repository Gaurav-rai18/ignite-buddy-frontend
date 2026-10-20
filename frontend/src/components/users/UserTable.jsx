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
            <th>ROLE</th>
            <th>DEPARTMENT</th>
            <th>STATUS</th>
            <th style={{ textAlign: 'right' }}>ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const isAdmin = user.role.toLowerCase() === 'admin';
            const isActive = user.status.toLowerCase() === 'active';

            return (
              <tr key={user.id}>
                <td>
                  <div className="user-cell">
                    <div className="user-avatar-pill" aria-hidden="true">
                      {user.initials}
                    </div>
                    <div className="user-details">
                      <b>{user.name}</b>
                      <small>{user.email}</small>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`role-badge ${isAdmin ? 'admin' : 'student'}`}>
                    {isAdmin ? (
                      <ShieldCheck size={13} aria-hidden="true" />
                    ) : (
                      <GraduationCap size={13} aria-hidden="true" />
                    )}
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className="department-text">{user.department}</span>
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
                      title={`Edit ${user.name}`}
                      aria-label={`Edit ${user.name}`}
                    >
                      <Edit2 size={15} aria-hidden="true" />
                    </button>
                    <button
                      type="button"
                      className="icon-action-btn danger"
                      onClick={() => onDelete(user)}
                      title={`Delete ${user.name}`}
                      aria-label={`Delete ${user.name}`}
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
