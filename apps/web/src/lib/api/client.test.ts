import { ApiClient, TranslationAudioCapabilities } from './client';

function response({
  ok = true,
  status = 200,
  statusText = 'OK',
  contentType = 'application/json',
  cache = null,
  json = {},
  jsonError,
  bodyText = JSON.stringify(json),
  blob = new Blob(),
}: {
  ok?: boolean;
  status?: number;
  statusText?: string;
  contentType?: string;
  cache?: string | null;
  json?: unknown;
  jsonError?: Error;
  bodyText?: string;
  blob?: Blob;
} = {}) {
  return {
    ok,
    status,
    statusText,
    headers: {
      get: (name: string) => {
        if (name.toLowerCase() === 'content-type') return contentType;
        if (name.toLowerCase() === 'x-audio-cache') return cache;
        return null;
      },
    },
    json: jsonError ? jest.fn().mockRejectedValue(jsonError) : jest.fn().mockResolvedValue(json),
    text: jest.fn().mockResolvedValue(bodyText),
    blob: jest.fn().mockResolvedValue(blob),
  } as unknown as Response;
}

describe('ApiClient translation audio endpoints', () => {
  const client = new ApiClient('https://api.example.test');
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it('parses valid translation audio capabilities and forwards an abort signal', async () => {
    const capabilities: TranslationAudioCapabilities = {
      available: true,
      supported_languages: ['th', 'en', 'id'],
      enabled_editions: ['edition one'],
    };
    const signal = new AbortController().signal;
    global.fetch = jest.fn().mockResolvedValue(response({ json: capabilities }));

    await expect(client.getTranslationAudioCapabilities(signal)).resolves.toEqual(capabilities);
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/quran/translation-audio/capabilities',
      expect.objectContaining({ signal }),
    );
  });

  it('returns an audio Blob and normalized cache status without a JSON Content-Type', async () => {
    const audio = new Blob(['audio bytes'], { type: 'audio/mpeg' });
    global.fetch = jest.fn().mockResolvedValue(response({
      contentType: 'audio/mpeg; charset=binary',
      cache: ' HIT ',
      blob: audio,
    }));

    await expect(client.getTranslationAudio(2, 3, 'edition', 1)).resolves.toEqual({
      blob: audio,
      cacheStatus: 'hit',
    });
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/quran/translation-audio/2/3?edition=edition&speed=1',
      expect.not.objectContaining({
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    );
  });

  it('URL-encodes edition and speed query values', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ contentType: 'audio/mpeg', cache: 'MISS' }));

    await expect(client.getTranslationAudio(1, 2, 'edition /& one', 1.15)).resolves.toMatchObject({
      cacheStatus: 'miss',
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/quran/translation-audio/1/2?edition=edition+%2F%26+one&speed=1.15',
      expect.any(Object),
    );
  });

  it('forwards the abort signal to the audio request and returns unknown for an unrecognized cache header', async () => {
    const signal = new AbortController().signal;
    global.fetch = jest.fn().mockResolvedValue(response({ contentType: 'audio/mpeg', cache: 'stale' }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1, signal)).resolves.toMatchObject({
      cacheStatus: 'unknown',
    });
    expect(global.fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ signal }));
  });

  it('returns unknown when the audio cache header is missing', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ contentType: 'audio/mpeg' }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1)).resolves.toMatchObject({
      cacheStatus: 'unknown',
    });
  });

  it('throws when the capabilities endpoint returns a non-OK response', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({
      ok: false,
      status: 503,
      statusText: 'Unavailable',
      json: { detail: 'temporarily unavailable' },
    }));

    await expect(client.getTranslationAudioCapabilities()).rejects.toThrow('temporarily unavailable');
  });

  it('throws when the audio endpoint returns a non-OK response', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ ok: false, status: 404, statusText: 'Not Found' }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1)).rejects.toThrow('404');
  });

  it.each([
    ['non-JSON', 'upstream unavailable'],
    ['empty', ''],
  ])('returns a controlled status error for %s capabilities error bodies', async (_bodyType, bodyText) => {
    global.fetch = jest.fn().mockResolvedValue(response({
      ok: false,
      status: 502,
      statusText: 'Bad Gateway',
      jsonError: new SyntaxError(bodyText ? 'Unexpected token' : 'Unexpected end of JSON input'),
      bodyText,
    }));

    await expect(client.getTranslationAudioCapabilities()).rejects.toThrow('API Error: 502 Bad Gateway');
  });

  it.each([
    ['non-JSON', 'upstream unavailable'],
    ['empty', ''],
  ])('returns a controlled status error for %s generated-audio error bodies', async (_bodyType, bodyText) => {
    global.fetch = jest.fn().mockResolvedValue(response({
      ok: false,
      status: 502,
      statusText: 'Bad Gateway',
      jsonError: new SyntaxError(bodyText ? 'Unexpected token' : 'Unexpected end of JSON input'),
      bodyText,
    }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1)).rejects.toThrow('API Error: 502 Bad Gateway');
  });

  it('uses a JSON error message from the generated-audio endpoint when available', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
      bodyText: JSON.stringify({ message: 'audio generation is throttled' }),
    }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1)).rejects.toThrow('audio generation is throttled');
  });

  it('rejects audio responses that are not audio/mpeg', async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ contentType: 'application/json' }));

    await expect(client.getTranslationAudio(1, 2, 'edition', 1)).rejects.toThrow(/audio\/mpeg/i);
  });

  it('rejects malformed capabilities payloads', async () => {
    const malformed = {
      available: true,
      supported_languages: ['th', 'fr'],
      enabled_editions: ['edition'],
    };
    global.fetch = jest.fn().mockResolvedValue(response({ json: malformed }));

    await expect(client.getTranslationAudioCapabilities()).rejects.toThrow(/capabilit/i);
  });

  it('sends a structured batch as one numbered, session-scoped question', async () => {
    const result = {
      success: true,
      data: { session_id: 'session-id', message_id: 'message-id' },
    };
    global.fetch = jest.fn().mockResolvedValue(response({ json: result }));

    await client.getAgentExplanation(1, 2, 'ibn_kathir', '1. First\n2. Second', {
      sessionId: 'session-id',
      subquestions: ['First', 'Second'],
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/tafsir/agents/explain?ayah_id=1%3A2&session_id=session-id',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          agent_types: ['ibn_kathir'],
          context: {
            question: '1. First\n2. Second',
            language: 'th',
            subquestions: ['First', 'Second'],
          },
        }),
      }),
    );
  });

  it('requests follow-up suggestions for a message in its session', async () => {
    const result = { suggestions: [] };
    global.fetch = jest.fn().mockResolvedValue(response({ json: result }));

    await expect(client.getChatSuggestions('session-id', 'message-id')).resolves.toEqual(result);

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/chat/suggestions',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ session_id: 'session-id', message_id: 'message-id' }),
        credentials: 'include',
      }),
    );
  });
});
