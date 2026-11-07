import Link from 'next/link';
import { notFound } from 'next/navigation';
import { CourseBlocks } from '../../../src/components/courses/course-blocks';
import {
  getChapterContent,
  getCourseBySlug,
  type Course,
  type CourseChapterContent,
} from '../../../src/lib/strapi';

export const dynamic = 'force-dynamic';

interface PageProps {
  params: { slug: string };
  searchParams?: { chapter?: string };
}

export default async function CourseStudyPage({ params, searchParams }: PageProps) {
  let course: Course | null;
  try {
    course = await getCourseBySlug(params.slug);
  } catch (error) {
    return (
      <main className="min-h-screen bg-[#F5F7F6] px-5 py-12">
        <div className="mx-auto max-w-3xl rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm leading-7 text-amber-900">
          <p className="font-semibold">ยังโหลดหลักสูตรจาก Strapi ไม่ได้</p>
          <p>{error instanceof Error ? error.message : 'กรุณาตรวจการเชื่อมต่อแล้วลองใหม่'}</p>
          <Link href="/courses" className="mt-4 inline-block font-semibold underline">กลับหน้าหลักสูตร</Link>
        </div>
      </main>
    );
  }
  if (!course) notFound();

  const requestedChapter = Number(searchParams?.chapter);
  const activeChapter = course.chapters.find((chapter) => chapter.id === requestedChapter) ?? course.chapters[0];
  let chapterContent: CourseChapterContent | null = null;
  let chapterError = '';
  if (activeChapter) {
    try {
      chapterContent = await getChapterContent(activeChapter.id);
    } catch (error) {
      chapterError = error instanceof Error ? error.message : 'โหลดเนื้อหาบทเรียนไม่สำเร็จ';
    }
  }

  return (
    <main className="min-h-screen bg-[#F5F7F6] px-4 py-6 text-slate-800 sm:px-6">
      <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="h-fit rounded-2xl border border-[#dce4e1] bg-white p-4">
          <Link href="/courses" className="text-xs font-semibold text-[#0E5E4F] hover:underline">← หลักสูตรทั้งหมด</Link>
          <h1 className="mt-4 text-lg font-bold text-[#073B32]">{course.title}</h1>
          {course.level && <p className="mt-2 text-xs text-slate-500">ระดับ: {course.level}</p>}
          <nav aria-label="สารบัญบทเรียน" className="mt-5 max-h-[60vh] space-y-2 overflow-y-auto [scrollbar-width:thin]">
            {course.chapters.map((chapter, index) => {
              const selected = chapter.id === activeChapter?.id;
              return (
                <Link
                  key={chapter.id}
                  href={`/courses/${encodeURIComponent(course.slug)}?chapter=${chapter.id}`}
                  aria-current={selected ? 'page' : undefined}
                  className={`block rounded-xl border p-3 text-sm ${selected ? 'border-[#0E5E4F] bg-[#E6F4F1] font-semibold text-[#073B32]' : 'border-slate-100 hover:bg-slate-50'}`}
                >
                  {chapter.chapterNumber ?? index + 1}. {chapter.title}
                </Link>
              );
            })}
          </nav>
        </aside>

        <section>
          {activeChapter ? (
            <>
              <header className="mb-5 rounded-2xl border border-[#dce4e1] bg-white p-5">
                <p className="text-xs font-semibold text-[#0E5E4F]">บทเรียนจาก Strapi CMS</p>
                <h2 className="mt-2 text-2xl font-bold text-[#073B32]">{chapterContent?.title ?? activeChapter.title}</h2>
                {(chapterContent?.surahId || chapterContent?.ayahRange) && (
                  <p className="mt-2 text-sm text-slate-500">
                    {chapterContent.surahId ? `ซูเราะฮ์ ${chapterContent.surahId}` : ''}
                    {chapterContent.ayahRange ? ` · อายะฮ์ ${chapterContent.ayahRange}` : ''}
                  </p>
                )}
              </header>
              {chapterError ? (
                <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{chapterError}</p>
              ) : (
                <CourseBlocks blocks={chapterContent?.contentBlocks ?? []} />
              )}
              <p className="mt-5 text-center text-xs text-slate-500">แบบฝึกหัดในหน้านี้ใช้เพื่อทบทวนส่วนตัว ความคืบหน้ายังไม่ถูกบันทึก</p>
            </>
          ) : (
            <p className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600">หลักสูตรนี้ยังไม่มีบทเรียน</p>
          )}
        </section>
      </div>
    </main>
  );
}
