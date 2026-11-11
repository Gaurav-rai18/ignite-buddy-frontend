import React from "react";
import { Megaphone, X, Clock, ChevronRight } from "lucide-react";

/**
 * Modal displaying the past 5 recent broadcasted messages.
 */
export default function RecentBroadcastsModal({ history, onSelect, onClose }) {
  return (
    <div className="recent-broadcasts-panel" data-hit role="dialog" aria-label="Recent Announcements">
      <header className="recent-broadcasts-header">
        <div className="recent-broadcasts-title">
          <Megaphone size={14} className="text-amber" />
          <span>Recent Announcements</span>
        </div>
        <button
          type="button"
          className="broadcast-card-close"
          onClick={onClose}
          title="Close recent announcements"
          aria-label="Close"
        >
          <X size={14} />
        </button>
      </header>

      <div className="recent-broadcasts-list">
        {history.length === 0 ? (
          <div className="recent-broadcasts-empty">
            <span>No broadcast announcements yet.</span>
          </div>
        ) : (
          history.map((item, idx) => {
            const timeStr = item.created_at
              ? new Date(item.created_at).toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })
              : item.timestamp
                ? new Date(item.timestamp).toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
                : "Recently";

            return (
              <button
                key={item.id || idx}
                type="button"
                className="recent-broadcast-item"
                onClick={() => {
                  onSelect(item);
                  onClose();
                }}
              >
                <div className="recent-item-main">
                  <div className="recent-item-top">
                    <span className="recent-item-title">{item.title || "Announcement"}</span>
                    <span className="recent-item-time">
                      <Clock size={10} />
                      {timeStr}
                    </span>
                  </div>
                  <p className="recent-item-snippet">
                    {(item.message || item.text || "").replace(/[#*`_]/g, "").slice(0, 90)}
                    {(item.message || item.text || "").length > 90 ? "..." : ""}
                  </p>
                </div>
                <ChevronRight size={14} className="recent-item-arrow" />
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

