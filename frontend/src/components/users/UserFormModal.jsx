import React, { useState, useEffect } from 'react';
import { X, UserPlus, Edit3 } from 'lucide-react';
import { Field } from '../ui/Field';

export function UserFormModal({ isOpen, onClose, onSubmit, initialUser = null }) {
  const isEditing = Boolean(initialUser);

  const [form, setForm] = useState({
    name: '',
    email: '',
    role: 'Student',
    department: 'Information Technology',
    status: 'Active',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialUser) {
      setForm({
        name: initialUser.name || '',
        email: initialUser.email || '',
        role: initialUser.role || 'Student',
        department: initialUser.department || 'Information Technology',
        status: initialUser.status || 'Active',
      });
    } else {
      setForm({
        name: '',
        email: '',
        role: 'Student',
        department: 'Information Technology',
        status: 'Active',
      });
    }
    setErrors({});
  }, [initialUser, isOpen]);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!form.name.trim()) {
      newErrors.name = 'Full name is required.';
    }
    if (!form.email.trim()) {
      newErrors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      newErrors.email = 'Please provide a valid email address.';
    }
    if (!form.department.trim()) {
      newErrors.department = 'Department is required.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(form);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="user-modal-title"
      onClick={onClose}
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="entry-icon" aria-hidden="true">
              {isEditing ? <Edit3 size={16} /> : <UserPlus size={16} />}
            </span>
            <h3 id="user-modal-title">{isEditing ? 'Edit user' : 'Add new user'}</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close user modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="form-layout" noValidate>
          <Field label="Full name" htmlFor="user-name" error={errors.name}>
            <input
              id="user-name"
              required
              placeholder="e.g. Rahul Sharma"
              value={form.name}
              onChange={(e) => {
                setForm({ ...form, name: e.target.value });
                if (errors.name) setErrors({ ...errors, name: '' });
              }}
              autoFocus
            />
          </Field>

          <Field label="Email address" htmlFor="user-email" error={errors.email}>
            <input
              id="user-email"
              required
              type="email"
              placeholder="e.g. rahul.sharma@campus.demo"
              value={form.email}
              onChange={(e) => {
                setForm({ ...form, email: e.target.value });
                if (errors.email) setErrors({ ...errors, email: '' });
              }}
            />
          </Field>

          <div className="date-time-grid">
            <Field label="Role" htmlFor="user-role">
              <select
                id="user-role"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="Student">Student</option>
                <option value="Admin">Admin</option>
              </select>
            </Field>

            <Field label="Status" htmlFor="user-status">
              <select
                id="user-status"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </select>
            </Field>
          </div>

          <Field label="Department" htmlFor="user-department" error={errors.department}>
            <input
              id="user-department"
              required
              placeholder="e.g. Information Technology"
              value={form.department}
              onChange={(e) => {
                setForm({ ...form, department: e.target.value });
                if (errors.department) setErrors({ ...errors, department: '' });
              }}
            />
          </Field>

          <div className="form-foot" style={{ marginTop: '8px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>
              Assign role and status for demo access
            </span>
            <div className="form-foot-actions">
              <button type="button" className="secondary-button" onClick={onClose} disabled={submitting}>
                Cancel
              </button>
              <button type="submit" className="primary-button" disabled={submitting}>
                {submitting ? 'Saving...' : isEditing ? 'Save changes' : 'Add user'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
