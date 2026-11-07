import Link from 'next/link';
import { listCourses, type Course } from '../../src/lib/strapi';

export const dynamic = 'force-dynamic';

export default async function CoursesPage() {
  let courses: Course[] = [];
  let loadError = '';
  try {
    courses = await listCourses();
  } catch (error) {
    loadError = error instanceof Error ? error.message : 'โหลดหลักสูตรจาก Strapi ไม่สำเร็จ';
  }

  return (
    <main className="min-h-screen bg-[#F5F7F6] px-5 py-8 text-slate-800">
      <div className="mx-auto max-w-5xl">
        <Link href="/" className="text-xs font-semibold text-[#0E5E4F] hover:underline">กลับหน้าหลัก</Link>
        <header className="mt-6">
          <p className="text-xs font-semibold text-[#0E5E4F]">QURAN AI · STUDY TRACKS</p>
          <h1 className="mt-2 text-3xl font-bold text-[#073B32]">หลักสูตรการเรียนรู้</h1>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">เนื้อหาบทเรียนจาก Strapi CMS พร้อมอายะฮ์ คำอธิบาย และแบบฝึกหัด</p>
        </header>

        {loadError ? (
          <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-7 text-amber-900" role="alert">
            <p className="font-semibold">ยังเชื่อมต่อหลักสูตรไม่ได้</p>
            <p>{loadError}</p>
            <p className="mt-2 text-xs">ตรวจการตั้งค่า URL และ read-only API permissions ของ Strapi ฝั่งเซิร์ฟเวอร์</p>
          </div>
        ) : courses.length === 0 ? (
          <p className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600">ยังไม่มีหลักสูตรที่เผยแพร่ใน Strapi</p>
        ) : (
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {courses.map((course) => (
              <Link key={course.id} href={`/courses/${encodeURIComponent(course.slug)}`} className="rounded-2xl border border-[#dce4e1] bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-md">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="font-bold text-[#073B32]">{course.title}</h2>
                  {course.level && <span className="rounded-full bg-[#E6F4F1] px-3 py-1 text-[10px] font-semibold text-[#0E5E4F]">{course.level}</span>}
                </div>
                {course.description && <p className="mt-3 text-sm leading-7 text-slate-600">{course.description}</p>}
                <p className="mt-4 text-xs font-semibold text-slate-500">{course.chapters.length} บทเรียน</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
