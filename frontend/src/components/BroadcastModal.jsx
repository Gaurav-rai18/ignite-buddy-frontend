import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Megaphone, X, Check, Clock } from "lucide-react";

/**
 * Announcement / Broadcast Modal.
 * Displays full announcement details with Markdown formatting.
 */
export default function BroadcastModal({
  broadcast,
  onClose,
  onDismiss,
  onOpenHistory,
}) {
  if (!broadcast) return null;

  const title = broadcast.title || "Campus Announcement";
  const body = broadcast.message || broadcast.text || "";
  const timeStr = broadcast.created_at
    ? new Date(broadcast.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : broadcast.timestamp
    ? new Date(broadcast.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "Just now";

  return (
    <aside
      className="broadcast-popup-card"
      data-hit
      role="dialog"
      aria-modal="true"
      aria-labelledby="broadcast-card-title"
    >
      <header className="broadcast-card-header">
        <div className="broadcast-card-badge">
          <Megaphone size={13} className="broadcast-card-icon" aria-hidden="true" />
          <span>Campus Announcement</span>
          <span className="broadcast-card-time">{timeStr}</span>
        </div>
        <div className="broadcast-header-actions">
          <button
            type="button"
            className="broadcast-card-close"
            onClick={onClose}
            title="Close announcement"
            aria-label="Close announcement"
          >
            <X size={14} />
          </button>
        </div>
      </header>

      <section className="broadcast-card-content">
        <h3 id="broadcast-card-title" className="broadcast-card-title">
          {title}
        </h3>
        <div className="broadcast-card-body markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
            {body}
          </ReactMarkdown>
        </div>
      </section>

      <footer className="broadcast-card-footer">
        {onOpenHistory && (
          <button
            type="button"
            className="broadcast-card-history-btn"
            onClick={onOpenHistory}
            title="View recent announcements"
          >
            <Clock size={12} aria-hidden="true" />
            <span>Recent</span>
          </button>
        )}
        <button
          type="button"
          className="broadcast-card-btn"
          onClick={() => {
            onDismiss?.(broadcast.id);
            onClose();
          }}
        >
          <Check size={13} aria-hidden="true" />
          <span>Got it</span>
        </button>
      </footer>
    </aside>
  );
}
