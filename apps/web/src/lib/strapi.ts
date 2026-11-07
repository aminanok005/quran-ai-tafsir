import 'server-only';

type JsonRecord = Record<string, unknown>;

export interface CourseChapter {
  id: number;
  title: string;
  chapterNumber?: number;
}

export interface Course {
  id: number;
  title: string;
  slug: string;
  description: string;
  level: string;
  chapters: CourseChapter[];
}

export type LearningBlock =
  | {
      kind: 'theory';
      id: number;
      title: string;
      arabicText: string;
      translationTh: string;
      explanation: string;
      citationReference: string;
    }
  | {
      kind: 'quiz';
      id: number;
      question: string;
      explanation: string;
      points: number;
      options: Array<{ id: number; label: string; value: string; correct: boolean; feedback: string }>;
    }
  | {
      kind: 'vocabulary';
      id: number;
      title: string;
      pairs: Array<{ id: number; arabicWord: string; rootWord: string; meaningTh: string }>;
    }
  | { kind: 'unsupported'; id: number; component: string };

export interface CourseChapterContent extends CourseChapter {
  surahId?: number;
  ayahRange: string;
  contentBlocks: LearningBlock[];
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function asNumber(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

function entityFields(value: unknown): { id: number; fields: JsonRecord } | null {
  if (!isRecord(value)) return null;
  const attributes = isRecord(value.attributes) ? value.attributes : value;
  const id = asNumber(value.id);
  return id === undefined ? null : { id, fields: attributes };
}

function relationItems(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (!isRecord(value)) return [];
  return Array.isArray(value.data) ? value.data : [];
}

function parseCourse(value: unknown): Course | null {
  const entity = entityFields(value);
  if (!entity) return null;
  const fields = entity.fields;
  const title = asString(fields.title);
  const slug = asString(fields.slug);
  if (!title || !slug) return null;

  const chapters = relationItems(fields.chapters)
    .map(entityFields)
    .filter((chapter): chapter is { id: number; fields: JsonRecord } => chapter !== null)
    .map(({ id, fields: chapter }) => ({
      id,
      title: asString(chapter.title) || 'บทเรียน',
      chapterNumber: asNumber(chapter.chapter_number),
    }))
    .sort((left, right) => (left.chapterNumber ?? left.id) - (right.chapterNumber ?? right.id));

  return {
    id: entity.id,
    title,
    slug,
    description: asString(fields.description),
    level: asString(fields.level),
    chapters,
  };
}

function parseBlocks(value: unknown): LearningBlock[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item): LearningBlock[] => {
    if (!isRecord(item)) return [];
    const id = asNumber(item.id) ?? 0;
    const component = asString(item.__component);

    if (component === 'learning.theory-block') {
      return [{
        kind: 'theory',
        id,
        title: asString(item.title),
        arabicText: asString(item.arabic_text),
        translationTh: asString(item.translation_th),
        explanation: asString(item.explanation_markdown ?? item.content_markdown),
        citationReference: asString(item.citation_reference),
      }];
    }
    if (component === 'learning.quiz-block') {
      const options = Array.isArray(item.options)
        ? item.options.flatMap((option, index) => {
            if (!isRecord(option)) return [];
            const label = asString(option.label);
            const value = asString(option.value);
            if (!label || !value) return [];
            return [{
              id: asNumber(option.id) ?? index + 1,
              label,
              value,
              correct: option.is_correct === true,
              feedback: asString(option.feedback),
            }];
          })
        : [];
      const question = asString(item.question);
      return question
        ? [{
            kind: 'quiz',
            id,
            question,
            explanation: asString(item.explanation_on_complete),
            points: asNumber(item.points) ?? 0,
            options,
          }]
        : [];
    }
    if (component === 'learning.vocabulary-matching') {
      const pairs = Array.isArray(item.pairs)
        ? item.pairs.flatMap((pair, index) => {
            if (!isRecord(pair)) return [];
            const arabicWord = asString(pair.arabic_word);
            const meaningTh = asString(pair.meaning_th);
            if (!arabicWord || !meaningTh) return [];
            return [{
              id: asNumber(pair.id) ?? index + 1,
              arabicWord,
              rootWord: asString(pair.root_word),
              meaningTh,
            }];
          })
        : [];
      return [{
        kind: 'vocabulary',
        id,
        title: asString(item.title),
        pairs,
      }];
    }
    return [{ kind: 'unsupported', id, component: component || 'unknown' }];
  });
}

function strapiUrl(path: string, query: Record<string, string>): URL {
  const baseUrl = process.env.STRAPI_API_BASE_URL;
  if (!baseUrl) throw new Error('ยังไม่ได้ตั้งค่า STRAPI_API_BASE_URL บนเซิร์ฟเวอร์');

  let url: URL;
  try {
    url = new URL(path, baseUrl);
  } catch {
    throw new Error('ค่า STRAPI_API_BASE_URL ไม่ถูกต้อง');
  }
  for (const [key, value] of Object.entries(query)) url.searchParams.set(key, value);
  return url;
}

async function getStrapiData(path: string, query: Record<string, string>): Promise<unknown> {
  const url = strapiUrl(path, query);
  const token = process.env.STRAPI_API_TOKEN;
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    next: { revalidate: 3600 },
  });
  if (!response.ok) {
    throw new Error(`Strapi ตอบกลับด้วยสถานะ HTTP ${response.status}`);
  }
  const payload: unknown = await response.json();
  if (!isRecord(payload)) throw new Error('รูปแบบข้อมูลจาก Strapi ไม่ถูกต้อง');
  return payload.data;
}

export async function listCourses(): Promise<Course[]> {
  const data = await getStrapiData('/api/courses', {
    'pagination[pageSize]': '100',
    'sort[0]': 'title:asc',
    'populate[chapters][fields][0]': 'title',
    'populate[chapters][fields][1]': 'chapter_number',
  });
  return relationItems(data).map(parseCourse).filter((course): course is Course => course !== null);
}

export async function getCourseBySlug(slug: string): Promise<Course | null> {
  const data = await getStrapiData('/api/courses', {
    'filters[slug][$eq]': slug,
    'pagination[pageSize]': '1',
    'populate[chapters][fields][0]': 'title',
    'populate[chapters][fields][1]': 'chapter_number',
  });
  return relationItems(data).map(parseCourse).find((course): course is Course => course !== null) ?? null;
}

export async function getChapterContent(id: number): Promise<CourseChapterContent> {
  const data = await getStrapiData(`/api/chapters/${encodeURIComponent(String(id))}`, {
    'populate[content_blocks][populate]': '*',
  });
  const entity = entityFields(data);
  if (!entity) throw new Error('ไม่พบบทเรียนใน Strapi');
  const fields = entity.fields;
  return {
    id: entity.id,
    title: asString(fields.title) || 'บทเรียน',
    chapterNumber: asNumber(fields.chapter_number),
    surahId: asNumber(fields.surah_id),
    ayahRange: asString(fields.ayah_range),
    contentBlocks: parseBlocks(fields.content_blocks),
  };
}
