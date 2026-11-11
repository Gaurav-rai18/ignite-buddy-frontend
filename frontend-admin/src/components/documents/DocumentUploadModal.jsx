import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, FileText, X, AlertCircle } from 'lucide-react';
import { formatFileSize } from '../../services/documentsService';
import { usersService } from '../../services/usersService';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.txt'];

export function DocumentUploadModal({ isOpen, onClose, onUpload }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetType, setTargetType] = useState('ALL');
  const [targetCohort, setTargetCohort] = useState('');
  const [targetBatch, setTargetBatch] = useState('');
  const [cohorts, setCohorts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && !uploading) {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      usersService.getCohorts().then(setCohorts).catch(() => setCohorts([]));
      usersService.getBatches().then(setBatches).catch(() => setBatches([]));
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, uploading]);

  useEffect(() => {
    if (isOpen) {
      setFile(null);
      setName('');
      setDescription('');
      setTargetType('ALL');
      setTargetCohort('');
      setTargetBatch('');
      setError('');
      setIsDragging(false);
      setUploading(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const validateAndSetFile = (candidateFile) => {
    setError('');
    if (!candidateFile) return;

    const lowerName = candidateFile.name.toLowerCase();
    const isAllowedExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
    if (!isAllowedExt) {
      setError('Please upload a PDF or text file.');
      return;
    }

    if (candidateFile.size > MAX_FILE_SIZE_BYTES) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }

    if (candidateFile.size === 0) {
      setError('The selected file is empty.');
      return;
    }

    setFile(candidateFile);
    if (!name) {
      setName(candidateFile.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (uploading) return;

    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    setError('');

    let audienceLabel = 'All Trainees';
    if (targetType === 'COHORT' && targetCohort) {
      const c = cohorts.find((x) => String(x.id) === String(targetCohort));
      audienceLabel = c ? `Cohort ${c.code}` : 'Cohort Targeted';
    } else if (targetType === 'BATCH' && targetBatch) {
      const b = batches.find((x) => String(x.id) === String(targetBatch));
      audienceLabel = b ? `Batch ${b.name}` : 'Batch Targeted';
    }

    try {
      await onUpload({
        file,
        name: name.trim() || file.name.replace(/\.[^/.]+$/, ''),
        audience: audienceLabel,
        description,
        cohort_id: targetCohort || null,
        batch_id: targetBatch || null,
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Unable to upload this document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-modal-title"
      onClick={onClose}
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="entry-icon" aria-hidden="true">
              <UploadCloud size={16} />
            </span>
            <h3 id="upload-modal-title">Upload RAG Knowledge Document</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close upload modal"
            disabled={uploading}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--color-danger)',
              fontSize: '11px',
              marginBottom: '10px',
              padding: '8px 10px',
              background: 'var(--color-danger-bg)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <AlertCircle size={14} aria-hidden="true" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-layout" noValidate>
          {!file ? (
            <div
              className={`dropzone ${isDragging ? 'dragover' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              aria-label="Upload document drag and drop area"
            >
              <UploadCloud size={32} color="var(--color-primary)" aria-hidden="true" />
              <b style={{ fontSize: '12px', color: 'var(--color-text-primary)' }}>
                Drag & drop your file here or click to browse
              </b>
              <p style={{ fontSize: '10px', color: 'var(--color-text-secondary)', margin: '4px 0 0' }}>
                PDF or TXT • Max size 10 MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="file-preview-card">
              <div className="file-preview-icon" aria-hidden="true">
                <FileText size={20} />
              </div>
              <div className="file-preview-meta">
                <b>{file.name}</b>
                <small>
                  {file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : 'TXT'} • {formatFileSize(file.size)}
                </small>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setFile(null)}
                style={{ padding: '6px 10px', fontSize: '10.5px' }}
                aria-label="Remove selected file"
                disabled={uploading}
              >
                Change file
              </button>
            </div>
          )}

          {file && (
            <div className="field">
              <span>Document title / Name</span>
              <input
                placeholder="e.g. TCS Space Safety Guidelines"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={uploading}
              />
            </div>
          )}

          <div className="field">
            <span>Document description / Subject</span>
            <input
              placeholder="e.g. Official lab conduct and assessment policy handbook"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploading}
            />
          </div>

          <div className="field">
            <span>Target audience</span>
            <select
              value={targetType}
              onChange={(e) => {
                setTargetType(e.target.value);
                setTargetCohort('');
                setTargetBatch('');
              }}
              disabled={uploading}
            >
              <option value="ALL">All Trainees (Campus-wide)</option>
              <option value="COHORT">Specific Cohort</option>
              <option value="BATCH">Specific Batch</option>
            </select>
          </div>

          {targetType === 'COHORT' && (
            <div className="field">
              <span>Select Cohort</span>
              <select
                value={targetCohort}
                onChange={(e) => setTargetCohort(e.target.value)}
                disabled={uploading}
              >
                <option value="">Choose a cohort...</option>
                {cohorts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} - {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {targetType === 'BATCH' && (
            <div className="field">
              <span>Select Batch</span>
              <select
                value={targetBatch}
                onChange={(e) => setTargetBatch(e.target.value)}
                disabled={uploading}
              >
                <option value="">Choose a batch...</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.cohort_code ? `${b.cohort_code} - ` : ''}Batch {b.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-foot" style={{ marginTop: '10px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>
              Text will be extracted, chunked & indexed for RAG
            </span>
            <div className="form-foot-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={onClose}
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="primary-button"
                disabled={!file || uploading}
              >
                <UploadCloud size={15} aria-hidden="true" />
                {uploading ? 'Uploading & Processing...' : 'Upload document'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
