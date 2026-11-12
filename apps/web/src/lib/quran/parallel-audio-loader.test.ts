import { createParallelAudioLoader } from './parallel-audio-loader';
import type { AudioIdbCache, CachedAudioClip } from './audio-idb-cache';

function cacheStub(initial: CachedAudioClip | null = null): AudioIdbCache {
  let value = initial;
  return {
    get: jest.fn(async () => value),
    put: jest.fn(async (clip) => {
      value = { ...clip, createdAt: clip.createdAt ?? 1, version: 1 };
      return true;
    }),
    delete: jest.fn(async () => undefined),
    cleanup: jest.fn(async () => undefined),
  };
}

describe('parallel audio loader', () => {
  it('deduplicates concurrent loads and caches remote result', async () => {
    const cache = cacheStub();
    const loader = createParallelAudioLoader({ cache });
    const blob = new Blob(['audio'], { type: 'audio/mpeg' });
    const fetchRemote = jest.fn(async () => ({ blob, contentType: 'audio/mpeg' as const }));

    const [first, second] = await Promise.all([
      loader.load('key', fetchRemote),
      loader.load('key', fetchRemote),
    ]);

    expect(fetchRemote).toHaveBeenCalledTimes(1);
    expect(first.blob).toBe(blob);
    expect(second.cacheStatus).toBe('unknown');
    expect(cache.put).toHaveBeenCalledTimes(1);
  });

  it('serves cached audio without fetching remote', async () => {
    const blob = new Blob(['cached'], { type: 'audio/mpeg' });
    const cache = cacheStub({
      key: 'key',
      blob,
      contentType: 'audio/mpeg',
      byteLength: blob.size,
      createdAt: 1,
      version: 1,
    });
    const loader = createParallelAudioLoader({ cache });
    const fetchRemote = jest.fn();

    const result = await loader.load('key', fetchRemote);

    expect(result.cacheStatus).toBe('idb');
    expect(result.blob).toBe(blob);
    expect(fetchRemote).not.toHaveBeenCalled();
  });

  it('cleans failed requests so the same key can retry', async () => {
    const cache = cacheStub();
    const loader = createParallelAudioLoader({ cache });
    const fetchRemote = jest
      .fn()
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce({
        blob: new Blob(['retry'], { type: 'audio/mpeg' }),
        contentType: 'audio/mpeg',
      });

    await expect(loader.load('key', fetchRemote)).rejects.toThrow('network down');
    await expect(loader.load('key', fetchRemote)).resolves.toMatchObject({
      cacheStatus: 'unknown',
    });
    expect(fetchRemote).toHaveBeenCalledTimes(2);
  });
});
