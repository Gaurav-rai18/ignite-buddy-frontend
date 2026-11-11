import { useCallback, useEffect, useReducer, useRef } from "react";
import { initialState, reducer } from "../lib/state.js";

const token = () => document.querySelector('meta[name="agent-token"]')?.content || "";

// Connection to the LOCAL Python agent (same origin). The agent relays to the central server and runs commands on this PC.
export function useAgent(onShell) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const ws = useRef(null);
  const shellRef = useRef(onShell);
  shellRef.current = onShell;
  // Keep a ref to answerOpen so sendText can choose conversation_user without stale closures.
  const answerOpenRef = useRef(false);
  answerOpenRef.current = state.answerOpen;

  useEffect(() => {
    let closed = false, delay = 500, timer;
    const open = () => {
      const sock = new WebSocket(`ws://${location.host}/ws`);
      ws.current = sock;
      sock.onopen = () => { delay = 500; sock.send(JSON.stringify({ type: "auth", token: token() })); dispatch({ type: "agent_open" }); };
      sock.onmessage = (e) => {
        let m; try { m = JSON.parse(e.data); } catch { return; }
        if (m.type === "shell") shellRef.current?.(m.action); else dispatch(m);
      };
      sock.onclose = () => { dispatch({ type: "agent_closed" }); if (!closed) { timer = setTimeout(open, delay); delay = Math.min(delay * 2, 8000); } };
    };
    open();
    return () => { closed = true; clearTimeout(timer); ws.current?.close(); };
  }, []);

  const send = useCallback((msg) => { if (ws.current?.readyState === 1) ws.current.send(JSON.stringify(msg)); }, []);
  const sendBinary = useCallback((buf) => { if (ws.current?.readyState === 1) ws.current.send(buf); }, []);

  const sendText = useCallback((text, voice = false) => {
    const t = text.trim();
    if (!t) return;
    // When the conversation panel is open, treat this as a multi-turn follow-up
    // so the top-middle panel accumulates Q&A instead of replacing it.
    if (answerOpenRef.current) {
      dispatch({ type: "conversation_user", text: t, voice });
    } else {
      dispatch({ type: "user_text", text: t, voice });
    }
    send({ type: "text", text: t });
  }, [send]);

  const cancel = useCallback(() => { send({ type: "cancel" }); dispatch({ type: "cancelled" }); window.speechSynthesis?.cancel(); }, [send]);

  const answer = useCallback((dialog, payload) => {
    const kinds = { confirm_request: "confirm_response", choose_request: "choose_response",
                    local_confirm: "local_confirm_response", capture_preview: "capture_decision" };
    send({ type: kinds[dialog.type], id: dialog.id, ...payload });
    dispatch({ type: "dialog_done", id: dialog.id });
  }, [send]);

  const login = useCallback((userId, password, newPassword = "") => {
    send({ type: "login", user_id: userId, password, new_password: newPassword });
  }, [send]);

  const logout = useCallback(() => {
    send({ type: "logout" });
    dispatch({ type: "auth_state", authenticated: false });
  }, [send]);

  return { state, dispatch, send, sendBinary, sendText, cancel, answer, login, logout };
}
