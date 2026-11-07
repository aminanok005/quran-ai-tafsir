import { getQpcData } from '../../../../src/lib/quran/qpc';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const { surahs } = await getQpcData();
    return Response.json(surahs);
  } catch (error) {
    console.error('Failed to load local QPC surah metadata:', error);
    return Response.json({ detail: 'ไม่สามารถอ่านข้อมูลอัลกุรอานในเครื่องได้' }, { status: 500 });
  }
}
