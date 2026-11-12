export const DEFAULT_CROSSFADE_MS = 180;

export interface ReaderFallbackAudio {
  src: string;
  currentTime: number;
  playbackRate: number;
  error: { code: number; message?: string | null } | null;
  onended: ((event: Event) => void) | null;
  onerror: ((event: Event) => void) | null;
  play(): Promise<void>;
  pause(): void;
}

export interface WebAudioEngine {
  resume(): Promise<void>;
  decode(data: ArrayBuffer | Blob): Promise<AudioBuffer>;
  armNext(buffer: AudioBuffer, playbackRate: number): void;
  playBuffer(
    buffer: AudioBuffer,
    playbackRate: number,
    signal: AbortSignal,
  ): Promise<void>;
  playHtmlFallback(
    audio: ReaderFallbackAudio,
    url: string,
    playbackRate: number,
    signal: AbortSignal,
  ): Promise<void>;
  stop(): void;
  dispose(): void;
}

interface WebAudioEngineOptions {
  createContext?: () => AudioContext;
  crossfadeMs?: number;
  wait?: (ms: number, signal: AbortSignal) => Promise<void>;
}

class PlaybackCancelled extends Error {
  constructor() {
    super("Playback cancelled");
    this.name = "PlaybackCancelled";
  }
}

interface Slot {
  source: AudioBufferSourceNode;
  gain: GainNode;
  buffer: AudioBuffer;
  playbackRate: number;
}

function defaultWait(ms: number, signal: AbortSignal): Promise<void> {
  if (ms <= 0) return Promise.resolve();
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new PlaybackCancelled());
      return;
    }
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(timer);
      reject(new PlaybackCancelled());
    };
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

function fadeSeconds(durationSec: number, configuredMs: number): number {
  if (durationSec <= 0) return 0;
  const configured = configuredMs / 1000;
  const max = durationSec / 4;
  const fade = Math.min(configured, max);
  return fade < 0.02 ? 0 : fade;
}

