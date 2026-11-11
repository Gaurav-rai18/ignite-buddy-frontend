// Voice activity detection (energy based, adaptive). Pure logic so it can be unit-tested without a microphone.
// Feed it one audio frame at a time; it tells you when to stop recording:
//   "silence"   the person finished speaking (speech heard, then `silenceMs` of quiet)
//   "no_speech" nothing was said for `noSpeechMs`  -> cancel, do not send
//   "max"       hard limit reached                 -> stop and send what we have
export const VAD_DEFAULTS = { silenceMs: 1200, maxMs: 30000, noSpeechMs: 6000, minSpeechMs: 250, floor: 0.012, factor: 3, calibrateMs: 300 };

export const rms = (samples) => {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  return Math.sqrt(sum / (samples.length || 1));
};

export class Vad {
  constructor(opts = {}) {
    this.o = { ...VAD_DEFAULTS, ...opts };
    this.elapsed = 0; this.speechMs = 0; this.silentMs = 0;
    this.noiseSum = 0; this.noiseN = 0; this.threshold = this.o.floor;
  }

  get heardSpeech() { return this.speechMs >= this.o.minSpeechMs; }

  feed(level, dtMs) {
    this.elapsed += dtMs;
    if (this.elapsed <= this.o.calibrateMs) {                 // learn the room's background noise first
      this.noiseSum += level; this.noiseN += 1;
      this.threshold = Math.max(this.o.floor, (this.noiseSum / this.noiseN) * this.o.factor);
      return { speaking: false, stop: null, threshold: this.threshold };
    }
    const speaking = level > this.threshold;
    if (speaking) { this.speechMs += dtMs; this.silentMs = 0; } else if (this.speechMs > 0) { this.silentMs += dtMs; }
    let stop = null;
    if (this.heardSpeech && this.silentMs >= this.o.silenceMs) stop = "silence";
    else if (this.elapsed >= this.o.maxMs) stop = this.heardSpeech ? "max" : "no_speech";
    else if (!this.heardSpeech && this.elapsed >= this.o.noSpeechMs) stop = "no_speech";
    return { speaking, stop, threshold: this.threshold };
  }
}
