/**
 * @file PageIntro.jsx
 * @description Reusable page header section with eyebrow label, title, and subtitle.
 * Used at the top of each main page for consistent layout.
 * @param {Object} props - { eyebrow, title, subtitle }
 */
import React from 'react';

export function PageIntro({ eyebrow, title, subtitle }) {
  return (
    <div className="page-intro">
      <div className="eyebrow">
        <span className="eyebrow-line" aria-hidden="true" />
        {eyebrow}
      </div>
      <h1>{title}</h1>
      <p className="subheading">{subtitle}</p>
    </div>
  );
}
