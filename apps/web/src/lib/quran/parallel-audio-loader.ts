import type { AudioIdbCache } from "./audio-idb-cache";

export type ParallelAudioCacheStatus = "idb" | "hit" | "miss" | "unknown";

export interface LoadedAudioClip {
  key: string;
  blob: Blob;
  contentType: string;
  cacheStatus: ParallelAudioCacheStatus;
}

export interface RemoteAudioClip {
  blob: Blob;
  contentType: string;
  cacheStatus?: Exclude<ParallelAudioCacheStatus, "idb">;
}

export interface ParallelAudioLoader {
  load(
    key: string,
    fetchRemote: (signal: AbortSignal) => Promise<RemoteAudioClip>,
    signal?: AbortSignal,
  ): Promise<LoadedAudioClip>;
  abort(key?: string): void;
}

interface ParallelAudioLoaderOptions {
  cache: AudioIdbCache;
}

class LoadAborted extends Error {
  constructor() {
    super("Audio load aborted");
    this.name = "LoadAborted";
  }
}

function assertCompleteBlob(blob: Blob): void {
  if (!(blob instanceof Blob) || blob.size <= 0) {
    throw new Error("Incomplete audio response");
  }
}

export function createParallelAudioLoader(
  options: ParallelAudioLoaderOptions,
): ParallelAudioLoader {
  const inFlight = new Map<string, Promise<LoadedAudioClip>>();
  const controllers = new Map<string, AbortController>();

  function unlink(key: string, promise: Promise<LoadedAudioClip>): void {
    if (inFlight.get(key) === promise) inFlight.delete(key);
    controllers.delete(key);
  }

  return {
    load(key, fetchRemote, signal) {
      if (signal?.aborted) return Promise.reject(new LoadAborted());

      const existing = inFlight.get(key);
      if (existing) {
        return new Promise((resolve, reject) => {
          const onAbort = () => reject(new LoadAborted());
          signal?.addEventListener("abort", onAbort, { once: true });
          existing.then(
            (clip) => {
              signal?.removeEventListener("abort", onAbort);
              if (signal?.aborted) reject(new LoadAborted());
              else resolve(clip);
            },
            (error) => {
              signal?.removeEventListener("abort", onAbort);
              reject(signal?.aborted ? new LoadAborted() : error);
            },
          );
        });
      }

      const nested = new AbortController();
      controllers.set(key, nested);
      const onOuterAbort = () => nested.abort();
      signal?.addEventListener("abort", onOuterAbort, { once: true });

      const promise = (async () => {
        try {
          const cached = await options.cache.get(key);
          if (nested.signal.aborted) throw new LoadAborted();
          if (cached) {
            return {
              key,
              blob: cached.blob,
              contentType: cached.contentType,
              cacheStatus: "idb" as const,
            };
          }

          const remote = await fetchRemote(nested.signal);
          if (nested.signal.aborted) throw new LoadAborted();
          assertCompleteBlob(remote.blob);
          const contentType = remote.contentType || "application/octet-stream";
          void options.cache.put({
            key,
            blob: remote.blob,
            contentType,
            byteLength: remote.blob.size,
          }).catch(() => undefined);

          return {
            key,
            blob: remote.blob,
            contentType,
            cacheStatus: remote.cacheStatus ?? "unknown",
          };
        } finally {
          signal?.removeEventListener("abort", onOuterAbort);
        }
      })();

      inFlight.set(key, promise);
      void promise.then(
        () => unlink(key, promise),
        () => unlink(key, promise),
      );
      return promise;
    },

    abort(key) {
      if (key) {
        controllers.get(key)?.abort();
        return;
      }
      controllers.forEach((controller) => controller.abort());
    },
  };
}

export async function fetchUrlAudioBlob(
  url: string,
  signal?: AbortSignal,
): Promise<RemoteAudioClip> {
  const response = await fetch(url, { signal, mode: "cors", credentials: "omit" });
  if (!response.ok) {
    throw new Error(`Audio download failed (${response.status})`);
  }
  const blob = await response.blob();
  assertCompleteBlob(blob);
  const contentType = response.headers.get("Content-Type")?.split(";", 1)[0]?.trim() || blob.type;
  return { blob, contentType, cacheStatus: "miss" };
}
