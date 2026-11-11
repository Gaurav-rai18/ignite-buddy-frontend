// Pure state logic for the desktop overlay (no React, no DOM) so it can be unit-tested with `node --test`.
export const initialState = {
  link: false, agent: false, authFailed: false, linkStatus: "connecting", linkDetail: "", server: "",
  config: { stt: "google", lang: "en-US", hotkey: "", avatar: false, shell: false },
  user: null, blocked: false, blockReason: "",
  status: "idle",                       // idle | listening | thinking | generating | speaking  (server side)
  tracking: { paused: false }, capabilities: {},
  mic: { on: false, level: 0, speaking: false, engine: null },   // engine: "agent" (audio goes to the local agent)
  heard: "",                            // live (interim) transcript while the trainee is speaking
  turn: null,                           // { id, query, voice, steps: [{id,text,error}], answer, streaming }
  bubble: false,                        // the small chat bubble (queries, command progress, questions to the trainee)
  answerOpen: false,                    // the markdown answer window
  composerOpen: false,                  // the text box is showing (hotkey / avatar click)
  dialogs: [],                          // confirm | choose | local_confirm | capture_preview
  toasts: [], speak: null,
  // Desktop JWT login (null = not required yet / unknown; false = need login; true = logged in)
  authenticated: null,
  authUser: null,                       // { user_id, name, batch }
  mustChangePassword: null,             // { userId, name, message } if first-time / reset password change required
  // Multi-turn RAG conversation shown in the top-middle panel
  conversation: [],                     // [{role:'user'|'assistant', text, streaming?}]
  vault: { tasks: [], notes: [] },
  filesView: null,                      // { folder, path, items: [{name, is_dir, path, ext, size}] }
  scheduleView: { slots: [], today_weekday: 0, time_now: "" },
  activeTab: "answer",
};


let seq = 0;
const nid = () => ++seq;
const newTurn = (query, voice = false) => ({ id: nid(), query, voice, steps: [], answer: "", streaming: false });
const appendConversation = (conv, role, text, streaming = false) => [...conv, { id: nid(), role, text, streaming }];
const withTurn = (s) => s.turn || newTurn("");

