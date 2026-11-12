import React, { useCallback, useEffect, useRef, useState } from "react";
import { LogIn, Megaphone } from "lucide-react";
import { useAgent } from "./hooks/useAgent.js";
import { useVoice } from "./hooks/useVoice.js";
import { useHitRegions } from "./lib/hit.js";
import { avatarMood, inputState, isBusy } from "./lib/state.js";
import Avatar from "./components/Avatar.jsx";
import Bubble, { Toasts } from "./components/Bubble.jsx";
import AnswerModal, { CapturePreview } from "./components/AnswerModal.jsx";
import Login from "./components/Login.jsx";
import BroadcastModal from "./components/BroadcastModal.jsx";
import RecentBroadcastsModal from "./components/RecentBroadcastsModal.jsx";

const BUBBLE_MS = 5000; // 5 seconds to clear command details and hide bubble after execution
const INACTIVITY_TIMEOUT_MS = 120000; // 2 minutes inactivity timeout

export default function App() {
  const shellHandler = useCallback((action) => {
    shellRef.current?.(action);
  }, []);
  const shellRef = useRef(null);
  const { state, dispatch, send, sendBinary, sendText, cancel, answer, login, logout } = useAgent(shellHandler);
  const voice = useVoice({ state, dispatch, send, sendBinary });
  const [text, setText] = useState("");
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [activeBroadcast, setActiveBroadcast] = useState(null);
  const [showBroadcastHistory, setShowBroadcastHistory] = useState(false);
  const [broadcastHistory, setBroadcastHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ignite_broadcast_history") || "[]");
    } catch {
      return [];
    }
  });
  const [isInteracting, setIsInteracting] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const lastToastIdRef = useRef(null);
  const input = inputState(state);
  const busy = isBusy(state);
  const mood = avatarMood(state);
  const hasAlertNotification = state.toasts.length > 0 || Boolean(activeBroadcast);
  const effectiveMood = hasAlertNotification ? "alert" : mood;
  const capture = state.dialogs.find((d) => d.type === "capture_preview");

  const inactivityTimerRef = useRef(null);

  // Trainee requires sign-in if server rejected token or explicit logout
  const isSignedIn = state.authenticated === true || (Boolean(state.user) && !state.authFailed && state.authenticated !== false);
  const needsLogin = !isSignedIn;
  // Modal opens only on trainee demand (clicking Buddy or pressing hotkey), not on system boot
  const showLogin = needsLogin && state.agent && loginModalOpen;

  // When not signed in, chat bubble and workspace are strictly hidden
  const showBubble =
    !needsLogin &&
    !showLogin &&
    (state.bubble ||
      state.composerOpen ||
      (!input.enabled && state.agent && (state.mic.on || state.turn)));

  const showAnswer = !needsLogin && state.answerOpen;

  // Track and persist campus announcements in recent history
  const lastToast = state.toasts[state.toasts.length - 1];
  const isAssignmentToast = (t) => Boolean(t) && (t.kind === "assignment" || t.category === "assignment");
  useEffect(() => {
    if (
      lastToast &&
      lastToast.id !== lastToastIdRef.current &&
      !isAssignmentToast(lastToast) &&
      (lastToast.kind === "broadcast" || lastToast.message)
    ) {
      lastToastIdRef.current = lastToast.id;
      // Persist in recent 5 broadcast history
      setBroadcastHistory((prev) => {
        const title = lastToast.title || "Announcement";
        const msg = lastToast.message || lastToast.text || "";
        const filtered = prev.filter(
          (b) => b.id !== lastToast.id && (b.title !== title || (b.message || b.text) !== msg)
        );
        const item = { ...lastToast, timestamp: Date.now() };
        const updated = [item, ...filtered].slice(0, 5);
        try {
          localStorage.setItem("ignite_broadcast_history", JSON.stringify(updated));
        } catch {}
        return updated;
      });
    }
  }, [lastToast]);

  useHitRegions(send);
  useEffect(() => {
    send({
      type: "shell_active",
      active:
        showLogin ||
        showAnswer ||
        showBubble ||
        Boolean(activeBroadcast) ||
        showBroadcastHistory,
    });
  }, [showLogin, showAnswer, showBubble, activeBroadcast, showBroadcastHistory, send]);

  useEffect(() => {
    if (location.search.includes("debug")) {
      window.__assistant = { dispatch, sendText };
    }
  });

  // Clear login spinner when auth_state arrives
  useEffect(() => {
    if (state.authenticated === true) {
      setLoginBusy(false);
      setLoginError("");
      setLoginModalOpen(false);
    }
    if (state.authenticated === false && loginBusy) {
      setLoginBusy(false);
    }
    if (state.mustChangePassword && loginBusy) {
      setLoginBusy(false);
      setLoginError("");
    }
  }, [state.authenticated, state.mustChangePassword, loginBusy]);

  // Surface agent errors during login
  useEffect(() => {
    if (!loginBusy) return;
    const lastErr = state.turn?.steps?.filter((s) => s.error).at(-1);
    if (lastErr) {
      setLoginError(lastErr.text);
      setLoginBusy(false);
    }
  }, [state.turn, loginBusy]);

  const summon = useCallback(() => {
    if (needsLogin) {
      setLoginModalOpen(true);
      return;
    }
    dispatch({ type: "activate" });
    if (input.enabled && !busy && !voice.active()) {
      voice.start();
    }
  }, [dispatch, input.enabled, busy, voice, needsLogin]);

  const dismiss = useCallback(() => {
    voice.cancel();
    setText("");
    if (busy) cancel();
    dispatch({ type: "deactivate" });
    window.speechSynthesis?.cancel();
  }, [voice, busy, cancel, dispatch]);

  const handleLogout = useCallback(() => {
    if (window.confirm("Are you sure you want to sign out of Ignite Buddy?")) {
      logout();
      dispatch({ type: "conversation_reset" });
      dismiss();
    }
  }, [logout, dispatch, dismiss]);

  // ---- Assignments (published by the admin/faculty panel) ----
  const fetchAssignments = useCallback(() => {
    dispatch({ type: "assignments_loading", loading: true });
    send({ type: "assignments_get" });
  }, [dispatch, send]);

  const submitAssignment = useCallback(
    ({ assignment_id, submission_text = "", submission_link = "" }) => {
      dispatch({ type: "assignment_submitting", id: assignment_id ?? null });
      send({ type: "assignment_submit", assignment_id, submission_text, submission_link });
    },
    [dispatch, send]
  );

  const openAssignment = useCallback(
    (id = null) => {
      dispatch({ type: "assignment_focus", id });
      fetchAssignments();
    },
    [dispatch, fetchAssignments]
  );

  // A notification carries action_url ("/assignments/12") — open that assignment.
  const openAssignmentFromToast = useCallback(
    (t) => {
      const match = /\/(\d+)\s*$/.exec(t?.action_url || "");
      openAssignment(match ? Number(match[1]) : null);
    },
    [openAssignment]
  );

  // Load the trainee's assignments as soon as they sign in.
  useEffect(() => {
    if (state.authenticated === true && state.link) fetchAssignments();
  }, [state.authenticated, state.link, fetchAssignments]);

  // A new-assignment / reminder / evaluation notification refreshes the list.
  useEffect(() => {
    if (isAssignmentToast(lastToast)) {
      fetchAssignments();
    }
  }, [lastToast, fetchAssignments]);

  // Stop listening as soon as user starts writing or focuses input
  const handleTyping = useCallback(() => {
    setIsInteracting(true);
    if (voice.active()) {
      voice.cancel();
      dispatch({ type: "mic", on: false });
    }
  }, [voice, dispatch]);

  // Shell actions triggered from desktop wrappers (Qt / Electron / Tray / Hotkey)
  shellRef.current = (action) => {
    if (action === "activate") {
      summon();
    } else if (action === "deactivate") {
      dismiss();
    }
  };

  // Keyboard shortcut listener within the window
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        if (state.answerOpen) {
          dispatch({ type: "conversation_reset" });
        } else {
          dismiss();
          send({ type: "shell_hide" });
          window.electronShell?.hide?.();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state.answerOpen, dismiss, dispatch, send]);

  // Auto-hide bubble only when trainee is NOT interacting with it
  // (Prevents hiding if trainee is typing, input is focused, cursor is hovering, listening, or has pending text)
  useEffect(() => {
    if (
      !state.bubble ||
      state.mic.on ||
      state.dialogs.length ||
      state.composerOpen ||
      busy ||
      Boolean(state.heard) ||
      text.trim().length > 0 ||
      isInteracting ||
      isInputFocused
    ) {
      return undefined;
    }
    const t = setTimeout(() => {
      if (text.trim().length === 0 && !isInteracting && !isInputFocused) {
        dispatch({ type: "turn_clear" });
        dispatch({ type: "bubble_hide" });
      }
    }, BUBBLE_MS);
    return () => clearTimeout(t);
  }, [
    state.bubble,
    state.composerOpen,
    state.mic.on,
    state.dialogs.length,
    busy,
    state.turn,
    state.heard,
    text,
    isInteracting,
    isInputFocused,
    dispatch,
  ]);

  // Spoken feedback
  useEffect(() => {
    if (state.speak && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(state.speak));
    }
    if (state.speak) dispatch({ type: "speak_done" });
  }, [state.speak, dispatch]);

  // 2-minute inactivity auto-hide
  const resetInactivity = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    // Never hide while speaking, listening, generating, or when dialog prompts exist
    if (state.mic.on || busy || state.turn?.streaming || state.dialogs.length > 0) {
      return;
    }
    inactivityTimerRef.current = setTimeout(() => {
      dismiss();
      send({ type: "shell_hide" });
      window.electronShell?.hide?.();
    }, INACTIVITY_TIMEOUT_MS);
  }, [state.mic.on, busy, state.turn?.streaming, state.dialogs.length, dismiss, send]);

  useEffect(() => {
    resetInactivity();
    const onUserActivity = () => resetInactivity();
    window.addEventListener("mousemove", onUserActivity, { passive: true });
    window.addEventListener("mousedown", onUserActivity, { passive: true });
    window.addEventListener("keydown", onUserActivity, { passive: true });
    window.addEventListener("touchstart", onUserActivity, { passive: true });
    return () => {
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
      window.removeEventListener("mousemove", onUserActivity);
      window.removeEventListener("mousedown", onUserActivity);
      window.removeEventListener("keydown", onUserActivity);
      window.removeEventListener("touchstart", onUserActivity);
    };
  }, [resetInactivity]);

  const submit = (e) => {
    e.preventDefault();
    if (input.enabled && text.trim()) {
      voice.cancel();
      dispatch({ type: "mic", on: false });
      sendText(text);
      setText("");
      dispatch({ type: "composer_close" });
    }
  };

  const toggleMic = useCallback(() => {
    if (state.mic.on || voice.active()) {
      voice.stop();
    } else {
      voice.start();
    }
  }, [state.mic.on, voice]);

  const onLogin = (userId, password, newPassword = "") => {
    setLoginBusy(true);
    setLoginError("");
    login(userId, password, newPassword);
  };

  const onFollowUp = (q) => {
    if (!input.enabled) return;
    sendText(q);
  };

  return (
    <div className="stage">
      {showLogin && (
        <Login
          onSubmit={onLogin}
          onClose={() => setLoginModalOpen(false)}
          busy={loginBusy}
          error={loginError}
          mustChangePassword={state.mustChangePassword}
          onClearMustChangePassword={() => dispatch({ type: "clear_must_change_password" })}
        />
      )}

      {showAnswer && (
        <AnswerModal
          conversation={state.conversation}
          turn={state.turn}
          activeTab={state.activeTab || "answer"}
          onTabChange={(tab) => dispatch({ type: "set_tab", tab })}
          vault={state.vault}
          filesView={state.filesView}
          scheduleView={state.scheduleView}
          assignments={state.assignments}
          assignmentsLoaded={state.assignmentsLoaded}
          assignmentsLoading={state.assignmentsLoading}
          assignmentSubmittingId={state.assignmentSubmittingId}
          assignmentFocusId={state.assignmentFocusId}
          onFetchAssignments={fetchAssignments}
          onSubmitAssignment={submitAssignment}
          onFetchSchedule={() => send({ type: "schedule_get" })}
          onOpenPath={(path) => send({ type: "open_path", path })}
          onListFolder={(path) => send({ type: "list_folder", path })}
          onMutateTask={(payload) => send({ type: "task_mutate", ...payload })}
          onMutateNote={(payload) => send({ type: "note_mutate", ...payload })}
          onRunCommand={(cmd) => sendText(cmd)}
          busy={busy}
          onClose={() => dispatch({ type: "conversation_reset" })}
          onLogout={handleLogout}
        />
      )}

      {capture && <CapturePreview dialog={capture} answer={answer} />}

      <div className="dock">
        {showBroadcastHistory && (
          <RecentBroadcastsModal
            history={broadcastHistory}
            onSelect={(item) => {
              setActiveBroadcast({ ...item, initialExpanded: true });
              setShowBroadcastHistory(false);
            }}
            onClose={() => setShowBroadcastHistory(false)}
          />
        )}

        {activeBroadcast && (
          <BroadcastModal
            broadcast={activeBroadcast}
            onClose={() => setActiveBroadcast(null)}
            onOpenHistory={() => {
              setActiveBroadcast(null);
              setShowBroadcastHistory(true);
            }}
            onDismiss={(id) => {
              if (id) dispatch({ type: "dismiss_toast", id });
              setActiveBroadcast(null);
            }}
          />
        )}

        {!needsLogin && (
          <Toasts
            toasts={state.toasts}
            dismiss={(id) => {
              if (activeBroadcast?.id === id) setActiveBroadcast(null);
              dispatch({ type: "dismiss_toast", id });
            }}
            onOpenBroadcast={(b) => setActiveBroadcast({ ...b, initialExpanded: true })}
            onOpenAssignment={openAssignmentFromToast}
          />
        )}

        {needsLogin && !loginModalOpen && (
          <button
            type="button"
            className="buddy-login-prompt"
            onClick={() => setLoginModalOpen(true)}
            data-hit
            title="Click to sign in to Ignite Buddy"
            aria-label="Click to sign in to Ignite Buddy"
          >
            <LogIn size={13} className="buddy-login-icon" aria-hidden="true" />
            <span>Click to sign in</span>
          </button>
        )}

        {showBubble && (
          <Bubble
            state={state}
            input={input}
            busy={busy}
            text={text}
            setText={setText}
            onSubmit={submit}
            onMic={toggleMic}
            onTyping={handleTyping}
            onInteractChange={setIsInteracting}
            onFocusChange={setIsInputFocused}
            onClose={() => {
              dismiss();
              send({ type: "shell_hide" });
              window.electronShell?.hide?.();
            }}
            onCancel={cancel}
            answer={answer}
            onLogout={!needsLogin ? handleLogout : undefined}
            onOpenBroadcasts={() => setShowBroadcastHistory((prev) => !prev)}
          />
        )}

        <Avatar
          mood={needsLogin ? "idle" : effectiveMood}
          glb={state.config.avatar ? "/avatar.glb" : null}
          animationMap={state.config?.animations || window.__ASSISTANT_ANIMATIONS__}
          onClick={() => {
            if (needsLogin) {
              setLoginModalOpen(true);
              return;
            }
            state.composerOpen || state.bubble || state.mic.on ? dismiss() : summon();
          }}
        />
      </div>
    </div>
  );
}
