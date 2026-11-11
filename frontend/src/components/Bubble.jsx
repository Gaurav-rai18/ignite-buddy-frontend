import React, { useEffect, useRef } from "react";
import {
  AlertCircle,
  Bell,
  Bot,
  Brain,
  CheckCircle2,
  ClipboardList,
  File,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  Folder,
  Keyboard,
  Loader2,
  LogOut,
  Megaphone,
  Mic,
  Search,
  Send,
  ShieldAlert,
  Sparkles,
  Square,
  Volume2,
  X,
} from "lucide-react";

/**
 * Cleans internal step numbering prefixes and formats folder/file listings cleanly.
 */
export function cleanStepText(raw) {
  if (!raw) return "";
  let text = String(raw).trim();
  if (text.includes("\n") && (text.includes("[DIR]") || text.includes("[FILE]") || text.includes(" items):"))) {
    const firstLine = text.split("\n")[0].trim();
    return firstLine.replace(/^[A-Z]:\\[^\\]+\\/i, "").replace(/:$/, "");
  }
  text = text.replace(/^(\[\d+\]|\(\d+\)|\d+\.|\bstep\s*\d+:?)\s*/i, "").trim();
  if (text.length > 0) {
    text = text.charAt(0).toUpperCase() + text.slice(1);
  }
  return text
    .replace(/\bgoogle chrome\b/gi, "Google Chrome")
    .replace(/\bchrome\b/gi, "Chrome")
    .replace(/\bvscode\b/gi, "VS Code")
    .replace(/\bvs code\b/gi, "VS Code");
}

function parseFileOption(raw) {
  if (typeof raw !== "string") return { name: String(raw), dir: "", ext: "", isDir: false };
  const parts = raw.split(/[\\/]/).filter(Boolean);
  const name = parts[parts.length - 1] || raw;
  const dir = parts.slice(0, -1).join("\\");
  const extMatch = /\.([a-zA-Z0-9]{1,6})$/.exec(name);
  const isDir = !extMatch && !name.includes(".");
  return {
    name,
    dir: dir.length > 28 ? "..." + dir.slice(-25) : dir,
    fullDir: dir,
    ext: extMatch ? extMatch[1].toUpperCase() : isDir ? "DIR" : "FILE",
    isDir,
  };
}

function getOptionIcon(parsed) {
  if (parsed.isDir) return <Folder size={15} className="file-choice-icon dir" />;
  const e = parsed.ext.toLowerCase();
  if (["py", "js", "jsx", "ts", "tsx", "html", "css", "json", "sh", "bat"].includes(e)) {
    return <FileCode size={15} className="file-choice-icon code" />;
  }
  if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(e)) {
    return <FileImage size={15} className="file-choice-icon img" />;
  }
  if (["csv", "xlsx", "xls"].includes(e)) {
    return <FileSpreadsheet size={15} className="file-choice-icon sheet" />;
  }
  return <FileText size={15} className="file-choice-icon doc" />;
}

/**
 * Cloud-styled speech bubble positioned above the 3D avatar's head.
 */