export function reducer(state, action) {
  switch (action.type) {
    // ---------- connection ----------
    case "agent_open": return { ...state, agent: true };
    case "agent_closed": return { ...state, agent: false, link: false };
    case "agent_ready": case "link":
      return { ...state, agent: true, link: !!action.connected, authFailed: !!action.auth_failed,
               linkStatus: action.status || (action.connected ? "ready" : "connecting"), linkDetail: action.detail || "",
               server: action.server || state.server, config: action.config ? { ...state.config, ...action.config } : state.config,
               status: action.connected ? state.status : "idle", user: action.connected ? state.user : null };
    case "hello_ok": return { ...state, user: action.user, link: true, authFailed: false,
                               capabilities: action.capabilities || {}, tracking: action.tracking || state.tracking };
    case "policy": return { ...state, blocked: !!action.blocked, blockReason: action.reason || "",
                             dialogs: action.blocked ? [] : state.dialogs, answerOpen: action.blocked ? false : state.answerOpen };
    case "blocked": return { ...state, blocked: true, blockReason: action.reason || state.blockReason };
    case "state": return { ...state, status: action.state };
    case "tracking": return { ...state, tracking: { paused: !!action.paused, seconds: action.seconds } };

    // ---------- summoning the assistant ----------
    case "activate": return { ...state, composerOpen: true, bubble: true };
    case "deactivate": return { ...state, composerOpen: false, answerOpen: false, heard: "", bubble: false,
                                 mic: { ...state.mic, on: false, level: 0, speaking: false } };
    case "bubble_hide": return state.composerOpen || state.mic.on || state.dialogs.length ? state : { ...state, bubble: false };
    case "turn_clear": return { ...state, turn: null, heard: "", bubble: false };
    case "composer_close": return { ...state, composerOpen: false };
    case "dismiss_answer": return { ...state, answerOpen: false };

    // ---------- a query / command ----------
    case "user_text": return { ...state, turn: newTurn(action.text, !!action.voice), heard: "", bubble: true, answerOpen: false };
    case "transcript":                                  // text recognised by the LOCAL agent STT
      return action.text ? { ...state, turn: newTurn(action.text, true), heard: "", bubble: true, answerOpen: false } : state;
    case "heard": return { ...state, heard: action.text || "", bubble: true };
    case "say": { const t = withTurn(state);
      const isHelp = action.text && (action.text.includes("Capabilities & Query Guide") || action.text.includes("Help & Commands"));
      const isTasks = action.text && (action.text.includes("task list") || action.text.includes("Your task list is empty"));
      const isNotes = action.text && (action.text.includes("Recent notes:") || action.text.includes("No notes yet") || action.text.includes("Note saved"));
      const isFiles = action.text && ((action.text.includes("items in") || action.text.includes("items):")) && (action.text.includes("[DIR]") || action.text.includes("Found ")));
      const isTimers = action.text && (action.text.includes("active timers") || action.text.includes("pending reminders") || action.text.includes("Timer set for") || action.text.includes("Reminder set for"));
      const tab = isHelp ? "help" : isTasks ? "tasks" : isNotes ? "notes" : isFiles ? "files" : isTimers ? "timers" : state.activeTab;
      const shouldOpenModal = isHelp || isTasks || isNotes || isFiles;
      return {
        ...state,
        turn: { ...t, steps: [...t.steps, { id: nid(), text: action.text }], answer: isHelp ? action.text : t.answer },
        bubble: true,
        answerOpen: shouldOpenModal ? true : state.answerOpen,
        activeTab: tab,
      }; }
    case "error": { const t = withTurn(state);
      return { ...state, heard: "", turn: { ...t, steps: [...t.steps, { id: nid(), text: action.message, error: true }] }, bubble: true }; }
    case "token": { const t = withTurn(state);                          // streamed RAG/chat answer → top panel
      const answer = t.answer + action.text;
      let conv = state.conversation;
      // Ensure exactly one user turn for this query (do not re-append on every token)
      if (t.query) {
        const last = conv[conv.length - 1];
        const prev = conv.length >= 2 ? conv[conv.length - 2] : null;
        const hasUser =
          (last && last.role === "user" && last.text === t.query) ||
          (last && last.role === "assistant" && prev && prev.role === "user" && prev.text === t.query);
        if (!hasUser) {
          conv = [...conv, { id: nid(), role: "user", text: t.query, streaming: false }];
        }
      }
      // Update the current assistant bubble, or open a new one once
      if (conv.length && conv[conv.length - 1].role === "assistant") {
        conv = [...conv.slice(0, -1), { ...conv[conv.length - 1], text: answer, streaming: true }];
      } else {
        conv = [...conv, { id: nid(), role: "assistant", text: answer, streaming: true }];
      }
      return { ...state, turn: { ...t, answer, streaming: true }, answerOpen: true, activeTab: "answer", conversation: conv }; }
    case "message_end": {
      let conv = state.conversation;
      if (conv.length && conv[conv.length - 1].role === "assistant") {
        conv = [...conv.slice(0, -1), { ...conv[conv.length - 1], streaming: false }];
      }
      return state.turn
        ? { ...state, turn: { ...state.turn, streaming: false }, conversation: conv }
        : { ...state, conversation: conv };
    }
    case "cancelled":
      return { ...state, dialogs: [], status: "idle", heard: "", turn: state.turn ? { ...state.turn, streaming: false } : null };

    // ---------- mic ----------
    case "mic": return { ...state, mic: { on: !!action.on, level: action.level ?? 0, speaking: !!action.speaking,
                                          engine: action.engine ?? state.mic.engine } };

    // ---------- notifications and questions to the trainee ----------
    case "speak": return { ...state, speak: action.text };
    case "speak_done": return { ...state, speak: null };
    case "notification": {
      const nid_val = action.notification_id || action.id;
      const isDuplicate = state.toasts.some(
        (t) =>
          (nid_val && t.notification_id === nid_val) ||
          (action.title && action.message && t.title === action.title && t.message === action.message) ||
          (action.text && t.text === action.text)
      );
      if (isDuplicate) return state;

      const newToast = {
        id: nid(),
        notification_id: nid_val,
        kind: action.kind || "broadcast",
        title: action.title || "",
        message: action.message || "",
        text: action.text || (action.title ? `${action.title}: ${action.message}` : ""),
        created_at: action.created_at || new Date().toISOString(),
      };
      return {
        ...state,
        toasts: [...state.toasts, newToast],
        speak: action.text || action.title || null,
      };
    }
    case "dismiss_toast": return { ...state, toasts: state.toasts.filter((t) => t.id !== action.id) };
    case "confirm_request": case "choose_request": case "local_confirm": case "capture_preview":
      return { ...state, dialogs: [...state.dialogs, { ...action }], bubble: true };
    case "dialog_done": return { ...state, dialogs: state.dialogs.filter((d) => d.id !== action.id) };
    case "must_change_password":
      return {
        ...state,
        mustChangePassword: {
          userId: action.user_id,
          name: action.name,
          message: action.message || "Password change required.",
        },
      };
    case "clear_must_change_password":
      return { ...state, mustChangePassword: null };
    case "auth_state":
      return {
        ...state,
        authenticated: !!action.authenticated,
        authUser: action.authenticated
          ? { user_id: action.user_id, name: action.name, batch: action.batch }
          : null,
        mustChangePassword: action.authenticated ? null : state.mustChangePassword,
        authFailed: !action.authenticated && state.authFailed,
      };
    case "conversation_user": {
      // Follow-up from the answer panel or bubble while a conversation is open
      const conv = appendConversation(state.conversation, "user", action.text);
      return {
        ...state,
        conversation: conv,
        turn: newTurn(action.text, !!action.voice),
        heard: "",
        bubble: true,
        answerOpen: true,
      };
    }
    case "conversation_reset":
      return { ...state, conversation: [], answerOpen: false, turn: null };
    case "vault_data":
      return { ...state, vault: { tasks: action.tasks || [], notes: action.notes || [] } };
    case "folder_listing":
      return {
        ...state,
        filesView: {
          folder: action.folder || "Folder",
          path: action.path || "",
          parent_path: action.parent_path || null,
          items: action.items || [],
          recursive_items: action.recursive_items || [],
        },
        activeTab: "files",
        answerOpen: true,
      };
    case "schedule_data":
    case "timetable_data":
      return {
        ...state,
        scheduleView: {
          slots: action.slots || [],
          today_weekday: typeof action.today_weekday === "number" ? action.today_weekday : (new Date().getDay() + 6) % 7,
          time_now: action.time_now || "",
        },
        activeTab: action.openTab ? "schedule" : (state.activeTab || "schedule"),
        answerOpen: action.openTab ? true : state.answerOpen,
      };
    case "set_tab":
      return { ...state, activeTab: action.tab, answerOpen: true };
    default: return state;
  }
}

