import test from "node:test";
import assert from "node:assert/strict";
import { Vad, rms } from "./vad.js";

const run = (vad, script) => {                     // script: [[level, ms], ...] in 100 ms frames
  for (const [level, ms] of script) {
    for (let t = 0; t < ms; t += 100) {
      const r = vad.feed(level, 100);
      if (r.stop) return { stop: r.stop, at: vad.elapsed };
    }
  }
  return { stop: null, at: vad.elapsed };
};

test("stops 1.2 s after the person finishes speaking", () => {
  const r = run(new Vad(), [[0.004, 400], [0.1, 1500], [0.004, 3000]]);
  assert.equal(r.stop, "silence");
  assert.ok(r.at >= 400 + 1500 + 1200 && r.at <= 400 + 1500 + 1400, `stopped at ${r.at}`);
});

test("a short pause inside a sentence does not stop the recording", () => {
  const r = run(new Vad(), [[0.004, 400], [0.1, 1000], [0.004, 800], [0.1, 1000], [0.004, 3000]]);
  assert.equal(r.stop, "silence");
  assert.ok(r.at > 400 + 1000 + 800 + 1000 + 1100);
});

test("nobody speaks -> no_speech after 6 s (the recording is cancelled, not sent)", () => {
  const r = run(new Vad(), [[0.005, 10000]]);
  assert.deepEqual([r.stop, r.at], ["no_speech", 6000]);
});

test("a click or cough shorter than 250 ms is not speech", () => {
  const r = run(new Vad(), [[0.004, 400], [0.2, 100], [0.004, 7000]]);
  assert.equal(r.stop, "no_speech");
});

test("continuous speech is cut at the 30 s limit and still sent", () => {
  const r = run(new Vad(), [[0.004, 400], [0.1, 40000]]);
  assert.deepEqual([r.stop, r.at], ["max", 30000]);
});

test("adapts to a noisy room: steady background hum is not speech", () => {
  const v = new Vad();
  const r = run(v, [[0.03, 400], [0.03, 3000], [0.2, 1000], [0.03, 3000]]);        // hum at 0.03, speech at 0.2
  assert.equal(r.stop, "silence");
  assert.ok(v.threshold >= 0.09);
});

test("rms of samples", () => {
  assert.ok(Math.abs(rms(Float32Array.from([0.5, -0.5, 0.5, -0.5])) - 0.5) < 1e-6);
  assert.equal(rms(new Float32Array(0)), 0);
});