export default function Bubble({
  state,
  input,
  busy,
  onSubmit,
  onMic,
  onTyping,
  onClose,
  onCancel,
  answer,
  text,
  setText,
  onLogout,
  onInteractChange,
  onFocusChange,
  onOpenBroadcasts,
}) {
  const { turn, heard, dialogs, mic, composerOpen, config, status } = state;
  const inputRef = useRef(null);

  useEffect(() => {
    if (composerOpen && input.enabled) {
      inputRef.current?.focus();
    }
  }, [composerOpen, input.enabled]);

  const dialog = dialogs.find(
    (d) => d.type === "confirm_request" || d.type === "local_confirm" || d.type === "choose_request"
  );

  const isGenerating = turn?.streaming || status === "generating";
  const isThinking = status === "thinking";
  const isExecuting = busy && !turn?.answer;
  const hasSteps = (turn?.steps?.length || 0) > 0;
  const lastStep = hasSteps ? turn.steps[turn.steps.length - 1] : null;
  const didNotCatch =
    hasSteps &&
    turn.steps.some(
      (s) =>
        s.text?.toLowerCase().includes("didn't hear") ||
        s.text?.toLowerCase().includes("didn't catch") ||
        s.text?.toLowerCase().includes("timed out")
    );

  const showComposer =
    composerOpen || didNotCatch || (!busy && (!turn || hasSteps)) || mic.on;

  return (
    <div
      className="bubble-cloud"
      data-hit
      role="log"
      aria-live="polite"
      onMouseEnter={() => onInteractChange?.(true)}
      onMouseLeave={() => onInteractChange?.(false)}
    >
      <div className="bubble-tail" aria-hidden="true" />

      {/* Cloud header: concise status chip and action buttons */}
      <div className="bubble-header">
        <div className="bubble-status">
          {mic.on ? (
            mic.speaking ? (
              <span className="status-chip hearing">
                <Volume2 size={11} className="pulse-icon" />
                <span>Hearing...</span>
              </span>
            ) : (
              <span className="status-chip listening">
                <Mic size={11} className="pulse-icon" />
                <span>Listening...</span>
              </span>
            )
          ) : isGenerating ? (
            <span className="status-chip generating">
              <Sparkles size={11} className="spin-slow" />
              <span>Generating...</span>
            </span>
          ) : isThinking ? (
            <span className="status-chip thinking">
              <Brain size={11} className="pulse-icon" />
              <span>Thinking...</span>
            </span>
          ) : isExecuting ? (
            <span className="status-chip executing">
              <Loader2 size={11} className="spin" />
              <span>Executing...</span>
            </span>
          ) : hasSteps ? (
            <span className={`status-chip ${lastStep?.error ? "error" : "done"}`}>
              {lastStep?.error ? <AlertCircle size={11} /> : <CheckCircle2 size={11} />}
              <span>{lastStep?.error ? "Failed" : "Done"}</span>
            </span>
          ) : (
            <span className="status-chip idle">
              <Bot size={11} />
              <span>Assistant</span>
            </span>
          )}
        </div>

        <div className="bubble-actions">
          {onOpenBroadcasts && (
            <button
              type="button"
              className="bubble-action-btn"
              onClick={onOpenBroadcasts}
              title="Recent announcements"
              aria-label="Recent announcements"
            >
              <Megaphone size={12} className="text-amber" />
            </button>
          )}
          {busy && (
            <button type="button" className="chip-stop" onClick={onCancel} title="Stop action">
              <Square size={9} />
              <span>Stop</span>
            </button>
          )}
          <button type="button" className="bubble-x" onClick={onClose} title="Close (Esc)" aria-label="Close">
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Warning message if disabled */}
      {!input.enabled && (
        <div className="bubble-row warn">
          <ShieldAlert size={14} />
          <span>{input.reason}</span>
        </div>
      )}

      {/* Audio meter when mic is listening */}
      {mic.on && !heard && (
        <div className="bubble-listening-pane">
          <div className="audio-bars" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
          <span className="listening-hint">
            {mic.speaking ? "Hearing you..." : "Speak now... (click mic button to stop)"}
          </span>
          <span className="mic-meter" title="Volume meter">
            <i style={{ width: `${Math.round(mic.level * 100)}%` }} />
          </span>
        </div>
      )}

      {/* Live speech transcription */}
      {heard ? (
        <div className="bubble-heard">
          <Mic size={13} className="heard-icon" />
          <span className="heard-text">
            "{heard}"
            <i className="caret" />
          </span>
        </div>
      ) : turn?.query ? (
        <div className="bubble-query">
          <span className="query-badge" title={turn.voice ? "Spoken query" : "Typed query"}>
            {turn.voice ? <Mic size={11} /> : <Keyboard size={11} />}
          </span>
          <span className="query-text">"{turn.query}"</span>
        </div>
      ) : isThinking ? (
        <div className="bubble-query thinking">
          <span className="query-badge" title="Processing audio">
            <Loader2 size={11} className="spin" />
          </span>
          <span className="query-text muted-pulse">Processing audio...</span>
        </div>
      ) : null}

      {/* Clean execution output steps without raw prefixes */}
      {turn?.steps?.map((step) => {
        const cleaned = cleanStepText(step.text);
        return (
          <div key={step.id} className={`cloud-step${step.error ? " err" : " ok"}`}>
            <span className="step-icon">
              {step.error ? <AlertCircle size={13} /> : <CheckCircle2 size={13} />}
            </span>
            <span className="step-label">{cleaned}</span>
          </div>
        );
      })}

      {/* Voice missed feedback chip */}
      {didNotCatch && !mic.on && (
        <div className="bubble-fallback-msg">
          <span>Didn't catch that. Type your query or tap mic to try again.</span>
        </div>
      )}

      {/* Interactive confirmations / choices */}
      {dialog && (
        <div className="cloud-ask">
          {dialog.type === "choose_request" ? (
            <div className="file-disambiguation">
              <div className="file-disambiguation-head">
                <Search size={13} className="disambig-icon" />
                <span className="ask-q">{dialog.question || "Multiple matches found. Select one:"}</span>
              </div>
              <div className="file-choice-list" role="listbox">
                {dialog.options.map((o) => {
                  const parsed = parseFileOption(o);
                  return (
                    <button
                      key={o}
                      type="button"
                      className="file-choice-card"
                      onClick={() => answer(dialog, { choice: o })}
                      title={o}
                    >
                      <div className="file-choice-icon-wrap">
                        {getOptionIcon(parsed)}
                      </div>
                      <div className="file-choice-meta">
                        <div className="file-choice-name">{parsed.name}</div>
                        {parsed.dir && <div className="file-choice-dir">{parsed.dir}</div>}
                      </div>
                      <span className={`file-choice-badge ${parsed.isDir ? "dir" : ""}`}>
                        {parsed.ext}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="file-choice-cancel-row">
                <button
                  type="button"
                  className="file-cancel-btn"
                  onClick={() => answer(dialog, { choice: null })}
                >
                  <X size={12} />
                  <span>Cancel</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="ask-q">{dialog.title}</div>
              {dialog.type === "local_confirm" && (
                <div className="muted small">This action executes locally on your machine.</div>
              )}
              {dialog.preview && <pre className="preview">{dialog.preview}</pre>}
              <div className="ask-actions">
                <button className="opt ghost" onClick={() => answer(dialog, { approved: false })}>
                  Cancel
                </button>
                <button className="opt primary" onClick={() => answer(dialog, { approved: true })}>
                  Approve
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Compact composer input bar */}
      {showComposer && (
        <form className="composer" onSubmit={onSubmit}>
          <input
            ref={inputRef}
            value={text}
            disabled={!input.enabled}
            placeholder={mic.on ? "Listening... (or type)" : "Ask or command..."}
            onFocus={() => {
              onTyping();
              onFocusChange?.(true);
            }}
            onBlur={() => {
              onFocusChange?.(false);
            }}
            onKeyDown={(e) => {
              if (e.key !== "Escape" && e.key !== "Enter") {
                onTyping();
              }
            }}
            onChange={(e) => {
              setText(e.target.value);
              onTyping();
            }}
          />
          <button
            type="button"
            className={`ic${mic.on ? " on" : ""}`}
            disabled={!input.enabled}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onMic();
            }}
            title={mic.on ? "Stop listening" : "Speak"}
            aria-label={mic.on ? "Stop listening" : "Speak"}
          >
            {mic.on ? <Square size={13} /> : <Mic size={13} />}
          </button>
          <button
            type="submit"
            className="ic primary"
            disabled={!input.enabled || !text.trim()}
            title="Send query"
            aria-label="Send"
          >
            <Send size={13} />
          </button>
        </form>
      )}

      {showComposer && (
        <div className="bubble-shortcut-hint">
          <span>{config.hotkey ? `${config.hotkey.replace(/\+/g, " + ")} to toggle · ` : ""}Esc to close</span>
          {onLogout && (
            <button
              type="button"
              className="bubble-logout-btn"
              onClick={onLogout}
              title="Sign out of Ignite Buddy"
            >
              <LogOut size={11} aria-hidden="true" />
              <span>Sign out</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Toast notifications for asynchronous events and reminders.
 */
export function Toasts({ toasts, dismiss, onOpenBroadcast }) {
  return (
    <div className="toasts" data-hit={toasts.length ? "" : undefined}>
      {toasts.map((t) => {
        const isBroadcast = t.kind === "broadcast" || Boolean(t.message);
        return (
          <div
            key={t.id}
            className={`toast ${isBroadcast ? "toast-broadcast" : ""}`}
            onClick={() => {
              if (isBroadcast && onOpenBroadcast) {
                onOpenBroadcast(t);
              } else {
                dismiss(t.id);
              }
            }}
            title={isBroadcast ? "Click to view announcement details" : "Click to dismiss"}
            role="button"
            tabIndex={0}
          >
            <div className="toast-icon-wrap">
              {isBroadcast ? (
                <Megaphone size={14} className="toast-icon broadcast-icon" aria-hidden="true" />
              ) : t.kind === "assignment" ? (
                <ClipboardList size={14} className="toast-icon" aria-hidden="true" />
              ) : (
                <Bell size={14} className="toast-icon" aria-hidden="true" />
              )}
            </div>
            <div className="toast-content">
              {t.title ? (
                <span className="toast-title">{t.title}</span>
              ) : null}
              <span className="toast-snippet">
                {t.message ? (t.message.length > 55 ? t.message.slice(0, 55) + "..." : t.message) : t.text}
              </span>
            </div>
            {isBroadcast && (
              <span className="toast-view-pill">View</span>
            )}
            <button
              type="button"
              className="toast-close-btn"
              onClick={(e) => {
                e.stopPropagation();
                dismiss(t.id);
              }}
              title="Dismiss"
              aria-label="Dismiss notification"
            >
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
