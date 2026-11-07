import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

type QpcWord = {
  id: number;
  surah: string;
  ayah: string;
  word: string;
  text: string;
};

export type QpcAyah = {
  number: number;
  surah_number: number;
  page_number?: number;
  text: string;
  source: 'qpc-v4';
};

export type QpcSurah = {
  number: number;
  name_simple: string;
  number_of_ayahs: number;
};

type QpcData = {
  ayahsBySurah: Map<number, QpcAyah[]>;
  surahs: QpcSurah[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

let qpcDataPromise: Promise<QpcData> | undefined;
const pageNumbersBySurah = new Map<number, Promise<Map<number, number>>>();

async function loadPageNumbers(surahNumber: number): Promise<Map<number, number>> {
  const response = await fetch(
    `https://api.quran.com/api/v4/verses/by_chapter/${surahNumber}?fields=page_number&per_page=300`,
    { cache: 'force-cache' }
  );
  if (!response.ok) {
    throw new Error(`Quran page metadata request failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();
  if (typeof payload !== 'object' || payload === null || !('verses' in payload) || !Array.isArray(payload.verses)) {
    throw new Error(`Quran page metadata for surah ${surahNumber} has an invalid format`);
  }

  const pageNumbers = new Map<number, number>();
  for (const verse of payload.verses) {
    if (typeof verse !== 'object' || verse === null || Array.isArray(verse)) {
      throw new Error(`Quran page metadata for surah ${surahNumber} contains an invalid verse`);
    }
    const verseNumber = Number(verse.verse_number);
    const pageNumber = Number(verse.page_number);
    if (
      !Number.isInteger(verseNumber) || verseNumber < 1
      || !Number.isInteger(pageNumber) || pageNumber < 1 || pageNumber > 604
    ) {
      throw new Error(`Quran page metadata for surah ${surahNumber} contains an invalid page number`);
    }
    pageNumbers.set(verseNumber, pageNumber);
  }
  return pageNumbers;
}

async function getPageNumbers(surahNumber: number): Promise<Map<number, number>> {
  let pageNumbersPromise = pageNumbersBySurah.get(surahNumber);
  if (!pageNumbersPromise) {
    pageNumbersPromise = loadPageNumbers(surahNumber).catch((error: unknown) => {
      pageNumbersBySurah.delete(surahNumber);
      throw error;
    });
    pageNumbersBySurah.set(surahNumber, pageNumbersPromise);
  }
  return pageNumbersPromise;
}

async function loadQpcData(): Promise<QpcData> {
  const filePath = resolve(process.cwd(), '../../data-tafsir/qpc-v4.json');
  const contents = await readFile(filePath, 'utf8');
  const parsed: unknown = JSON.parse(contents);

  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error('QPC dataset must be a keyed object');
  }

  const surahInfoPath = resolve(process.cwd(), '../../data-tafsir/surah-info-id.json');
  const surahInfoContents = await readFile(surahInfoPath, 'utf8');
  const parsedSurahInfo: unknown = JSON.parse(surahInfoContents);
  if (!isRecord(parsedSurahInfo)) {
    throw new Error('Surah metadata must be a keyed object');
  }

  const wordsBySurah = new Map<number, Map<number, QpcWord[]>>();
  for (const [location, value] of Object.entries(parsed)) {
    if (typeof value !== 'object' || value === null || Array.isArray(value)) {
      throw new Error(`Invalid QPC record at ${location}`);
    }

    const word = value as Partial<QpcWord>;
    const surah = Number(word.surah);
    const ayah = Number(word.ayah);
    const wordNumber = Number(word.word);
    const id = Number(word.id);
    if (
      !Number.isInteger(surah) || surah < 1 || surah > 114
      || !Number.isInteger(ayah) || ayah < 1
      || !Number.isInteger(wordNumber) || wordNumber < 1
      || !Number.isInteger(id) || id < 1
      || typeof word.text !== 'string' || !word.text
    ) {
      throw new Error(`Invalid QPC word record at ${location}`);
    }

    let ayahs = wordsBySurah.get(surah);
    if (!ayahs) {
      ayahs = new Map<number, QpcWord[]>();
      wordsBySurah.set(surah, ayahs);
    }
    const words = ayahs.get(ayah) ?? [];
    words.push({
      id,
      surah: String(surah),
      ayah: String(ayah),
      word: String(wordNumber),
      text: word.text,
    });
    ayahs.set(ayah, words);
  }

  const ayahsBySurah = new Map<number, QpcAyah[]>();
  const surahs: QpcSurah[] = [];
  for (const [surahNumber, ayahMap] of Array.from(wordsBySurah.entries())) {
    const surahInfo = parsedSurahInfo[String(surahNumber)];
    if (
      !isRecord(surahInfo)
      || Number(surahInfo.surah_number) !== surahNumber
      || typeof surahInfo.surah_name !== 'string' || !surahInfo.surah_name.trim()
    ) {
      throw new Error(`Missing or invalid name metadata for surah ${surahNumber}`);
    }

    const ayahs = Array.from(ayahMap.entries())
      .sort(([left], [right]) => left - right)
      .map(([ayahNumber, words]) => ({
        number: ayahNumber,
        surah_number: surahNumber,
        text: words.sort((left, right) => Number(left.word) - Number(right.word)).map((word) => word.text).join(' '),
        source: 'qpc-v4' as const,
      }));
    ayahsBySurah.set(surahNumber, ayahs);
    surahs.push({
      number: surahNumber,
      name_simple: surahInfo.surah_name.trim(),
      number_of_ayahs: ayahs.length,
    });
  }

  surahs.sort((left, right) => left.number - right.number);
  return { ayahsBySurah, surahs };
}

export function getQpcData(): Promise<QpcData> {
  qpcDataPromise ??= loadQpcData().catch((error: unknown) => {
    qpcDataPromise = undefined;
    throw error;
  });
  return qpcDataPromise;
}

export async function getQpcSurahAyahs(surahNumber: number): Promise<QpcAyah[]> {
  const { ayahsBySurah } = await getQpcData();
  const ayahs = ayahsBySurah.get(surahNumber);
  if (!ayahs) return [];

  const pageNumbers = await getPageNumbers(surahNumber);
  return ayahs.map((ayah) => {
    const pageNumber = pageNumbers.get(ayah.number);
    if (!pageNumber) {
      throw new Error(`Quran page metadata is missing ${surahNumber}:${ayah.number}`);
    }
    return { ...ayah, page_number: pageNumber };
  });
}