export function createWebAudioEngine(options: WebAudioEngineOptions = {}): WebAudioEngine {
  const crossfadeMs = options.crossfadeMs ?? DEFAULT_CROSSFADE_MS;
  const wait = options.wait ?? defaultWait;
  let context: AudioContext | null = null;
  let current: Slot | null = null;
  let armed: { buffer: AudioBuffer; playbackRate: number } | null = null;
  let generation = 0;
  let disposed = false;

  function getContext(): AudioContext {
    if (disposed) throw new Error("Audio engine disposed");
    if (context) return context;
    if (options.createContext) {
      context = options.createContext();
      return context;
    }
    const Ctor =
      window.AudioContext
      || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) throw new Error("Web Audio API is unavailable");
    context = new Ctor();
    return context;
  }

  function disconnectSlot(slot: Slot | null, when?: number): void {
    if (!slot) return;
    try {
      if (typeof when === "number") slot.source.stop(when);
      else slot.source.stop();
    } catch {
      /* already stopped */
    }
    try {
      slot.source.disconnect();
    } catch {
      /* ignore */
    }
    try {
      slot.gain.disconnect();
    } catch {
      /* ignore */
    }
  }

  function startSlot(
    ctx: AudioContext,
    buffer: AudioBuffer,
    playbackRate: number,
    startGain: number,
  ): Slot {
    const source = ctx.createBufferSource();
    const gain = ctx.createGain();
    source.buffer = buffer;
    source.playbackRate.value = playbackRate;
    gain.gain.setValueAtTime(startGain, ctx.currentTime);
    source.connect(gain);
    gain.connect(ctx.destination);
    source.start(ctx.currentTime);
    return { source, gain, buffer, playbackRate };
  }

  async function resume(): Promise<void> {
    const ctx = getContext();
    if (ctx.state === "suspended") await ctx.resume();
  }

  return {
    resume,

    async decode(data) {
      const ctx = getContext();
      const buffer = data instanceof Blob ? await data.arrayBuffer() : data;
      return ctx.decodeAudioData(buffer.slice(0));
    },

    armNext(buffer, playbackRate) {
      armed = { buffer, playbackRate };
    },

    async playBuffer(buffer, playbackRate, signal) {
      if (signal.aborted) throw new PlaybackCancelled();
      await resume();
      const ctx = getContext();
      const requestGeneration = generation;

      if (current && current.buffer === buffer) {
        /* already handed off from a previous crossfade */
      } else if (current) {
        const fade = fadeSeconds(
          Math.min(current.buffer.duration / current.playbackRate, buffer.duration / playbackRate),
          crossfadeMs,
        );
        const next = startSlot(ctx, buffer, playbackRate, 0);
        const now = ctx.currentTime;
        current.gain.gain.cancelScheduledValues(now);
        next.gain.gain.cancelScheduledValues(now);
        current.gain.gain.setValueAtTime(current.gain.gain.value, now);
        next.gain.gain.setValueAtTime(0, now);
        if (fade > 0) {
          current.gain.gain.linearRampToValueAtTime(0, now + fade);
          next.gain.gain.linearRampToValueAtTime(1, now + fade);
          disconnectSlot(current, now + fade);
        } else {
          current.gain.gain.setValueAtTime(0, now);
          next.gain.gain.setValueAtTime(1, now);
          disconnectSlot(current, now);
        }
        current = next;
      } else {
        current = startSlot(ctx, buffer, playbackRate, 1);
      }

      const durationMs = (buffer.duration / Math.max(playbackRate, 0.01)) * 1000;
      const fadeMs = fadeSeconds(buffer.duration / Math.max(playbackRate, 0.01), crossfadeMs) * 1000;
      const waitMs = Math.max(0, durationMs - fadeMs);

      try {
        await wait(waitMs, signal);
        if (generation !== requestGeneration || signal.aborted) throw new PlaybackCancelled();

        const next = armed;
        armed = null;
        if (next && fadeMs > 0) {
          const incoming = startSlot(ctx, next.buffer, next.playbackRate, 0);
          const now = ctx.currentTime;
          const fadeSec = fadeMs / 1000;
          if (current) {
            current.gain.gain.cancelScheduledValues(now);
            current.gain.gain.setValueAtTime(current.gain.gain.value, now);
            current.gain.gain.linearRampToValueAtTime(0, now + fadeSec);
            disconnectSlot(current, now + fadeSec);
          }
          incoming.gain.gain.cancelScheduledValues(now);
          incoming.gain.gain.setValueAtTime(0, now);
          incoming.gain.gain.linearRampToValueAtTime(1, now + fadeSec);
          current = incoming;
        } else {
          await wait(fadeMs, signal);
          if (generation !== requestGeneration || signal.aborted) throw new PlaybackCancelled();
          disconnectSlot(current);
          current = null;
        }
      } catch (error) {
        if (generation !== requestGeneration) throw new PlaybackCancelled();
        throw error;
      }
    },

    playHtmlFallback(audio, url, playbackRate, signal) {
      if (!url) return Promise.reject(new Error("ไม่มีเสียงอ่านสำหรับอายะฮ์นี้"));
      audio.src = url;
      audio.currentTime = 0;
      audio.playbackRate = playbackRate;
      return new Promise((resolve, reject) => {
        const cleanup = () => {
          audio.onended = null;
          audio.onerror = null;
          signal.removeEventListener("abort", onAbort);
        };
        const onAbort = () => {
          cleanup();
          audio.pause();
          reject(new PlaybackCancelled());
        };
        audio.onended = () => {
          cleanup();
          resolve();
        };
        audio.onerror = () => {
          cleanup();
          const message = audio.error?.message;
          reject(
            new Error(
              (typeof message === "string" && message.trim()) || "เล่นเสียงอ่านไม่สำเร็จ",
            ),
          );
        };
        signal.addEventListener("abort", onAbort, { once: true });
        if (signal.aborted) {
          onAbort();
          return;
        }
        void audio.play().catch((error: unknown) => {
          cleanup();
          reject(error instanceof Error ? error : new Error("เล่นเสียงอ่านไม่สำเร็จ"));
        });
      });
    },

    stop() {
      generation += 1;
      armed = null;
      disconnectSlot(current);
      current = null;
    },

    dispose() {
      this.stop();
      disposed = true;
      if (context) {
        void context.close?.();
        context = null;
      }
    },
  };
}
