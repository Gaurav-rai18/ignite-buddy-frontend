/**
 * BatchManagerModal.jsx — Modal Dialog for Dynamic Batch & Sub-Batch CRUD.
 *
 * Allows administrators to:
 *  - Create new batch groups (e.g. Batch D, Batch E) with auto-generated sub-batches.
 *  - Add custom sub-batches (e.g. A5, B5, D1) under existing batch groups.
 *  - Delete batches or individual sub-batches with safety confirmations.
 *  - Prevents duplicate batch codes/names and sub-batch codes within the same batch.
 *
 * Persists immediately to Django SQLite database via `onAddBatch` / `onRemoveBatch` props.
 */

import React, { useState } from 'react';
import { X, Plus, Trash2, Users, Layers, AlertTriangle, Check } from 'lucide-react';

export function BatchManagerModal({ isOpen, onClose, config, onAddBatch, onRemoveBatch, onAddSubBatch, onRemoveSubBatch }) {
  const [newBatchName, setNewBatchName] = useState('');
  const [newBatchCode, setNewBatchCode] = useState('');
  const [activeSubBatchBatchId, setActiveSubBatchBatchId] = useState(null);
  const [newSubBatchName, setNewSubBatchName] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null); // { type: 'batch'|'sub', id, name, batchId }

  if (!isOpen) return null;

  const batches = config?.batches || [];

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    setError('');
    const code = (newBatchCode || '').trim().toUpperCase();
    const name = (newBatchName || `Batch ${code}`).trim();

    if (!code) {
      setError('Batch letter / code is required (e.g. D, E).');
      return;
    }

    if (batches.some((b) => b.code.toUpperCase() === code)) {
      setError(`Batch "${code}" already exists.`);
      return;
    }

    setIsSubmitting(true);
    try {
      await onAddBatch({ name, code, subbatches_count: 4 });
      setNewBatchName('');
      setNewBatchCode('');
    } catch (err) {
      setError(err?.message || 'Failed to create batch.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateSubBatch = async (batch) => {
    setError('');
    const name = (newSubBatchName || '').trim();
    if (!name) {
      setError('Sub-batch name is required (e.g. A5, B5).');
      return;
    }

    const code = name.toLowerCase();
    if (batch.subbatches?.some((s) => s.code.toLowerCase() === code)) {
      setError(`Sub-batch "${name}" already exists in ${batch.name}.`);
      return;
    }

    setIsSubmitting(true);
    try {
      await onAddSubBatch({
        batch: batch.id,
        name: name.toUpperCase(),
        code,
      });
      setNewSubBatchName('');
      setActiveSubBatchBatchId(null);
    } catch (err) {
      setError(err?.message || 'Failed to create sub-batch.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmation) return;
    setIsSubmitting(true);
    setError('');
    try {
      if (deleteConfirmation.type === 'batch') {
        await onRemoveBatch(deleteConfirmation.id);
      } else if (deleteConfirmation.type === 'sub') {
        await onRemoveSubBatch(deleteConfirmation.id, deleteConfirmation.batchId);
      }
      setDeleteConfirmation(null);
    } catch (err) {
      setError(err?.message || 'Failed to delete item.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="batch-mgr-title" onClick={onClose}>
      <div className="modal-card batch-manager-modal" style={{ maxWidth: '640px', width: '95%' }} onClick={(e) => e.stopPropagation()}>
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
              <Users size={18} />
            </span>
            <div>
              <h3 id="batch-mgr-title" style={{ margin: 0, fontSize: '15px' }}>
                Manage Dynamic Batches &amp; Sub-Batches
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                Add or remove batch groups and individual sub-batches
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

        {/* Delete Confirmation Card */}
        {deleteConfirmation && (
          <div className="delete-confirm-box" style={{ margin: '14px 0 0', padding: '12px 14px', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '8px' }}>
            <p style={{ margin: '0 0 10px', fontSize: '12px', fontWeight: '600', color: '#92400E' }}>
              Are you sure you want to delete {deleteConfirmation.type === 'batch' ? 'batch' : 'sub-batch'} &quot;{deleteConfirmation.name}&quot;?
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="danger-button"
                style={{ fontSize: '11px', padding: '5px 12px' }}
                onClick={handleConfirmDelete}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Deleting...' : 'Yes, Delete'}
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

        {/* Existing Batches List */}
        <div className="batches-list-container" style={{ marginTop: '16px', display: 'grid', gap: '12px', maxHeight: '340px', overflowY: 'auto' }}>
          {batches.map((b) => (
            <div key={b.id || b.code} className="batch-row-card" style={{ padding: '12px 14px', border: '1px solid var(--color-border)', borderRadius: '8px', background: '#FAFBFD' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="batch-group-tag" style={{ background: '#014BAA', color: '#FFF', fontWeight: '700', fontSize: '11px', padding: '2px 8px', borderRadius: '4px' }}>
                    {b.code}
                  </span>
                  <span style={{ fontWeight: '600', fontSize: '13px' }}>{b.name}</span>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    ({b.subbatches?.length || 0} sub-batches)
                  </span>
                </div>
                <button
                  type="button"
                  className="icon-action-btn delete"
                  title={`Delete ${b.name}`}
                  onClick={() => setDeleteConfirmation({ type: 'batch', id: b.id, name: b.name })}
                  disabled={isSubmitting}
                  style={{ background: 'none', border: 'none', color: '#DC2626', cursor: 'pointer', padding: '4px' }}
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {/* Sub-batches chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                {(b.subbatches || []).map((sb) => (
                  <span
                    key={sb.id || sb.code}
                    className="subbatch-pill"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      background: '#FFF',
                      border: '1px solid var(--color-border)',
                      borderRadius: '4px',
                      padding: '3px 8px',
                      fontSize: '11px',
                      fontWeight: '600',
                    }}
                  >
                    <span>{sb.name}</span>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmation({ type: 'sub', id: sb.id, name: sb.name, batchId: b.id })}
                      disabled={isSubmitting}
                      style={{ background: 'none', border: 'none', color: '#9CA3AF', cursor: 'pointer', padding: 0, display: 'grid' }}
                      title={`Remove ${sb.name}`}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}

                {/* Add Sub-Batch inline control */}
                {activeSubBatchBatchId === b.id ? (
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <input
                      type="text"
                      placeholder={`e.g. ${b.code}5`}
                      value={newSubBatchName}
                      onChange={(e) => setNewSubBatchName(e.target.value)}
                      style={{ width: '70px', padding: '3px 6px', fontSize: '11px', borderRadius: '4px', border: '1px solid var(--color-primary)' }}
                      autoFocus
                    />
                    <button
                      type="button"
                      className="primary-button"
                      style={{ padding: '3px 7px', fontSize: '10px' }}
                      onClick={() => handleCreateSubBatch(b)}
                      disabled={isSubmitting}
                    >
                      Add
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      style={{ padding: '3px 6px', fontSize: '10px' }}
                      onClick={() => {
                        setActiveSubBatchBatchId(null);
                        setNewSubBatchName('');
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="add-subbatch-btn"
                    onClick={() => {
                      setActiveSubBatchBatchId(b.id);
                      const nextNum = (b.subbatches?.length || 0) + 1;
                      setNewSubBatchName(`${b.code}${nextNum}`);
                    }}
                    style={{
                      border: '1px dashed var(--color-primary)',
                      background: 'none',
                      color: 'var(--color-primary)',
                      fontSize: '10.5px',
                      fontWeight: '600',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Plus size={12} /> Add Sub-Batch
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Add New Batch Form */}
        <form onSubmit={handleCreateBatch} style={{ marginTop: '16px', padding: '14px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
          <h4 style={{ margin: '0 0 10px', fontSize: '12px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Plus size={14} color="var(--color-primary)" /> Add New Batch Group
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr auto', gap: '8px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--color-text-secondary)', marginBottom: '3px' }}>
                Code *
              </label>
              <input
                type="text"
                maxLength={4}
                placeholder="e.g. D"
                value={newBatchCode}
                onChange={(e) => {
                  const val = e.target.value.toUpperCase();
                  setNewBatchCode(val);
                  if (!newBatchName || newBatchName.startsWith('Batch ')) {
                    setNewBatchName(val ? `Batch ${val}` : '');
                  }
                }}
                style={{ textTransform: 'uppercase', padding: '6px 8px', fontSize: '12px', width: '100%' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '10.5px', color: 'var(--color-text-secondary)', marginBottom: '3px' }}>
                Batch Title
              </label>
              <input
                type="text"
                placeholder="e.g. Batch D (Cloud)"
                value={newBatchName}
                onChange={(e) => setNewBatchName(e.target.value)}
                style={{ padding: '6px 8px', fontSize: '12px', width: '100%' }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                type="submit"
                className="primary-button"
                disabled={isSubmitting || !newBatchCode.trim()}
                style={{ padding: '7px 14px', fontSize: '12px' }}
              >
                {isSubmitting ? 'Adding...' : '+ Add Batch'}
              </button>
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

