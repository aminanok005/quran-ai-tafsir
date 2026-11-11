const supportedEditions = new Set(['th.thai', 'ar.alafasy', 'en.sahih', 'id.indonesian']);

export const dynamic = 'force-dynamic';

const MAX_ATTEMPTS = 3;

async function fetchWithRetry(url: string): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetch(url, { next: { revalidate: 86400 } });
      const retryable = response.status >= 500 || response.status === 429;
      if (!retryable || attempt === MAX_ATTEMPTS) return response;
    } catch (error) {
      lastError = error;
      if (attempt === MAX_ATTEMPTS) throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, 150 * attempt));
  }
  throw lastError;
}

export async function GET(
  request: Request,
  { params }: { params: { surah: string } }
) {
  const surahNumber = Number(params.surah);
  if (!Number.isInteger(surahNumber) || surahNumber < 1 || surahNumber > 114) {
    return Response.json({ detail: 'หมายเลขซูเราะฮ์ต้องอยู่ระหว่าง 1 ถึง 114' }, { status: 400 });
  }

  const edition = new URL(request.url).searchParams.get('edition');
  if (!edition || !supportedEditions.has(edition)) {
    return Response.json({ detail: 'edition นี้ไม่รองรับ' }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetchWithRetry(`https://api.alquran.cloud/v1/surah/${surahNumber}/${edition}`);
  } catch (error) {
    console.error(`Quran Cloud request failed for surah ${surahNumber} (${edition}):`, error);
    return Response.json({ detail: 'เชื่อมต่อแหล่งคำแปลหรือเสียงอ่านไม่สำเร็จ' }, { status: 503 });
  }

  if (!upstream.ok) {
    console.error(`Quran Cloud returned ${upstream.status} for surah ${surahNumber} (${edition})`);
    return Response.json({ detail: 'แหล่งคำแปลหรือเสียงอ่านตอบกลับผิดพลาด' }, { status: 502 });
  }

  const payload: unknown = await upstream.json();
  if (
    typeof payload !== 'object' || payload === null
    || !('code' in payload) || payload.code !== 200
    || !('data' in payload) || typeof payload.data !== 'object' || payload.data === null
    || !('ayahs' in payload.data) || !Array.isArray(payload.data.ayahs)
  ) {
    console.error(`Quran Cloud returned an invalid ${edition} response for surah ${surahNumber}`);
    return Response.json({ detail: 'ข้อมูลคำแปลหรือเสียงอ่านมีรูปแบบไม่ถูกต้อง' }, { status: 502 });
  }

  return Response.json(payload.data);
}
