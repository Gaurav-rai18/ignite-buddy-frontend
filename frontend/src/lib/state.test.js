import test from "node:test";
import assert from "node:assert/strict";
import { initialState, reducer, inputState, isBusy, avatarMood, toPcm16 } from "./state.js";

const run = (...actions) => actions.reduce(reducer, initialState);
const ready = { type: "agent_ready", status: "ready", connected: true, config: { stt: "google", hotkey: "ctrl+alt+space" } };

test("commands go to the bubble (steps), answers go to the markdown window", () => {
  let s = run(ready, { type: "user_text", text: "open project in vscode and explain streams" },
              { type: "say", text: "[1] Found folder x" }, { type: "say", text: "[2] Opened x in vs code" });
  assert.deepEqual(s.turn.steps.map((x) => x.text), ["[1] Found folder x", "[2] Opened x in vs code"]);
  assert.equal(s.answerOpen, false);
  s = reducer(s, { type: "token", text: "## Streams\n" });
  s = reducer(s, { type: "token", text: "A **stream** is..." });
  assert.equal(s.answerOpen, true);
  assert.equal(s.turn.answer, "## Streams\nA **stream** is...");
  assert.equal(s.turn.streaming, true);
  s = reducer(s, { type: "message_end" });
  assert.equal(s.turn.streaming, false);
  assert.equal(s.turn.steps.length, 2);                       // the command progress is still there
});

test("a new query replaces the previous turn and closes the old answer", () => {
  let s = run(ready, { type: "user_text", text: "q1" }, { type: "token", text: "a1" });
  s = reducer(s, { type: "user_text", text: "q2", voice: true });
  assert.deepEqual([s.turn.query, s.turn.voice, s.turn.answer, s.answerOpen], ["q2", true, "", false]);
});

test("live (interim) speech shows in the bubble, then the final text becomes the query", () => {
  let s = run(ready, { type: "activate" }, { type: "heard", text: "open task" });
  assert.deepEqual([s.heard, s.bubble, s.composerOpen], ["open task", true, true]);
  s = reducer(s, { type: "heard", text: "open task manager" });
  s = reducer(s, { type: "user_text", text: "open task manager", voice: true });
  assert.equal(s.heard, "");
  assert.equal(s.turn.voice, true);
});

test("hotkey summons, escape/deactivate dismisses everything", () => {
  let s = run(ready, { type: "activate" }, { type: "user_text", text: "x" }, { type: "token", text: "y" });
  s = reducer(s, { type: "deactivate" });
  assert.deepEqual([s.composerOpen, s.answerOpen, s.bubble, s.mic.on], [false, false, false, false]);
});

test("the bubble auto-hides, but not while the trainee is being asked something or is typing/speaking", () => {
  let s = run(ready, { type: "user_text", text: "x" }, { type: "say", text: "Done" });
  assert.equal(reducer(s, { type: "bubble_hide" }).bubble, false);
  s = reducer(s, { type: "confirm_request", id: "r1", title: "Run install.bat" });
  assert.equal(reducer(s, { type: "bubble_hide" }).bubble, true);
  s = reducer(s, { type: "dialog_done", id: "r1" });
  s = reducer(s, { type: "mic", on: true });
  assert.equal(reducer(s, { type: "bubble_hide" }).bubble, true);
  assert.equal(reducer(run(ready, { type: "activate" }), { type: "bubble_hide" }).bubble, true);
});

test("input fails closed until agent, server link and policy are all healthy", () => {
  assert.equal(inputState(initialState).enabled, false);
  assert.equal(inputState(run(ready)).enabled, true);
  assert.equal(inputState(reducer(run(ready), { type: "policy", blocked: true, reason: "Assessment" })).reason, "Assessment");
  assert.equal(inputState(reducer(run(ready), { type: "link", status: "auth_failed", connected: false, auth_failed: true })).enabled, false);
  assert.match(inputState(run({ type: "agent_ready", status: "unreachable", connected: false, server: "wss://srv", detail: "ConnectionRefusedError" })).reason,
               /Cannot reach .*wss:\/\/srv.*ConnectionRefusedError/);
});

test("a block clears dialogs and the open answer", () => {
  let s = run(ready, { type: "local_confirm", id: "a1", title: "Run x.bat" }, { type: "token", text: "secret answer" });
  s = reducer(s, { type: "policy", blocked: true, reason: "x" });
  assert.deepEqual([s.dialogs.length, s.answerOpen], [0, false]);
});

test("late page gets hello and is ready; user hidden while the link is down", () => {
  let s = run(ready, { type: "hello_ok", user: { name: "alice" }, capabilities: { "files.delete": false } });
  assert.equal(s.user.name, "alice");
  s = reducer(s, { type: "link", status: "authenticating", connected: false });
  assert.equal(s.user, null);
});

