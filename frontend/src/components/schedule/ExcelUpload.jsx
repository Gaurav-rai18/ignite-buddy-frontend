/**
 * ExcelUpload.jsx — Spreadsheet Upload, Validation & Parsing UI.
 *
 * Responsibilities:
 *  - Drag-and-drop zone supporting `.xlsx` and `.xls` files (up to 15MB).
 *  - Official Excel Template download banner linked to `/api/schedule-template/`.
 *  - Calls `scheduleService.parseExcel(file)` upon drop/selection to extract
 *    slots across all 7 locations and Monday-Friday working days.
 *  - File summary card showing filename, formatted file size, and 'Verified & Ready' badge.
 *  - File replace and remove actions.
 *  - Surfaces validation warnings (e.g. non-working day warnings).
 */

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  X,
  RefreshCw,
} from 'lucide-react';
import { scheduleService } from '../../services/scheduleService';

export function ExcelUpload({
  file,
  fileName,
  fileSize,
  parsedData,
  onFileSelect,
  onFileRemove,
  disabled,
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const fileInputRef = useRef(null);

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      processFile(droppedFiles[0]);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      processFile(selectedFiles[0]);
    }
  };

  const processFile = async (selectedFile) => {
    setUploadError('');
    setUploadSuccess('');

    // Validate extension (.xlsx, .xls)
    const name = selectedFile.name.toLowerCase();
    if (!name.endsWith('.xlsx') && !name.endsWith('.xls')) {
      setUploadError('Invalid file format. Please upload a valid Microsoft Excel file (.xlsx or .xls).');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await scheduleService.parseExcel(selectedFile);
      if (result && result.success) {
        setUploadSuccess(
          `Excel verified successfully! Extracted ${result.total_rows_parsed || 0} slots across ${result.days_found?.length || 1} day(s).`
        );
        onFileSelect({
          file: selectedFile,
          fileName: selectedFile.name,
          fileSize: selectedFile.size,
          parsedData: result,
        });
      } else {
        const errList = result?.errors || ['Failed to parse Excel schedule.'];
        setUploadError(errList.join(' '));
      }
    } catch (err) {
      setUploadError(err?.message || 'Error uploading and processing Excel spreadsheet.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadTemplate = () => {
    const downloadUrl = scheduleService.getTemplateDownloadUrl();
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'ScheduleTemplate.xlsx';
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="excel-upload-container">
      {/* Template Download Banner */}
      <div className="excel-template-banner">
        <div className="banner-left">
          <FileSpreadsheet size={16} className="text-primary" aria-hidden="true" />
          <span>
            <b>Standardized Excel Template:</b> Download the official timetable spreadsheet formatted with all 7 locations &amp; dynamic batches.
          </span>
        </div>
        <button
          type="button"
          className="template-download-btn"
          onClick={handleDownloadTemplate}
          title="Download Schedule Template (.xlsx)"
        >
          <Download size={13} aria-hidden="true" />
          <span>Download Template (.xlsx)</span>
        </button>
      </div>

      {/* Drag & Drop Zone */}
      {!file ? (
        <div
          className={`excel-dropzone ${isDragging ? 'is-dragging' : ''} ${disabled ? 'is-disabled' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Click or drag Excel spreadsheet to upload"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx, .xls"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            disabled={disabled}
          />
          <div className="dropzone-icon-circle">
            {isProcessing ? (
              <RefreshCw size={26} className="spin-icon" color="var(--color-primary)" />
            ) : (
              <UploadCloud size={28} color="var(--color-primary)" />
            )}
          </div>
          <div className="dropzone-text-group">
            <h4 className="dropzone-title">
              {isProcessing ? 'Validating & parsing spreadsheet...' : 'Drag and drop your timetable Excel file here'}
            </h4>
            <p className="dropzone-sub">
              Supports <b>.xlsx</b> and <b>.xls</b> formats up to 15MB.
            </p>
          </div>
          <button
            type="button"
            className="secondary-button browse-files-btn"
            disabled={disabled || isProcessing}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse Files
          </button>
        </div>
      ) : (
        /* Uploaded File Summary Card */
        <div className="excel-file-card">
          <div className="file-card-main">
            <span className="file-type-icon" aria-hidden="true">
              <FileSpreadsheet size={22} color="#014BAA" />
            </span>
            <div className="file-info">
              <h4 className="file-name">{fileName || file.name}</h4>
              <p className="file-meta">
                <span>{formatFileSize(fileSize || file.size)}</span>
                <span className="meta-bullet">&bull;</span>
                <span className="file-status-badge verified">
                  <CheckCircle2 size={12} aria-hidden="true" /> Verified &amp; Ready
                </span>
              </p>
            </div>
          </div>

          <div className="file-card-actions">
            <button
              type="button"
              className="replace-file-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              title="Replace with another file"
            >
              Replace File
            </button>
            <button
              type="button"
              className="remove-file-btn"
              onClick={onFileRemove}
              disabled={disabled}
              title="Remove uploaded file"
              aria-label="Remove uploaded file"
            >
              <X size={16} aria-hidden="true" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx, .xls"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              disabled={disabled}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {uploadError && (
        <div className="upload-alert error">
          <AlertCircle size={15} aria-hidden="true" style={{ flexShrink: 0 }} />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Success Message */}
      {uploadSuccess && (
        <div className="upload-alert success">
          <CheckCircle2 size={15} aria-hidden="true" style={{ flexShrink: 0 }} />
          <span>{uploadSuccess}</span>
        </div>
      )}
    </div>
  );
}
