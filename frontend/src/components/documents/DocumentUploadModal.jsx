import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, FileText, X, AlertCircle } from 'lucide-react';
import { formatFileSize } from '../../services/documentsService';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.txt'];

export function DocumentUploadModal({ isOpen, onClose, onUpload }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [audience, setAudience] = useState('All students');
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
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, uploading]);

  useEffect(() => {
    if (isOpen) {
      setFile(null);
      setName('');
      setDescription('');
      setAudience('All students');
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
    if (uploading) return; // Prevent duplicate submission

    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await onUpload({
        file,
        name: name.trim() || file.name.replace(/\.[^/.]+$/, ''),
        audience,
        description,
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
      onClick={() => {
        if (!uploading) onClose();
      }}
    >
      <div className="modal-card" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="entry-icon" aria-hidden="true">
              <UploadCloud size={16} />
            </span>
            <div>
              <h3 id="upload-modal-title">Upload document</h3>
            </div>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            disabled={uploading}
            aria-label="Close upload modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: '0 0 16px', lineHeight: '1.5' }}>
          Add a PDF or text file to your knowledge base for RAG extraction and indexing.
        </p>

        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 12px',
              background: 'var(--color-danger-bg)',
              color: 'var(--color-danger)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              marginBottom: '14px',
              border: '1px solid #F5C7CD',
            }}
            role="alert"
          >
            <AlertCircle size={15} style={{ flexShrink: 0 }} aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-layout" noValidate>
          {!file ? (
            <div
              className={`dropzone ${isDragging ? 'dropzone-active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
              aria-label="Upload file dropzone. Click to browse or drag and drop."
            >
              <div className="dropzone-icon" aria-hidden="true">
                <UploadCloud size={32} />
              </div>
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
                placeholder="e.g. Semester Timetable"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={uploading}
              />
            </div>
          )}

          <div className="field">
            <span>Document description / Subject</span>
            <input
              placeholder="e.g. Updated timetable for all departments"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploading}
            />
          </div>

          <div className="field">
            <span>Target audience</span>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              disabled={uploading}
            >
              <option value="All students">All students</option>
              <option value="First year">First year</option>
              <option value="Second year">Second year</option>
              <option value="Third year">Third year</option>
              <option value="Final year">Final year</option>
            </select>
          </div>

          <div className="form-foot" style={{ marginTop: '10px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>
              Text will be extracted & indexed for RAG
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
