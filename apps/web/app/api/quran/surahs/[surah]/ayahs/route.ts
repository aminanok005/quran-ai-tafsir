import { getQpcSurahAyahs } from '../../../../../../src/lib/quran/qpc';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  { params }: { params: { surah: string } }
) {
  const surahNumber = Number(params.surah);
  if (!Number.isInteger(surahNumber) || surahNumber < 1 || surahNumber > 114) {
    return Response.json({ detail: 'หมายเลขซูเราะฮ์ต้องอยู่ระหว่าง 1 ถึง 114' }, { status: 400 });
  }

  try {
    const ayahs = await getQpcSurahAyahs(surahNumber);
    if (!ayahs.length) {
      return Response.json({ detail: 'ไม่พบข้อมูลซูเราะฮ์นี้ใน QPC dataset' }, { status: 404 });
    }
    return Response.json(ayahs);
  } catch (error) {
    console.error(`Failed to load local QPC ayahs for surah ${surahNumber}:`, error);
    return Response.json({ detail: 'ไม่สามารถอ่านข้อมูลอัลกุรอานในเครื่องได้' }, { status: 500 });
  }
}
