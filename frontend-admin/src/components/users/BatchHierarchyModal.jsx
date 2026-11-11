import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  Layers,
  Plus,
  Trash2,
  FolderTree,
  Building,
  CheckCircle2,
  AlertCircle,
  Hash,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { Field } from '../ui/Field';
import { usersService } from '../../services/usersService';

export function BatchHierarchyModal({
  isOpen,
  onClose,
  onHierarchyUpdated,
  defaultTab = 'subbatches',
}) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Loaded Data
  const [cohorts, setCohorts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [subBatches, setSubBatches] = useState([]);
  const [labs, setLabs] = useState([]);

  // Forms State
  const [newCohort, setNewCohort] = useState({
    code: '',
    name: '',
    start_date: '',
    end_date: '',
    is_active: true,
  });

  const [newBatch, setNewBatch] = useState({
    cohort: '',
    name: '',
    description: '',
  });

  const [newSubBatch, setNewSubBatch] = useState({
    batch: '',
    name: '',
    lab: '',
  });

  const [newLab, setNewLab] = useState({
    name: '',
    capacity: 35,
    location: '',
  });

  const [actionLoading, setActionLoading] = useState(false);

  // Load all hierarchy entities
  const loadAllData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const [cData, bData, sbData, lData] = await Promise.all([
        usersService.getCohorts(),
        usersService.getBatches(),
        usersService.getSubBatches(),
        usersService.getLabs(),
      ]);

      const cList = Array.isArray(cData) ? cData : [];
      const bList = Array.isArray(bData) ? bData : [];
      const sbList = Array.isArray(sbData) ? sbData : [];
      const lList = Array.isArray(lData) ? lData : [];

      setCohorts(cList);
      setBatches(bList);
      setSubBatches(sbList);
      setLabs(lList);

      // Set default select dropdown values if empty
      if (cList.length > 0 && !newBatch.cohort) {
        setNewBatch((prev) => ({ ...prev, cohort: cList[0].id }));
      }
      if (bList.length > 0 && !newSubBatch.batch) {
        setNewSubBatch((prev) => ({ ...prev, batch: bList[0].id }));
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load batch hierarchy data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      loadAllData();
      setErrorMsg('');
      setSuccessMsg('');
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

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

  // Handlers for Add Operations
  const handleAddCohort = async (e) => {
    e.preventDefault();
    if (!newCohort.code.trim()) {
      setErrorMsg('Cohort code is required (e.g. B50, B51).');
      return;
    }
    setActionLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        code: newCohort.code.trim().toUpperCase(),
        name: newCohort.name.trim() || `TCS Ignite ${newCohort.code.trim().toUpperCase()}`,
        start_date: newCohort.start_date || null,
        end_date: newCohort.end_date || null,
        is_active: newCohort.is_active,
      };
      await usersService.createCohort(payload);
      setSuccessMsg(`Cohort ${payload.code} created successfully.`);
      setNewCohort({ code: '', name: '', start_date: '', end_date: '', is_active: true });
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.response?.data?.code?.[0] || err.message || 'Failed to create cohort.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddBatch = async (e) => {
    e.preventDefault();
    if (!newBatch.cohort) {
      setErrorMsg('Please select a Cohort.');
      return;
    }
    if (!newBatch.name.trim()) {
      setErrorMsg('Batch name is required (e.g. A, B, C, D).');
      return;
    }
    setActionLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        cohort: parseInt(newBatch.cohort, 10),
        name: newBatch.name.trim().toUpperCase(),
        description: newBatch.description.trim(),
      };
      await usersService.createBatch(payload);
      setSuccessMsg(`Batch ${payload.name} created successfully.`);
      setNewBatch((prev) => ({ ...prev, name: '', description: '' }));
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.response?.data?.non_field_errors?.[0] || err.message || 'Failed to create batch.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddSubBatch = async (e) => {
    e.preventDefault();
    if (!newSubBatch.batch) {
      setErrorMsg('Please select a Batch.');
      return;
    }
    if (!newSubBatch.name.trim()) {
      setErrorMsg('Sub-batch name is required (e.g. A1, A2, B1, C4).');
      return;
    }
    setActionLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        batch: parseInt(newSubBatch.batch, 10),
        name: newSubBatch.name.trim().toUpperCase(),
        lab: newSubBatch.lab ? parseInt(newSubBatch.lab, 10) : null,
      };
      await usersService.createSubBatch(payload);
      setSuccessMsg(`Sub-batch ${payload.name} created successfully.`);
      setNewSubBatch((prev) => ({ ...prev, name: '' }));
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.response?.data?.non_field_errors?.[0] || err.message || 'Failed to create sub-batch.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddLab = async (e) => {
    e.preventDefault();
    if (!newLab.name.trim()) {
      setErrorMsg('Lab name is required (e.g. Lab 1, TR1, WA, TS).');
      return;
    }
    setActionLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        name: newLab.name.trim(),
        capacity: parseInt(newLab.capacity, 10) || 35,
        location: newLab.location.trim(),
      };
      await usersService.createLab(payload);
      setSuccessMsg(`Lab ${payload.name} created successfully.`);
      setNewLab({ name: '', capacity: 35, location: '' });
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.response?.data?.name?.[0] || err.message || 'Failed to create lab.');
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Handlers
  const handleDeleteSubBatch = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete sub-batch ${name}?`)) return;
    try {
      await usersService.deleteSubBatch(id);
      setSuccessMsg(`Sub-batch ${name} deleted.`);
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to delete sub-batch.');
    }
  };

  const handleDeleteBatch = async (id, name) => {
    if (!window.confirm(`Delete batch ${name}? All sub-batches under it will also be removed!`)) return;
    try {
      await usersService.deleteBatch(id);
      setSuccessMsg(`Batch ${name} deleted.`);
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to delete batch.');
    }
  };

  const handleDeleteCohort = async (id, code) => {
    if (!window.confirm(`Delete cohort ${code}? All batches and sub-batches under it will also be removed!`)) return;
    try {
      await usersService.deleteCohort(id);
      setSuccessMsg(`Cohort ${code} deleted.`);
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to delete cohort.');
    }
  };

  const handleDeleteLab = async (id, name) => {
    if (!window.confirm(`Delete room/lab ${name}?`)) return;
    try {
      await usersService.deleteLab(id);
      setSuccessMsg(`Lab ${name} deleted.`);
      await loadAllData();
      if (onHierarchyUpdated) onHierarchyUpdated();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to delete lab.');
    }
  };

  return createPortal(
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="hierarchy-modal-title"
      onClick={onClose}
    >
      <div
        className="modal-card"
        style={{ maxWidth: '820px', width: '92vw', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Head */}
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="entry-icon" aria-hidden="true" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' }}>
              <Layers size={18} />
            </span>
            <div>
              <h3 id="hierarchy-modal-title" style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                Manage Cohorts, Batches & Labs
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary, #94a3b8)' }}>
                Dynamically define cohorts, major tracks, lab groups and venues for TCS Ignite.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close batch hierarchy modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))',
            padding: '12px 20px 0 20px',
            background: 'var(--bg-card-header, rgba(255, 255, 255, 0.02))',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('subbatches')}
            style={{
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: activeTab === 'subbatches' ? 600 : 400,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'subbatches' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent',
              color: activeTab === 'subbatches' ? 'var(--color-primary, #3b82f6)' : 'var(--text-secondary, #94a3b8)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <FolderTree size={14} />
            Sub-Batches
            <span
              style={{
                fontSize: '11px',
                padding: '1px 6px',
                borderRadius: '10px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
              }}
            >
              {subBatches.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('batches')}
            style={{
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: activeTab === 'batches' ? 600 : 400,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'batches' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent',
              color: activeTab === 'batches' ? 'var(--color-primary, #3b82f6)' : 'var(--text-secondary, #94a3b8)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Layers size={14} />
            Batches (Tracks)
            <span
              style={{
                fontSize: '11px',
                padding: '1px 6px',
                borderRadius: '10px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
              }}
            >
              {batches.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('cohorts')}
            style={{
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: activeTab === 'cohorts' ? 600 : 400,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'cohorts' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent',
              color: activeTab === 'cohorts' ? 'var(--color-primary, #3b82f6)' : 'var(--text-secondary, #94a3b8)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Hash size={14} />
            Cohorts (Intakes)
            <span
              style={{
                fontSize: '11px',
                padding: '1px 6px',
                borderRadius: '10px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
              }}
            >
              {cohorts.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('labs')}
            style={{
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: activeTab === 'labs' ? 600 : 400,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'labs' ? '2px solid var(--color-primary, #3b82f6)' : '2px solid transparent',
              color: activeTab === 'labs' ? 'var(--color-primary, #3b82f6)' : 'var(--text-secondary, #94a3b8)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Building size={14} />
            Labs & Venues
            <span
              style={{
                fontSize: '11px',
                padding: '1px 6px',
                borderRadius: '10px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
              }}
            >
              {labs.length}
            </span>
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
          {/* Notifications */}
          {errorMsg && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '6px',
                color: '#ef4444',
                fontSize: '13px',
                marginBottom: '16px',
              }}
            >
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'rgba(34, 197, 94, 0.1)',
                border: '1px solid rgba(34, 197, 94, 0.25)',
                borderRadius: '6px',
                color: '#22c55e',
                fontSize: '13px',
                marginBottom: '16px',
              }}
            >
              <CheckCircle2 size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* TAB 1: SUB-BATCHES */}
          {activeTab === 'subbatches' && (
            <div>
              {/* Quick Add Card */}
              <div
                style={{
                  background: 'var(--bg-card-nested, rgba(255, 255, 255, 0.03))',
                  border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Plus size={16} style={{ color: 'var(--color-primary, #3b82f6)' }} />
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>Create New Sub-Batch (e.g. A3, A4, B1)</span>
                </div>
                <form onSubmit={handleAddSubBatch}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr auto', gap: '12px', alignItems: 'flex-end' }}>
                    <Field label="Parent Batch" htmlFor="sb-batch-select">
                      <select
                        id="sb-batch-select"
                        value={newSubBatch.batch}
                        onChange={(e) => setNewSubBatch({ ...newSubBatch, batch: e.target.value })}
                        required
                      >
                        <option value="">Select Batch...</option>
                        {batches.map((b) => (
                          <option key={b.id} value={b.id}>
                            {b.cohort_code ? `${b.cohort_code} - ` : ''}Batch {b.name}
                          </option>
                        ))}
                      </select>
                    </Field>

                    <Field label="Sub-Batch Name" htmlFor="sb-name">
                      <input
                        id="sb-name"
                        placeholder="e.g. A3, B2, C1"
                        value={newSubBatch.name}
                        onChange={(e) => setNewSubBatch({ ...newSubBatch, name: e.target.value })}
                        required
                      />
                    </Field>

                    <Field label="Designated Home Lab" htmlFor="sb-lab">
                      <select
                        id="sb-lab"
                        value={newSubBatch.lab}
                        onChange={(e) => setNewSubBatch({ ...newSubBatch, lab: e.target.value })}
                      >
                        <option value="">No Lab Assigned</option>
                        {labs.map((l) => (
                          <option key={l.id} value={l.id}>
                            {l.name} {l.location ? `(${l.location})` : ''}
                          </option>
                        ))}
                      </select>
                    </Field>

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={actionLoading}
                      style={{ height: '38px', padding: '0 16px', marginBottom: '2px' }}
                    >
                      <Plus size={14} />
                      Add Sub-Batch
                    </button>
                  </div>
                </form>
              </div>

              {/* Sub-Batches Table */}
              <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)', marginBottom: '10px' }}>
                Existing Sub-Batches ({subBatches.length})
              </h4>
              <div style={{ border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.03)', textAlign: 'left', borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))' }}>
                      <th style={{ padding: '10px 14px' }}>Sub-Batch Code</th>
                      <th style={{ padding: '10px 14px' }}>Batch</th>
                      <th style={{ padding: '10px 14px' }}>Cohort</th>
                      <th style={{ padding: '10px 14px' }}>Designated Home Lab</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subBatches.length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary, #94a3b8)' }}>
                          No sub-batches defined yet. Use the form above to add sub-batches.
                        </td>
                      </tr>
                    ) : (
                      subBatches.map((sb) => (
                        <tr key={sb.id} style={{ borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.05))' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--color-primary, #60a5fa)' }}>
                            {sb.name}
                          </td>
                          <td style={{ padding: '10px 14px' }}>Batch {sb.batch_name}</td>
                          <td style={{ padding: '10px 14px' }}>{sb.cohort_code || '-'}</td>
                          <td style={{ padding: '10px 14px' }}>
                            {sb.lab_name ? (
                              <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(34, 197, 94, 0.1)', color: '#4ade80', fontSize: '12px' }}>
                                {sb.lab_name}
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-secondary, #94a3b8)', fontStyle: 'italic', fontSize: '12px' }}>Unassigned</span>
                            )}
                          </td>
                          <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                            <button
                              type="button"
                              onClick={() => handleDeleteSubBatch(sb.id, sb.name)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                              title="Delete Sub-Batch"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: BATCHES */}
          {activeTab === 'batches' && (
            <div>
              <div
                style={{
                  background: 'var(--bg-card-nested, rgba(255, 255, 255, 0.03))',
                  border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Plus size={16} style={{ color: 'var(--color-primary, #3b82f6)' }} />
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>Create New Major Batch (e.g. A, B, C, D)</span>
                </div>
                <form onSubmit={handleAddBatch}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1.5fr auto', gap: '12px', alignItems: 'flex-end' }}>
                    <Field label="Select Cohort" htmlFor="batch-cohort">
                      <select
                        id="batch-cohort"
                        value={newBatch.cohort}
                        onChange={(e) => setNewBatch({ ...newBatch, cohort: e.target.value })}
                        required
                      >
                        <option value="">Select Cohort...</option>
                        {cohorts.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.code} {c.name ? `(${c.name})` : ''}
                          </option>
                        ))}
                      </select>
                    </Field>

                    <Field label="Batch Name / Letter" htmlFor="batch-name">
                      <input
                        id="batch-name"
                        placeholder="e.g. A, B, C, D"
                        value={newBatch.name}
                        onChange={(e) => setNewBatch({ ...newBatch, name: e.target.value })}
                        required
                      />
                    </Field>

                    <Field label="Description (Optional)" htmlFor="batch-desc">
                      <input
                        id="batch-desc"
                        placeholder="e.g. Core Java Track, Morning Section"
                        value={newBatch.description}
                        onChange={(e) => setNewBatch({ ...newBatch, description: e.target.value })}
                      />
                    </Field>

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={actionLoading}
                      style={{ height: '38px', padding: '0 16px', marginBottom: '2px' }}
                    >
                      <Plus size={14} />
                      Add Batch
                    </button>
                  </div>
                </form>
              </div>

              <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)', marginBottom: '10px' }}>
                Existing Batches ({batches.length})
              </h4>
              <div style={{ border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.03)', textAlign: 'left', borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))' }}>
                      <th style={{ padding: '10px 14px' }}>Batch Name</th>
                      <th style={{ padding: '10px 14px' }}>Full Code</th>
                      <th style={{ padding: '10px 14px' }}>Cohort</th>
                      <th style={{ padding: '10px 14px' }}>Description</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary, #94a3b8)' }}>
                          No batches found.
                        </td>
                      </tr>
                    ) : (
                      batches.map((b) => (
                        <tr key={b.id} style={{ borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.05))' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600 }}>Batch {b.name}</td>
                          <td style={{ padding: '10px 14px', color: 'var(--color-primary, #60a5fa)' }}>{b.full_code || `${b.cohort_code}-${b.name}`}</td>
                          <td style={{ padding: '10px 14px' }}>{b.cohort_code || '-'}</td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-secondary, #94a3b8)' }}>{b.description || '-'}</td>
                          <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                            <button
                              type="button"
                              onClick={() => handleDeleteBatch(b.id, b.name)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                              title="Delete Batch"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: COHORTS */}
          {activeTab === 'cohorts' && (
            <div>
              <div
                style={{
                  background: 'var(--bg-card-nested, rgba(255, 255, 255, 0.03))',
                  border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Plus size={16} style={{ color: 'var(--color-primary, #3b82f6)' }} />
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>Create New Cohort (e.g. B50, B51)</span>
                </div>
                <form onSubmit={handleAddCohort}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr 1fr auto', gap: '12px', alignItems: 'flex-end' }}>
                    <Field label="Cohort Code" htmlFor="cohort-code">
                      <input
                        id="cohort-code"
                        placeholder="e.g. B51"
                        value={newCohort.code}
                        onChange={(e) => setNewCohort({ ...newCohort, code: e.target.value })}
                        required
                      />
                    </Field>

                    <Field label="Cohort Name" htmlFor="cohort-name">
                      <input
                        id="cohort-name"
                        placeholder="e.g. TCS Ignite Batch 51"
                        value={newCohort.name}
                        onChange={(e) => setNewCohort({ ...newCohort, name: e.target.value })}
                      />
                    </Field>

                    <Field label="Start Date" htmlFor="cohort-start">
                      <input
                        id="cohort-start"
                        type="date"
                        value={newCohort.start_date}
                        onChange={(e) => setNewCohort({ ...newCohort, start_date: e.target.value })}
                      />
                    </Field>

                    <Field label="End Date" htmlFor="cohort-end">
                      <input
                        id="cohort-end"
                        type="date"
                        value={newCohort.end_date}
                        onChange={(e) => setNewCohort({ ...newCohort, end_date: e.target.value })}
                      />
                    </Field>

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={actionLoading}
                      style={{ height: '38px', padding: '0 16px', marginBottom: '2px' }}
                    >
                      <Plus size={14} />
                      Add Cohort
                    </button>
                  </div>
                </form>
              </div>

              <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)', marginBottom: '10px' }}>
                Existing Cohorts ({cohorts.length})
              </h4>
              <div style={{ border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.03)', textAlign: 'left', borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))' }}>
                      <th style={{ padding: '10px 14px' }}>Code</th>
                      <th style={{ padding: '10px 14px' }}>Full Name</th>
                      <th style={{ padding: '10px 14px' }}>Start Date</th>
                      <th style={{ padding: '10px 14px' }}>End Date</th>
                      <th style={{ padding: '10px 14px' }}>Status</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cohorts.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary, #94a3b8)' }}>
                          No cohorts found.
                        </td>
                      </tr>
                    ) : (
                      cohorts.map((c) => (
                        <tr key={c.id} style={{ borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.05))' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--color-primary, #60a5fa)' }}>{c.code}</td>
                          <td style={{ padding: '10px 14px' }}>{c.name || '-'}</td>
                          <td style={{ padding: '10px 14px' }}>{c.start_date || '-'}</td>
                          <td style={{ padding: '10px 14px' }}>{c.end_date || '-'}</td>
                          <td style={{ padding: '10px 14px' }}>
                            <span style={{ padding: '2px 8px', borderRadius: '4px', background: c.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(148, 163, 184, 0.1)', color: c.is_active ? '#4ade80' : '#94a3b8', fontSize: '12px' }}>
                              {c.is_active ? 'Active' : 'Archived'}
                            </span>
                          </td>
                          <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                            <button
                              type="button"
                              onClick={() => handleDeleteCohort(c.id, c.code)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                              title="Delete Cohort"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: LABS & VENUES */}
          {activeTab === 'labs' && (
            <div>
              <div
                style={{
                  background: 'var(--bg-card-nested, rgba(255, 255, 255, 0.03))',
                  border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Plus size={16} style={{ color: 'var(--color-primary, #3b82f6)' }} />
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>Create New Lab or Venue (e.g. Lab 2, TR1, WA, TS)</span>
                </div>
                <form onSubmit={handleAddLab}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1.5fr auto', gap: '12px', alignItems: 'flex-end' }}>
                    <Field label="Venue / Lab Name" htmlFor="lab-name">
                      <input
                        id="lab-name"
                        placeholder="e.g. Lab 2, TR1, TS, WA"
                        value={newLab.name}
                        onChange={(e) => setNewLab({ ...newLab, name: e.target.value })}
                        required
                      />
                    </Field>

                    <Field label="Seating Capacity" htmlFor="lab-cap">
                      <input
                        id="lab-cap"
                        type="number"
                        placeholder="e.g. 35"
                        value={newLab.capacity}
                        onChange={(e) => setNewLab({ ...newLab, capacity: e.target.value })}
                      />
                    </Field>

                    <Field label="Location / Wing (Optional)" htmlFor="lab-loc">
                      <input
                        id="lab-loc"
                        placeholder="e.g. 1st Floor, Academic Block"
                        value={newLab.location}
                        onChange={(e) => setNewLab({ ...newLab, location: e.target.value })}
                      />
                    </Field>

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={actionLoading}
                      style={{ height: '38px', padding: '0 16px', marginBottom: '2px' }}
                    >
                      <Plus size={14} />
                      Add Lab
                    </button>
                  </div>
                </form>
              </div>

              <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary, #94a3b8)', marginBottom: '10px' }}>
                Existing Labs & Venues ({labs.length})
              </h4>
              <div style={{ border: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.03)', textAlign: 'left', borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.08))' }}>
                      <th style={{ padding: '10px 14px' }}>Lab / Room Name</th>
                      <th style={{ padding: '10px 14px' }}>Capacity</th>
                      <th style={{ padding: '10px 14px' }}>Location</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {labs.length === 0 ? (
                      <tr>
                        <td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary, #94a3b8)' }}>
                          No labs found.
                        </td>
                      </tr>
                    ) : (
                      labs.map((l) => (
                        <tr key={l.id} style={{ borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.05))' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600 }}>{l.name}</td>
                          <td style={{ padding: '10px 14px' }}>{l.capacity} trainees</td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-secondary, #94a3b8)' }}>{l.location || '-'}</td>
                          <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                            <button
                              type="button"
                              onClick={() => handleDeleteLab(l.id, l.name)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                              title="Delete Lab"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

