import React, { Suspense, lazy } from "react";

const Avatar3D = lazy(() => import("./Avatar3D.jsx"));

/**
 * 2D SVG fallback character when 2D mode is explicitly requested.
 */
export function AvatarFlat({ mood }) {
  return (
    <svg viewBox="0 0 120 140" className={`avatar-flat ${mood}`} aria-hidden="true">
      <circle cx="60" cy="125" r="34" className="af-ring" />
      <rect x="32" y="70" width="56" height="50" rx="24" fill="#2f5bea" />
      <circle cx="60" cy="48" r="32" fill="#f4f6fb" />
      <rect x="36" y="38" width="48" height="24" rx="12" fill="#141a2b" />
      <circle cx="49" cy="50" r="4.5" className="af-eye" />
      <circle cx="71" cy="50" r="4.5" className="af-eye" />
      <rect x="53" y="73" width="14" height="3" rx="1.5" className="af-eye af-mouth" />
      <line x1="60" y1="16" x2="60" y2="6" stroke="#f4f6fb" strokeWidth="2" />
      <circle cx="60" cy="5" r="4" className="af-eye" />
    </svg>
  );
}

// Configurable via environment variable: VITE_AVATAR_RENDER_MODE or VITE_AVATAR_MODE ('2D' or '3D')
// Defaults to '3D'.
const AVATAR_RENDER_MODE = (
  import.meta.env?.VITE_AVATAR_RENDER_MODE ||
  import.meta.env?.VITE_AVATAR_MODE ||
  (typeof window !== "undefined" && (window.__AVATAR_RENDER_MODE__ || window.__AVATAR_MODE__)) ||
  "3D"
).toUpperCase();

/**
 * Main Avatar component.
 * Renders 3D character by default (prioritizing model.glb -> fallback to existing 3D robot).
 * Renders 2D character only if VITE_AVATAR_RENDER_MODE="2D" is explicitly set.
 */
export default function Avatar({ mood, glb, onClick, animationMap }) {
  if (AVATAR_RENDER_MODE === "2D") {
    return (
      <button
        className={`avatar ${mood}`}
        data-hit
        onClick={onClick}
        title="Click or press the shortcut to interact"
        aria-label="Assistant"
      >
        <AvatarFlat mood={mood} />
      </button>
    );
  }

  // 3D Mode: strictly renders 3D without degrading to 2D
  return (
    <button
      className={`avatar ${mood}`}
      data-hit
      onClick={onClick}
      title="Click or press the shortcut to interact"
      aria-label="Assistant"
    >
      <Suspense fallback={<div className="avatar3d-loading" />}>
        <Avatar3D
          mood={mood}
          glb={glb || "/model.glb"}
          animationMap={animationMap}
        />
      </Suspense>
    </button>
  );
}
