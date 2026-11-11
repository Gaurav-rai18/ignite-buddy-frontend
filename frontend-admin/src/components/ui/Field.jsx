import React from 'react';

export function Field({ label, children, htmlFor, error, helpText }) {
  return (
    <label className="field" htmlFor={htmlFor}>
      <span>{label}</span>
      {children}
      {helpText && <small className="field-help">{helpText}</small>}
      {error && (
        <span
          className="field-error"
          role="alert"
          style={{ color: '#d9534f', fontSize: '10px', marginTop: '2px', fontWeight: '600' }}
        >
          {error}
        </span>
      )}
    </label>
  );
}
