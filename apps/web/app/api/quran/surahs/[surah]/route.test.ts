/** @jest-environment node */

import { GET } from './route';

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  jest.restoreAllMocks();
});

describe('Quran translation edition route', () => {
  it.each(['th.thai', 'ar.alafasy', 'en.sahih', 'id.indonesian'])(
    'allows the %s edition and returns normalized data',
    async (edition) => {
      const data = { ayahs: [{ number: 1, text: 'sample' }] };
      globalThis.fetch = jest.fn().mockResolvedValue(
        Response.json({ code: 200, data }),
      ) as jest.MockedFunction<typeof fetch>;

      const response = await GET(
        new Request(`http://localhost/api/quran/surahs/1/?edition=${edition}`),
        { params: { surah: '1' } },
      );

      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual(data);
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
      expect(globalThis.fetch).toHaveBeenCalledWith(
        `https://api.alquran.cloud/v1/surah/1/${edition}`,
        { next: { revalidate: 86400 } },
      );
    },
  );

  it('rejects unsupported editions without calling upstream', async () => {
    const fetchMock = jest.fn();
    globalThis.fetch = fetchMock as jest.MockedFunction<typeof fetch>;

    const response = await GET(
      new Request('http://localhost/api/quran/surahs/1/?edition=ar.abdurrahmaansudais'),
      { params: { surah: '1' } },
    );

    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('retries transient network failures and 5xx responses before succeeding', async () => {
    const data = { ayahs: [{ number: 1, text: 'sample' }] };
    const fetchMock = jest
      .fn()
      .mockRejectedValueOnce(new TypeError('fetch failed'))
      .mockResolvedValueOnce(new Response('busy', { status: 503 }))
      .mockResolvedValueOnce(Response.json({ code: 200, data }));
    globalThis.fetch = fetchMock as jest.MockedFunction<typeof fetch>;

    const response = await GET(
      new Request('http://localhost/api/quran/surahs/112/?edition=th.thai'),
      { params: { surah: '112' } },
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(data);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('gives up with 503 after repeated network failures and does not retry 4xx', async () => {
    const failing = jest.fn().mockRejectedValue(new TypeError('fetch failed'));
    globalThis.fetch = failing as jest.MockedFunction<typeof fetch>;
    const down = await GET(
      new Request('http://localhost/api/quran/surahs/112/?edition=th.thai'),
      { params: { surah: '112' } },
    );
    expect(down.status).toBe(503);
    expect(failing).toHaveBeenCalledTimes(3);

    const notFound = jest.fn().mockResolvedValue(new Response('no', { status: 404 }));
    globalThis.fetch = notFound as jest.MockedFunction<typeof fetch>;
    const missing = await GET(
      new Request('http://localhost/api/quran/surahs/112/?edition=th.thai'),
      { params: { surah: '112' } },
    );
    expect(missing.status).toBe(502);
    expect(notFound).toHaveBeenCalledTimes(1);
  });
});
