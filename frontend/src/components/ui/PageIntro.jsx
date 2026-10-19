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