test("avatar mood follows what is happening", () => {
  const base = run(ready);
  assert.equal(avatarMood(initialState), "offline");
  assert.equal(avatarMood(base), "idle");
  assert.equal(avatarMood(reducer(base, { type: "mic", on: true })), "listening");
  assert.equal(avatarMood(reducer(base, { type: "mic", on: true, speaking: true })), "hearing");
  assert.equal(avatarMood(reducer(base, { type: "state", state: "thinking" })), "thinking");
  assert.equal(avatarMood(reducer(base, { type: "token", text: "x" })), "speaking");
  assert.equal(avatarMood(reducer(base, { type: "notification", kind: "timer", text: "t" })), "alert");
});

test("notifications are toasts and spoken; busy states and cancel", () => {
  let s = run(ready, { type: "notification", kind: "timer", text: "Timer finished: pasta" });
  assert.deepEqual([s.toasts.length, s.speak], [1, "Timer finished: pasta"]);
  s = run(ready, { type: "state", state: "generating" }, { type: "token", text: "x" });
  assert.equal(isBusy(s), true);
  s = reducer(s, { type: "cancelled" });
  assert.deepEqual([isBusy(s), s.turn.streaming], [false, false]);
});

test("server-side transcripts start a voice turn; empty ones are ignored", () => {
  assert.equal(run(ready, { type: "transcript", text: "" }).turn, null);
  assert.equal(run(ready, { type: "transcript", text: "set a timer" }).turn.voice, true);
});

test("PCM16 conversion downsamples to 16 kHz and clips", () => {
  const out = toPcm16(Float32Array.from({ length: 480 }, (_, i) => (i % 2 ? 2 : -2)), 48000);
  assert.deepEqual([out.length, out[0], out[1]], [160, -32768, 32767]);
});

test("assignment notifications open the workspace and keep their action target", () => {
  let s = run(ready, {
    type: "notification",
    kind: "assignment",
    title: "New Assignment Posted",
    message: "Hi Trainee! A new assignment, React Lab, has been posted by Ravi.",
    priority: "high",
    category: "assignment",
    action_url: "/assignments/12",
    action_label: "View Assignment",
  });
  assert.equal(s.toasts.length, 1);
  assert.equal(s.toasts[0].category, "assignment");
  assert.equal(s.toasts[0].action_url, "/assignments/12");
  assert.equal(s.toasts[0].priority, "high");

  s = reducer(s, { type: "assignment_focus", id: 12 });
  assert.deepEqual([s.activeTab, s.answerOpen, s.assignmentFocusId], ["assignments", true, 12]);
});

test("assignments load into state; a failed submission raises a toast", () => {
  let s = run(ready,
    { type: "assignments_loading", loading: true },
    { type: "assignments_data", assignments: [{ id: 1, title: "Lab 1", status: "PENDING" }] });
  assert.deepEqual([s.assignmentsLoaded, s.assignmentsLoading, s.assignments.length], [true, false, 1]);

  s = reducer(s, { type: "assignment_submitting", id: 1 });
  assert.equal(s.assignmentSubmittingId, 1);

  s = reducer(s, { type: "assignment_submitted", ok: false, error: "Provide a submission link." });
  const toast = s.toasts[s.toasts.length - 1];
  assert.deepEqual(
    [s.assignmentSubmittingId, toast.kind, toast.title, toast.message],
    [null, "assignment", "Submission Failed", "Provide a submission link."]
  );

  // A successful submission clears the spinner and does not add a toast.
  const count = s.toasts.length;
  s = reducer(s, { type: "assignment_submitted", ok: true, assignment_id: 1, status: "SUBMITTED" });
  assert.deepEqual([s.assignmentSubmittingId, s.toasts.length], [null, count]);
});

test("local assignment output opens the assignments tab", () => {
  const s = run(ready, { type: "say", text: "[ ] React Lab: due Mon 10:00\n[DONE] SQL Drill: due Fri 09:00" });
  assert.equal(s.activeTab, "assignments");
  assert.equal(s.answerOpen, true);
});

test("streaming tokens keep a single user/assistant pair in conversation", () => {
  let s = run(ready, { type: "user_text", text: "what is a stream" },
              { type: "token", text: "A " },
              { type: "token", text: "stream " },
              { type: "token", text: "is lazy." });
  assert.equal(s.conversation.length, 2);
  assert.equal(s.conversation[0].role, "user");
  assert.equal(s.conversation[0].text, "what is a stream");
  assert.equal(s.conversation[1].role, "assistant");
  assert.equal(s.conversation[1].text, "A stream is lazy.");
  assert.equal(s.turn.answer, "A stream is lazy.");
});
