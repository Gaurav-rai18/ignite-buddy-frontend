import React, { useState } from 'react';
import { X, Plus, Trash2, Edit2, Clock, AlertTriangle, Check, ArrowDownUp } from 'lucide-react';
import { validateTimeSlot } from '../../utils/validation';

export function TimeSlotManagerModal({ isOpen, onClose, config, onAddTimeSlot, onEditTimeSlot, onRemoveTimeSlot }) {
  const [editingId, setEditingId] = useState(null);
  const [startTime, setStartTime] = useState('09:00 AM');
  const [endTime, setEndTime] = useState('11:00 AM');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);

  if (!isOpen) return null;

  const timeSlots = config?.time_slots || [];

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');

    const validation = validateTimeSlot(startTime, endTime, timeSlots, editingId);
    if (!validation.isValid) {
      setError(validation.errors.endTime || validation.errors.overlap || 'Invalid time slot.');
      return;
    }

    const label = `${startTime.trim()} – ${endTime.trim()}`;
    setIsSubmitting(true);
    try {
      if (editingId) {
        await onEditTimeSlot(editingId, {
          start_time: startTime.trim(),
          end_time: endTime.trim(),
          label,
        });
        setEditingId(null);
      } else {
        await onAddTimeSlot({
          start_time: startTime.trim(),
          end_time: endTime.trim(),
          label,
          order: timeSlots.length + 1,
        });
      }
      setStartTime('09:00 AM');
      setEndTime('11:00 AM');
    } catch (err) {
      setError(err?.message || 'Failed to save time slot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartEdit = (slot) => {
    setEditingId(slot.id);
    setStartTime(slot.start_time || '09:00 AM');
    setEndTime(slot.end_time || '11:00 AM');
    setError('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setStartTime('09:00 AM');
    setEndTime('11:00 AM');
    setError('');
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmation) return;
    setIsSubmitting(true);
    setError('');
    try {
      await onRemoveTimeSlot(deleteConfirmation.id);
      setDeleteConfirmation(null);
    } catch (err) {
      setError(err?.message || 'Failed to remove time slot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ts-mgr-title" onClick={onClose}>
      <div className="modal-card timeslot-manager-modal" style={{ maxWidth: '600px', width: '95%' }} onClick={(e) => e.stopPropagation()}>
        {/* Head */}
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              className="entry-icon"
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                display: 'grid',
                placeItems: 'center',
              }}
              aria-hidden="true"
            >
              <Clock size={18} />
            </span>
            <div>
              <h3 id="ts-mgr-title" style={{ margin: 0, fontSize: '15px' }}>
                Manage Dynamic Time Slots
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                Configure, edit, and reorder class or lab periods
              </p>
            </div>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close dialog">
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {error && (
          <div className="manager-error-alert" style={{ margin: '14px 0 0', padding: '10px 12px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '6px', color: '#991B1B', fontSize: '11.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Delete Confirmation Box */}
        {deleteConfirmation && (
          <div className="delete-confirm-box" style={{ margin: '14px 0 0', padding: '12px 14px', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '8px' }}>
            <p style={{ margin: '0 0 10px', fontSize: '12px', fontWeight: '600', color: '#92400E' }}>
              Are you sure you want to delete time slot &quot;{deleteConfirmation.label}&quot;? Existing schedule cells in this slot may become unassigned.
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="danger-button"
                style={{ fontSize: '11px', padding: '5px 12px' }}
                onClick={handleConfirmDelete}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Deleting...' : 'Yes, Delete Slot'}
              </button>
              <button
                type="button"
                className="secondary-button"
                style={{ fontSize: '11px', padding: '5px 12px' }}
                onClick={() => setDeleteConfirmation(null)}
                disabled={isSubmitting}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Existing Time Slots List */}
        <div className="slots-list" style={{ marginTop: '16px', display: 'grid', gap: '8px', maxHeight: '280px', overflowY: 'auto' }}>
          {timeSlots.map((slot, index) => (
            <div
              key={slot.id || slot.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                background: editingId === slot.id ? 'var(--color-primary-light)' : '#FAFBFD',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', width: '20px' }}>
                  #{index + 1}
                </span>
                <Clock size={14} color="var(--color-primary)" />
                <span style={{ fontWeight: '700', fontSize: '13px' }}>{slot.label}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  title="Edit time slot"
                  onClick={() => handleStartEdit(slot)}
                  disabled={isSubmitting}
                  style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', padding: '4px' }}
                >
                  <Edit2 size={13} />
                </button>
                <button
                  type="button"
                  title="Delete time slot"
                  onClick={() => setDeleteConfirmation(slot)}
                  disabled={isSubmitting}
                  style={{ background: 'none', border: 'none', color: '#DC2626', cursor: 'pointer', padding: '4px' }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add / Edit Time Slot Form */}
        <form onSubmit={handleSave} style={{ marginTop: '16px', padding: '14px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
          <h4 style={{ margin: '0 0 10px', fontSize: '12px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '6px' }}>
            {editingId ? <Edit2 size={14} color="var(--color-primary)" /> : <Plus size={14} color="var(--color-primary)" />}
            {editingId ? 'Edit Selected Time Slot' : 'Add New Time Slot'}
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '10px', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                Start Time (e.g. 9:00 AM)
              </label>
              <input
                type="text"
                placeholder="e.g. 9:00 AM"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                style={{ width: '100%', padding: '7px 10px', fontSize: '12px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                End Time (e.g. 11:00 AM)
              </label>
              <input
                type="text"
                placeholder="e.g. 11:00 AM"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
                style={{ width: '100%', padding: '7px 10px', fontSize: '12px' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="submit"
                className="primary-button"
                disabled={isSubmitting || !startTime.trim() || !endTime.trim()}
                style={{ padding: '7px 14px', fontSize: '12px' }}
              >
                {isSubmitting ? 'Saving...' : editingId ? 'Update' : '+ Add Slot'}
              </button>
              {editingId && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleCancelEdit}
                  style={{ padding: '7px 10px', fontSize: '12px' }}
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </form>

        <div className="modal-actions" style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
          <button type="button" className="secondary-button" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
