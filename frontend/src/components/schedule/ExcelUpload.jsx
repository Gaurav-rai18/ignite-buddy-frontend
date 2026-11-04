import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  X,
  RefreshCw,
  Eye,
  Clock,
  BookOpen,
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
  const [previewDay, setPreviewDay] = useState('');
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

    // Validate extension
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
          `Timetable parsed successfully! Extracted ${result.total_rows_parsed || 0} slots across ${result.days_found?.length || 1} day(s).`
        );
        setPreviewDay(result.selected_day || 'Monday');
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

  // Days found in parsed data
  const daysFound = parsedData?.days_found || (parsedData?.days_data ? Object.keys(parsedData.days_data) : []);
  const activeDay = previewDay || (daysFound.length > 0 ? daysFound[0] : 'Monday');
  const activeDayGrid = parsedData?.days_data?.[activeDay] || parsedData?.grid || {};
  const activeDayTimeSlots = Object.keys(activeDayGrid);

  return (
    <div className="excel-upload-container">
      {/* Template Download Banner */}
      <div className="excel-template-banner">
        <div className="banner-left">
          <FileSpreadsheet size={16} className="text-primary" aria-hidden="true" />
          <span>
            <b>Standardized Excel Template:</b> Download the official timetable spreadsheet formatted with Lab 1–4, Work Area, TR1, TR2 &amp; dynamic batches.
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

      {/* Parsed Timetable Interactive Preview */}
      {parsedData && (
        <div className="excel-preview-section">
          <div className="preview-heading-row">
            <div className="heading-left">
              <Eye size={15} className="text-primary" aria-hidden="true" />
              <span>
                <b>Timetable Preview</b> &bull; Verify parsed slots before publishing
              </span>
            </div>

            {/* Day Switcher if multiple days found */}
            {daysFound.length > 1 && (
              <div className="preview-day-tabs">
                {daysFound.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={`preview-day-pill ${d === activeDay ? 'active' : ''}`}
                    onClick={() => setPreviewDay(d)}
                  >
                    {d}
                  </button>
                ))}
              </div>
            )}
          </div>

          {activeDayTimeSlots.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '12px' }}>
              No slots scheduled for {activeDay}.
            </div>
          ) : (
            <div className="excel-preview-table-wrapper" style={{ overflowX: 'auto' }}>
              <table className="schedule-builder-table excel-preview-table">
                <thead>
                  <tr>
                    <th style={{ width: '130px' }}>Time Slot</th>
                    <th>Lab / Location</th>
                    <th>Topic / Subject</th>
                    <th>Assigned Batches</th>
                  </tr>
                </thead>
                <tbody>
                  {activeDayTimeSlots.map((time) => {
                    const locationsInSlot = activeDayGrid[time] || {};
                    const locKeys = Object.keys(locationsInSlot);

                    return locKeys.map((loc, lIdx) => {
                      const cell = locationsInSlot[loc];
                      const subbatches = cell?.subbatches || [];

                      return (
                        <tr key={`${time}-${loc}`}>
                          {lIdx === 0 && (
                            <td className="time-cell" rowSpan={locKeys.length} style={{ verticalAlign: 'top' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Clock size={12} aria-hidden="true" />
                                <span>{time}</span>
                              </div>
                            </td>
                          )}
                          <td style={{ fontWeight: '700', fontSize: '12px', color: '#014BAA' }}>{loc}</td>
                          <td style={{ fontSize: '12px' }}>
                            {cell?.topic ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <BookOpen size={12} color="var(--color-primary)" />
                                <span>{cell.topic}</span>
                              </div>
                            ) : (
                              <span style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                                (No topic)
                              </span>
                            )}
                          </td>
                          <td>
                            {subbatches.length > 0 ? (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                                {subbatches.map((sb) => (
                                  <span
                                    key={sb}
                                    className="sb-chip active batch-a"
                                    style={{ fontSize: '9px', padding: '2px 5px', pointerEvents: 'none' }}
                                  >
                                    {sb.toUpperCase()}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>
                                All trainees
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    });
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
