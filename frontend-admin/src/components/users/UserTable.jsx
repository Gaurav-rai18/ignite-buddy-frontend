import React from 'react';
import {
  GraduationCap,
  ShieldCheck,
  UserCheck,
  Briefcase,
  Edit2,
  Trash2,
} from 'lucide-react';

export function UserTable({
  users = [],
  onEdit,
  onDelete,
}) {
  if (users.length === 0) {
    return (
      <div
        style={{
          padding: '36px 16px',
          textAlign: 'center',
          color: 'var(--color-text-secondary)',
          fontSize: '12px',
        }}
      >
        No matching users found.
      </div>
    );
  }

  const getRoleIcon = (role) => {
    switch (role?.toUpperCase()) {
      case 'ADMIN':
        return <ShieldCheck size={13} aria-hidden="true" />;
      case 'TA':
      case 'HR':
      case 'MANAGER':
        return <Briefcase size={13} aria-hidden="true" />;
      case 'TRAINEE':
      default:
        return <GraduationCap size={13} aria-hidden="true" />;
    }
  };

  return (
    <div className="table-responsive">
      <table className="data-table">
        <thead>
          <tr>
            <th>USER</th>
            <th>ROLE</th>
            <th>EMPLOYEE ID</th>
            <th>BATCH / HIERARCHY</th>
            <th>STATUS</th>
            <th style={{ textAlign: 'right' }}>
              ACTIONS
            </th>
          </tr>
        </thead>

        <tbody>
          {users.map((user) => {
            const isAdmin = user.role?.toUpperCase() === 'ADMIN';
            const isActive = user.is_active !== false;
            const batchDisplay = user.full_batch_name || user.cohort_code || '-';

            return (
              <tr key={user.id}>
                <td>
                  <div className="user-cell">
                    <div
                      className="user-avatar-pill"
                      aria-hidden="true"
                    >
                      {user.username
                        ?.charAt(0)
                        ?.toUpperCase() || 'U'}
                    </div>

                    <div className="user-details">
                      <b>{user.username}</b>
                      <small>{user.email}</small>
                    </div>
                  </div>
                </td>

                <td>
                  <span
                    className={`role-badge ${
                      isAdmin ? 'admin' : 'student'
                    }`}
                  >
                    {getRoleIcon(user.role)}
                    {user.role}
                  </span>
                </td>

                <td>
                  <span style={{ fontSize: '11.5px', color: 'var(--color-text-primary)', fontWeight: 500 }}>
                    {user.employee_id || '-'}
                  </span>
                </td>

                <td>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '11px',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--color-primary-light)',
                      color: 'var(--color-primary)',
                      fontWeight: 600,
                    }}
                  >
                    {batchDisplay}
                  </span>
                </td>

                <td>
                  <span
                    className={`mini-status ${isActive ? 'on' : 'off'}`}
                    style={{ fontSize: '10.5px' }}
                  >
                    <i aria-hidden="true" />
                    {isActive ? 'ACTIVE' : 'INACTIVE'}
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
