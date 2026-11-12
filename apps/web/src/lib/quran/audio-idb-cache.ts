export const AUDIO_IDB_NAME = "quran-reader-audio";
export const AUDIO_IDB_STORE = "clips";
export const DEFAULT_AUDIO_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export interface CachedAudioClip {
  key: string;
  blob: Blob;
  contentType: string;
  byteLength: number;
  createdAt: number;
  version: number;
}

export interface AudioIdbCache {
  get(key: string): Promise<CachedAudioClip | null>;
  put(clip: Omit<CachedAudioClip, "createdAt" | "version"> & { createdAt?: number }): Promise<boolean>;
  delete(key: string): Promise<void>;
  cleanup(): Promise<void>;
}

interface AudioIdbCacheOptions {
  indexedDB?: IDBFactory;
  dbName?: string;
  version?: number;
  ttlMs?: number;
  now?: () => number;
}

class QuotaExceeded extends Error {
  constructor() {
    super("IndexedDB quota exceeded");
    this.name = "QuotaExceededError";
  }
}

function isQuotaError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const name = "name" in error ? String(error.name) : "";
  return name === "QuotaExceededError" || name === "NS_ERROR_DOM_QUOTA_REACHED";
}

function requestToPromise<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("IndexedDB request failed"));
  });
}

function isCompleteClip(value: unknown, expectedVersion: number): value is CachedAudioClip {
  if (!value || typeof value !== "object") return false;
  const clip = value as CachedAudioClip;
  return (
    typeof clip.key === "string"
    && clip.blob instanceof Blob
    && clip.blob.size > 0
    && typeof clip.contentType === "string"
    && typeof clip.byteLength === "number"
    && clip.byteLength > 0
    && clip.byteLength === clip.blob.size
    && typeof clip.createdAt === "number"
    && clip.version === expectedVersion
  );
}

export function createAudioIdbCache(options: AudioIdbCacheOptions = {}): AudioIdbCache {
  const factory = options.indexedDB;
  const dbName = options.dbName ?? AUDIO_IDB_NAME;
  const version = options.version ?? 1;
  const ttlMs = options.ttlMs ?? DEFAULT_AUDIO_CACHE_TTL_MS;
  const now = options.now ?? (() => Date.now());
  let dbPromise: Promise<IDBDatabase> | null = null;

  function unavailable(): boolean {
    return !factory;
  }

  function openDb(): Promise<IDBDatabase> {
    if (unavailable() || !factory) return Promise.reject(new Error("IndexedDB is unavailable"));
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const request = factory.open(dbName, version);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(AUDIO_IDB_STORE)) {
          db.createObjectStore(AUDIO_IDB_STORE, { keyPath: "key" });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => {
        dbPromise = null;
        reject(request.error ?? new Error("Failed to open audio cache"));
      };
    });
    return dbPromise;
  }

  async function withStore<T>(
    mode: IDBTransactionMode,
    run: (store: IDBObjectStore) => Promise<T>,
  ): Promise<T> {
    const db = await openDb();
    const tx = db.transaction(AUDIO_IDB_STORE, mode);
    const store = tx.objectStore(AUDIO_IDB_STORE);
    return run(store);
  }

  async function readAll(): Promise<CachedAudioClip[]> {
    return withStore("readonly", async (store) => {
      const rows = await requestToPromise(store.getAll());
      return Array.isArray(rows) ? rows.filter((row): row is CachedAudioClip => isCompleteClip(row, version)) : [];
    });
  }

  async function cleanup(): Promise<void> {
    if (unavailable()) return;
    const cutoff = now() - ttlMs;
    await withStore("readwrite", async (store) => {
      const rows = await requestToPromise(store.getAll());
      for (const row of rows) {
        if (!isCompleteClip(row, version) || row.createdAt < cutoff) {
          const key = row && typeof row === "object" && "key" in row ? String((row as CachedAudioClip).key) : "";
          if (key) await requestToPromise(store.delete(key));
        }
      }
    });
  }

  async function evictOldest(): Promise<boolean> {
    const clips = await readAll();
    if (clips.length === 0) return false;
    clips.sort((a, b) => a.createdAt - b.createdAt);
    const oldest = clips[0];
    await withStore("readwrite", (store) => requestToPromise(store.delete(oldest.key)));
    return true;
  }

  return {
    async get(key) {
      if (unavailable()) return null;
      try {
        const clip = await withStore("readonly", (store) => requestToPromise(store.get(key)));
        if (!isCompleteClip(clip, version)) {
          if (clip) await withStore("readwrite", (store) => requestToPromise(store.delete(key)));
          return null;
        }
        if (clip.createdAt < now() - ttlMs) {
          await withStore("readwrite", (store) => requestToPromise(store.delete(key)));
          return null;
        }
        return clip;
      } catch {
        return null;
      }
    },

    async put(input) {
      if (unavailable()) return false;
      if (!(input.blob instanceof Blob) || input.blob.size <= 0 || input.byteLength <= 0) return false;
      if (input.blob.size !== input.byteLength) return false;
      const clip: CachedAudioClip = {
        key: input.key,
        blob: input.blob,
        contentType: input.contentType,
        byteLength: input.byteLength,
        createdAt: input.createdAt ?? now(),
        version,
      };

      const write = () => withStore("readwrite", (store) => requestToPromise(store.put(clip)));

      try {
        await write();
        return true;
      } catch (error) {
        if (!isQuotaError(error) && !(error instanceof QuotaExceeded)) return false;
        try {
          await cleanup();
          await write();
          return true;
        } catch (retryError) {
          if (!isQuotaError(retryError)) return false;
          const evicted = await evictOldest();
          if (!evicted) return false;
          try {
            await write();
            return true;
          } catch {
            return false;
          }
        }
      }
    },

    async delete(key) {
      if (unavailable()) return;
      try {
        await withStore("readwrite", (store) => requestToPromise(store.delete(key)));
      } catch {
        return;
      }
    },

    cleanup,
  };
}