// The UI is usable only when everything on the path is healthy (fails closed, like the server's assessment block).
export function inputState(s) {
  if (!s.agent) return { enabled: false, reason: "Local agent not running. Start it with: trainee-desktop" };
  if (s.authFailed || s.authenticated === false) return { enabled: false, reason: "Sign in with the account your admin created." };
  if (s.linkStatus === "unreachable") {
    return { enabled: false, reason: `Cannot reach the assistant server${s.server ? ` at ${s.server}` : ""}${s.linkDetail ? `: ${s.linkDetail}` : ""}. Retrying...` };
  }
  if (!s.link) return { enabled: false, reason: `Connecting to the assistant server${s.server ? ` (${s.server})` : ""}...` };
  if (s.blocked) return { enabled: false, reason: s.blockReason || "The assistant is disabled right now." };
  return { enabled: true, reason: "" };
}

export const isBusy = (s) => ["thinking", "generating", "speaking"].includes(s.status);

// What the avatar should be doing.
export function avatarMood(s) {
  if (!inputState(s).enabled) return "offline";
  if (s.mic.on) return s.mic.speaking ? "hearing" : "listening";
  if (s.status === "thinking") return "thinking";
  if (s.status === "generating" || s.status === "speaking" || (s.turn && s.turn.streaming)) return "speaking";
  if (s.toasts.length) return "alert";
  return "idle";
}

// Float32 mic samples at `rate` Hz -> little-endian PCM16 at 16 kHz (the server's speech-to-text contract).
export function toPcm16(float32, rate) {
  const ratio = rate / 16000;
  const n = Math.floor(float32.length / ratio);
  const out = new Int16Array(n);
  for (let i = 0; i < n; i++) {
    const s = Math.max(-1, Math.min(1, float32[Math.floor(i * ratio)]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}
