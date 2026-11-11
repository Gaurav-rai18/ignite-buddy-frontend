import { useCallback, useEffect, useRef } from "react";
import { toPcm16 } from "../lib/state.js";
import { Vad, rms } from "../lib/vad.js";

/**
 * Fallback script processor for browsers that do not support AudioWorkletNode.
 */
function fallbackScriptProcessor(ctx, src, s, onSamples) {
  const proc = ctx.createScriptProcessor(4096, 1, 1);
  proc.onaudioprocess = (e) => {
    onSamples(e.inputBuffer.getChannelData(0));
  };
  src.connect(proc);
  proc.connect(ctx.destination);
  s.node = proc;
}

/**
 * Speech input hook.
 * Supports:
 *   1. "server": Browser microphone via Web Audio (AudioWorklet/ScriptProcessor), buffered locally and sent in one shot.
 *   2. "local": Direct Windows OS microphone capture via Python SpeechListener (for Accops VDI / desktop shells).
 * Automatically falls back to "local" Python capture when browser microphone permissions are restricted.
 */
export function useVoice({ state, dispatch, send, sendBinary }) {
  const live = useRef(null);
  const transcribeTimerRef = useRef(null);
  const stateRef = useRef(state);
  stateRef.current = state;

  const clearTranscribeTimer = useCallback(() => {
    if (transcribeTimerRef.current) {
      clearTimeout(transcribeTimerRef.current);
      transcribeTimerRef.current = null;
    }
  }, []);

  // Clear transcribe timeout whenever a transcript, answer, or turn arrives
  useEffect(() => {
    if (state?.heard) {
      clearTranscribeTimer();
    }
    if (state?.turn?.query || state?.turn?.answer) {
      clearTranscribeTimer();
    }
    if (!state?.mic?.on && live.current?.kind === "local") {
      live.current = null;
      clearTranscribeTimer();
    }
  }, [state?.heard, state?.turn, state?.mic?.on, clearTranscribeTimer]);

  const teardown = useCallback((s) => {
    clearTranscribeTimer();
    s.stream?.getTracks().forEach((t) => t.stop());
    s.node?.disconnect?.();
    s.src?.disconnect?.();
    s.ctx?.close().catch(() => {});
  }, [clearTranscribeTimer]);

  // ------------------------------------------------ Python Direct OS Mic (Accops / Desktop)
  const startLocal = useCallback(() => {
    const s = { kind: "local", done: false };
    const finish = (reason) => {
      if (s.done) return;
      s.done = true;
      live.current = null;
      clearTranscribeTimer();
      dispatch({ type: "mic", on: false, speaking: false });

      if (reason === "cancel") {
        send({ type: "mic_cancel" });
        dispatch({ type: "heard", text: "" });
      } else {
        send({ type: "mic_stop" });
        // Set a safety timeout for backend server transcription
        transcribeTimerRef.current = setTimeout(() => {
          if (!stateRef.current?.turn?.query) {
            dispatch({ type: "heard", text: "" });
            dispatch({ type: "say", text: "I didn't catch that. Please try speaking again or typing your query." });
            dispatch({ type: "activate" });
          }
        }, 25000);
      }
    };
    s.request = finish;
    live.current = s;
    send({ type: "mic_start" });
    dispatch({ type: "mic", on: true, level: 0, speaking: false, engine: "local" });
  }, [dispatch, send, clearTranscribeTimer]);

  // ------------------------------------------------ Browser Web Audio Capture (Web / Pure Browser)
  const startWebAudio = useCallback(async () => {
    let stream;
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("getUserMedia not supported");
      }
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch {
      // Browser audio unavailable (e.g. inside Accops VDI) -> fall back to Python OS capture
      return startLocal();
    }

    const ctx = new AudioContext();
    const src = ctx.createMediaStreamSource(stream);
    const vad = new Vad();
    const s = {
      kind: "server",
      stream,
      ctx,
      src,
      node: null,
      chunks: [],
      done: false,
    };
    let last = 0;

    const onAudioSamples = (samples) => {
      // Buffer PCM samples locally without streaming over WebSocket
      const pcm = toPcm16(samples, ctx.sampleRate);
      s.chunks.push(pcm);

      const level = rms(samples);
      const r = vad.feed(level, (samples.length / ctx.sampleRate) * 1000);
      const now = performance.now();
      if (now - last > 120) {
        last = now;
        dispatch({
          type: "mic",
          on: true,
          level: Math.min(1, level * 6),
          speaking: r.speaking,
          engine: "server",
        });
      }
      if (r.stop) finish(r.stop);
    };

    const finish = (reason) => {
      if (s.done) return;
      s.done = true;
      teardown(s);
      live.current = null;
      clearTranscribeTimer();
      dispatch({ type: "mic", on: false, speaking: false });

      if (reason === "no_speech" || reason === "cancel") {
        s.chunks = [];
        send({ type: "cancel" });
        if (reason === "no_speech") {
          dispatch({ type: "say", text: "I didn't hear anything." });
          dispatch({ type: "activate" });
        }
      } else {
        // Concatenate all buffered audio chunks into one contiguous buffer to send in one shot
        let totalLength = 0;
        for (const chunk of s.chunks) {
          totalLength += chunk.length;
        }
        const fullAudio = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of s.chunks) {
          fullAudio.set(chunk, offset);
          offset += chunk.length;
        }
        s.chunks = [];

        dispatch({ type: "heard", text: "" });
        dispatch({ type: "state", state: "thinking" });

        // Send the complete audio recording in one shot directly to the backend
        sendBinary(fullAudio.buffer);

        transcribeTimerRef.current = setTimeout(() => {
          if (!stateRef.current?.turn?.query) {
            dispatch({ type: "heard", text: "" });
            dispatch({ type: "say", text: "I didn't catch that. Please try speaking again or typing your query." });
            dispatch({ type: "activate" });
          }
        }, 25000);
      }
    };
    s.request = finish;

    // Use AudioWorkletNode (falls back to ScriptProcessorNode if unsupported)
    if (ctx.audioWorklet) {
      try {
        const workletCode = `
class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel && channel.length > 0) {
      this.port.postMessage(channel);
    }
    return true;
  }
}
registerProcessor('pcm-capture-processor', PcmCaptureProcessor);
`;
        const blob = new Blob([workletCode], { type: "application/javascript" });
        const workletUrl = URL.createObjectURL(blob);
        await ctx.audioWorklet.addModule(workletUrl);
        URL.revokeObjectURL(workletUrl);

        const workletNode = new AudioWorkletNode(ctx, "pcm-capture-processor");
        workletNode.port.onmessage = (e) => {
          onAudioSamples(e.data);
        };
        src.connect(workletNode);
        workletNode.connect(ctx.destination);
        s.node = workletNode;
      } catch {
        fallbackScriptProcessor(ctx, src, s, onAudioSamples);
      }
    } else {
      fallbackScriptProcessor(ctx, src, s, onAudioSamples);
    }

    live.current = s;
    dispatch({ type: "mic", on: true, engine: "server" });
  }, [dispatch, send, sendBinary, startLocal, teardown, clearTranscribeTimer]);

  const start = useCallback(() => {
    if (live.current) return;
    if (stateRef.current?.config?.speech === "local") {
      return startLocal();
    }
    return startWebAudio();
  }, [startLocal, startWebAudio]);

  const stop = useCallback((reason = "stop") => {
    clearTranscribeTimer();
    dispatch({ type: "mic", on: false, speaking: false });
    if (live.current) {
      live.current.request(reason);
    } else {
      send({ type: "mic_stop" });
    }
  }, [clearTranscribeTimer, dispatch, send]);

  const cancel = useCallback(() => {
    clearTranscribeTimer();
    dispatch({ type: "mic", on: false, speaking: false });
    if (live.current) {
      live.current.request("cancel");
    } else {
      send({ type: "mic_cancel" });
    }
  }, [clearTranscribeTimer, dispatch, send]);

  return {
    start,
    stop,
    cancel,
    active: () => Boolean(live.current || stateRef.current?.mic?.on),
  };
}
