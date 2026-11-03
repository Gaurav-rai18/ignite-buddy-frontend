import React, { useState, useEffect } from 'react';
import { X, UserPlus, Edit3 } from 'lucide-react';
import { Field } from '../ui/Field';

export function UserFormModal({ isOpen, onClose, onSubmit, initialUser = null }) {
  const isEditing = Boolean(initialUser);

  const [form, setForm] = useState({
    username: '',
    email: '',
    batch: '51',
    subbatch: 'a1',
    password: '',
    status: 'Active',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialUser) {
      setForm({
        username: initialUser.username || '',
        email: initialUser.email || '',
        batch: initialUser.batch || '51',
        subbatch: initialUser.subbatch || 'a1',
        password: '', // Don't populate password on edit
        status: initialUser.status || 'Active',
      });
    } else {
      setForm({
        username: '',
        email: '',
        batch: '51',
        subbatch: 'a1',
        password: '',
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

    if (!form.username.trim()) {
      newErrors.username = 'Username is required.';
    }
    if (!form.email.trim()) {
      newErrors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      newErrors.email = 'Please provide a valid email address.';
    }
    if (!isEditing && !form.password) {
      newErrors.password = 'Password is required for new users.';
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
          <Field label="Username" htmlFor="user-username" error={errors.username}>
            <input
              id="user-username"
              required
              placeholder="e.g. rahul_s"
              value={form.username}
              onChange={(e) => {
                setForm({ ...form, username: e.target.value });
                if (errors.username) setErrors({ ...errors, username: '' });
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
            <Field label="Batch" htmlFor="user-batch">
              <select
                id="user-batch"
                value={form.batch}
                onChange={(e) => setForm({ ...form, batch: e.target.value })}
              >
                {['51', '50', '49', '46', '47'].map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </Field>

            <Field label="Sub-batch" htmlFor="user-subbatch">
              <select
                id="user-subbatch"
                value={form.subbatch}
                onChange={(e) => setForm({ ...form, subbatch: e.target.value })}
              >
                {['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4', 'c1', 'c2', 'c3', 'c4'].map(sb => (
                  <option key={sb} value={sb}>{sb.toUpperCase()}</option>
                ))}
              </select>
            </Field>
          </div>

          <div className="date-time-grid">
            <Field label="Password" htmlFor="user-password" error={errors.password}>
              <input
                id="user-password"
                type="password"
                placeholder={isEditing ? "Leave blank to keep current" : "Enter password"}
                value={form.password}
                onChange={(e) => {
                  setForm({ ...form, password: e.target.value });
                  if (errors.password) setErrors({ ...errors, password: '' });
                }}
              />
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