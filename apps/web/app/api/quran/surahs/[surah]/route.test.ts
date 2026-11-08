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
});
