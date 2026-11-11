import React, { useState } from "react";
import { X, Upload } from "lucide-react";
import { createPortal } from "react-dom";

export function BulkUploadUserModal({
  isOpen,
  onClose,
  onUpload,
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] =
    useState(false);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!file) {
      alert("Select an Excel file");
      return;
    }

    try {
      setUploading(true);

      await onUpload(file);

      onClose();
    } finally {
      setUploading(false);
    }
  };

  return createPortal(
    <div
      className="modal-overlay"
      onClick={onClose}
    >
      <div
        className="modal-card"
        onClick={(e) =>
          e.stopPropagation()
        }
      >
        <div className="modal-head">
          <h3>
            Bulk Upload Users
          </h3>

          <button
            className="modal-close"
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={(e) =>
            setFile(
              e.target.files[0]
            )
          }
        />

        <div
          style={{
            marginTop: "20px",
          }}
        >
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="primary-button"
          >
            {uploading
              ? "Uploading..."
              : "Upload Users"}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
