'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '../src/lib/api/client';
import { amiriQuran, notoSansThai } from '../src/components/ui/fonts';

type RecordValue = Record<string, any>;
type Status = 'idle' | 'loading' | 'success' | 'error' | 'empty';

const agents = [
  { id: 'ibn_kathir', label: 'อิบนุกะษีร' },
  { id: 'al_tabari', label: 'อัฏ-เฏาะบะรี' },
  { id: 'al_qurtubi', label: 'อัลกุรฏุบี' },
  { id: 'ibn_ashur', label: 'อิบนุอาชูร' },
  { id: 'al_saadi', label: 'อัสสะอฺดี' },
  { id: 'al_zuhayli', label: 'วะฮ์บะฮ์ อัซซุฮัยลี' },
];

function listOf(value: any): any[] {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.data)) return value.data;
  if (Array.isArray(value?.surahs)) return value.surahs;
  if (Array.isArray(value?.ayahs)) return value.ayahs;
  if (Array.isArray(value?.translations)) return value.translations;
  return [];
}

function textOf(value: any): string {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return '';
  return value.text ?? value.text_uthmani ?? value.arabic_text ?? value.translation ?? value.translated_text ?? '';
}

function numberOf(value: any, fallback: number): number {
  const number = Number(value?.number ?? value?.surah_number ?? value?.ayah_number);
  return Number.isFinite(number) ? number : fallback;
}

function EvidenceBadge({ status }: { status?: string }) {
  if (!status) return null;
  const colors: Record<string, string> = {
    VERIFIED: 'bg-emerald-100 text-emerald-800',
    'SOURCE-ATTRIBUTED': 'bg-sky-100 text-sky-800',
    'SCHOLARLY-DIFFERENCE': 'bg-amber-100 text-amber-800',
    UNVERIFIED: 'bg-slate-100 text-slate-700',
    'AI-SYNTHESIS': 'bg-violet-100 text-violet-800',
  };
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${colors[status] ?? colors.UNVERIFIED}`}>{status}</span>;
}

function Landing() {
  const router = useRouter();
  const openReader = () => router.push('/?view=reader');
  const features = [
    ['01', 'อ่านอาหรับอย่างถูกทิศทาง', 'ตัวอักษรอาหรับแสดงแบบ RTL พร้อมตัวเลือกอายะฮ์ที่ชัดเจน'],
    ['02', 'คำแปลภาษาไทย', 'ดูคำแปลของอายะฮ์ที่เลือกจากบริการข้อมูล ไม่แสดงข้อมูลจำลอง'],
    ['03', 'ศึกษาอย่างมีหลักฐาน', 'คำอธิบายแสดงสถานะหลักฐานและแหล่งอ้างอิงเมื่อระบบได้รับข้อมูล'],
  ];
  return (
    <main className={`${notoSansThai.className} min-h-screen overflow-hidden bg-[#F5F7F6] text-[#1E293B]`}>
      <header className="sticky top-0 z-20 border-b border-[#073B32]/10 bg-[#F5F7F6]/95 backdrop-blur"><div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10"><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-3 font-semibold tracking-wide text-[#073B32]"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[#073B32] text-lg text-white">ق</span>QURAN AI</button><nav className="hidden gap-8 text-sm text-slate-600 md:flex"><a href="#features">คุณสมบัติ</a><a href="#method">วิธีใช้งาน</a><a href="#evidence">หลักฐาน</a></nav><button onClick={openReader} className="rounded-full bg-[#0E5E4F] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#073B32]">เปิด Reader</button></div></header>
      <section className="relative mx-auto grid min-h-[720px] max-w-7xl items-center gap-16 px-6 py-24 lg:grid-cols-[1fr_.9fr] lg:px-10 lg:py-32"><div><p className="mb-6 text-sm font-semibold uppercase tracking-[.24em] text-[#C9A227]">อ่าน • ศึกษา • ทำความเข้าใจ</p><h1 className="text-5xl font-semibold leading-[1.12] tracking-tight text-[#073B32] md:text-7xl">อ่านอัลกุรอาน<br /><span className="text-[#0E5E4F]">อย่างเข้าใจ</span></h1><p className="mt-8 max-w-xl text-lg leading-8 text-slate-600">พื้นที่ศึกษาอัลกุรอานภาษาไทยที่เชื่อมการอ่านภาษาอาหรับ คำแปล และคำอธิบายไว้ใน workspace เดียว</p><div className="mt-10 flex flex-wrap items-center gap-4"><button onClick={openReader} className="rounded-full bg-[#0E5E4F] px-7 py-4 font-semibold text-white shadow-xl shadow-[#0E5E4F]/20 hover:bg-[#073B32]">เริ่มอ่านกุรอาน <span className="ml-2">→</span></button><a href="#features" className="rounded-full px-5 py-4 text-sm font-semibold text-[#0E5E4F] hover:bg-white">ดูคุณสมบัติ</a></div><div className="mt-12 flex flex-wrap gap-8 text-sm text-slate-500"><span>✓ ภาษาไทยเป็นหลัก</span><span>✓ อาหรับ RTL</span><span>✓ สถานะหลักฐานชัดเจน</span></div></div><div className="relative mx-auto w-full max-w-lg"><div className="absolute -right-8 -top-8 h-32 w-32 rounded-full border border-[#C9A227]/40" /><div className="relative rounded-[2rem] bg-[#E6F4F1] p-5 shadow-2xl shadow-[#073B32]/10 md:p-8"><div className="rounded-2xl border border-[#0E5E4F]/10 bg-white p-5"><div className="mb-6 flex justify-between text-xs text-slate-400"><span>QURAN AI READER</span><span className="rounded-full bg-[#FEF9E7] px-3 py-1 text-[#8A6C11]">Study mode</span></div><div className="h-2 w-24 rounded-full bg-[#C9A227]" /><div className="mt-6 space-y-3"><div className="h-3 rounded-full bg-slate-100" /><div className="h-3 w-4/5 rounded-full bg-slate-100" /><div className="h-3 w-3/5 rounded-full bg-slate-100" /></div><div className="mt-8 rounded-xl bg-[#073B32] p-8 text-center"><div className="mx-auto mb-4 h-16 w-16 rounded-full border border-[#C9A227]/60" /><p className="text-sm text-white/80">เลือกอายะฮ์เพื่อเริ่มศึกษา</p></div></div></div></div></section>

      <section id="features" className="border-y border-slate-200 bg-white"><div className="mx-auto max-w-7xl px-6 py-24 lg:px-10"><div className="max-w-2xl"><p className="text-sm font-semibold uppercase tracking-[.2em] text-[#C9A227]">Built for reflection</p><h2 className="mt-4 text-4xl font-semibold tracking-tight text-[#073B32] md:text-5xl">ทุกส่วนช่วยให้การศึกษา<br />มีความหมายมากขึ้น</h2></div><div className="mt-16 grid gap-5 md:grid-cols-3">{features.map(([number, title, description]) => <article key={number} className="rounded-2xl border border-slate-200 p-7 transition hover:-translate-y-1 hover:border-[#0E5E4F]/30 hover:shadow-lg"><span className="text-sm font-bold text-[#C9A227]">{number}</span><h3 className="mt-12 text-xl font-semibold text-[#073B32]">{title}</h3><p className="mt-4 leading-7 text-slate-600">{description}</p></article>)}</div></div></section>

      <section id="method" className="mx-auto grid max-w-7xl gap-14 px-6 py-24 lg:grid-cols-[.8fr_1.2fr] lg:px-10 lg:py-32"><div><p className="text-sm font-semibold uppercase tracking-[.2em] text-[#C9A227]">Simple study flow</p><h2 className="mt-4 text-4xl font-semibold text-[#073B32]">เริ่มต้นได้ในไม่กี่ขั้นตอน</h2><p className="mt-6 leading-8 text-slate-600">เลือกซูเราะฮ์ เลือกอายะฮ์ แล้วใช้พื้นที่ด้านข้างเพื่ออ่านคำอธิบายตามข้อมูลที่ระบบมี</p></div><div className="space-y-4">{[['01', 'เลือกซูเราะฮ์', 'เปิดสารบัญและเลือกซูเราะฮ์ที่ต้องการอ่าน'], ['02', 'อ่านและเลือกอายะฮ์', 'ดูข้อความอาหรับแบบ RTL และคำแปลภาษาไทย'], ['03', 'ขอคำอธิบาย', 'เลือก agent และตรวจดูสถานะหลักฐานก่อนนำไปศึกษา']].map(([number, title, description]) => <div key={number} className="flex gap-5 rounded-2xl bg-white p-6 shadow-sm"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[#E6F4F1] text-sm font-bold text-[#0E5E4F]">{number}</span><div><h3 className="font-semibold text-[#073B32]">{title}</h3><p className="mt-1 text-sm leading-6 text-slate-600">{description}</p></div></div>)}</div></section>

      <section id="evidence" className="bg-[#073B32] text-white"><div className="mx-auto grid max-w-7xl items-center gap-10 px-6 py-24 lg:grid-cols-[1fr_auto] lg:px-10"><div><p className="text-sm font-semibold uppercase tracking-[.2em] text-[#E6C75A]">Evidence first</p><h2 className="mt-4 max-w-2xl text-4xl font-semibold md:text-5xl">ความชัดเจนสำคัญกว่าคำตอบที่ดูสมบูรณ์</h2><p className="mt-6 max-w-2xl leading-8 text-white/70">ระบบแยกคำอธิบาย AI ออกจากข้อมูลอ้างอิง และไม่สร้าง citation เมื่อไม่มีข้อมูลรองรับ</p></div><button onClick={openReader} className="rounded-full bg-[#C9A227] px-7 py-4 font-semibold text-[#073B32] hover:bg-[#E6C75A]">เปิดพื้นที่ศึกษา →</button></div></section>

      <footer className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-10 text-sm text-slate-500 md:flex-row md:items-center md:justify-between lg:px-10"><span className="font-semibold text-[#073B32]">QURAN AI</span><span>Thai-first Quran study workspace</span><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="text-left hover:text-[#0E5E4F] md:text-right">กลับขึ้นด้านบน ↑</button></footer>
    </main>
  );
}

export default function Home() {
  return <Suspense fallback={<main className="min-h-screen bg-[#f7f5ef]" />}><Workspace /></Suspense>;
}

function Workspace() {
  const params = useSearchParams();
  const reader = params?.get('view') === 'reader';
  if (!reader) return <Landing />;
  const surah = Number(params?.get('surah')) || 1;
  const ayah = Number(params?.get('ayah')) || 1;
  return <Reader key={`${surah}:${ayah}`} initialSurah={surah} initialAyah={ayah} />;
}

function Reader({ initialSurah, initialAyah }: { initialSurah: number; initialAyah: number }) {
  const router = useRouter();
  const [surahs, setSurahs] = useState<any[]>([]);
  const [surah, setSurah] = useState(initialSurah);
  const [ayah, setAyah] = useState(initialAyah);
  const [ayahs, setAyahs] = useState<any[]>([]);
  const [ayahData, setAyahData] = useState<RecordValue | null>(null);
  const [translation, setTranslation] = useState('');
  const [agent, setAgent] = useState(agents[0].id);
  const [tafsir, setTafsir] = useState<RecordValue | null>(null);
  const [surahStatus, setSurahStatus] = useState<Status>('loading');
  const [contentStatus, setContentStatus] = useState<Status>('idle');
  const [tafsirStatus, setTafsirStatus] = useState<Status>('idle');
  const [error, setError] = useState('');

  useEffect(() => { apiClient.get('/surahs').then((data) => { const items = listOf(data); setSurahs(items); setSurahStatus(items.length ? 'success' : 'empty'); }).catch(() => { setSurahStatus('error'); }); }, []);
  useEffect(() => { let cancelled = false; setContentStatus('loading'); setError(''); setTafsir(null); setTafsirStatus('idle'); Promise.all([apiClient.get(`/surahs/${surah}/ayahs`), apiClient.get(`/ayahs/${surah}/${ayah}`), apiClient.get(`/ayahs/${surah}/${ayah}/translations?language=th`)]).then(([surahData, verseData, translationData]) => { if (cancelled) return; const verse = verseData?.data ?? verseData; const thai = listOf(translationData)[0]; setAyahs(listOf(surahData)); setAyahData(verse); setTranslation(textOf(thai)); setContentStatus(verse ? 'success' : 'empty'); }).catch(() => { if (!cancelled) { setContentStatus('error'); setError('ไม่สามารถโหลดข้อมูลอายะฮ์ได้'); } }); return () => { cancelled = true; }; }, [surah, ayah]);

  const selectedSurah = useMemo(() => surahs.find((item) => numberOf(item, 0) === surah), [surahs, surah]);
  const selectSurah = (value: number) => { setSurah(value); setAyah(1); router.replace(`/?view=reader&surah=${value}&ayah=1`, { scroll: false }); };
  const selectAyah = (value: number) => { setAyah(value); router.replace(`/?view=reader&surah=${surah}&ayah=${value}`, { scroll: false }); };
  const loadTafsir = async () => { setTafsirStatus('loading'); setTafsir(null); const result = await apiClient.getAgentExplanation(surah, ayah, agent); if (result) { setTafsir(result); setTafsirStatus('success'); } else setTafsirStatus('error'); };
  const arabic = textOf(ayahData);

  return <main className={`${notoSansThai.className} flex min-h-screen flex-col bg-[#F5F7F6] text-[#1E293B]`}>
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#073B32]/10 bg-white px-5 lg:px-8"><button onClick={() => router.push('/')} className="flex items-center gap-2 font-semibold text-[#073B32]"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#073B32] text-white">ق</span> QURAN AI</button><div className="hidden items-center gap-5 text-xs text-slate-500 md:flex"><span>ภาษาไทย</span><span className="h-4 w-px bg-slate-200" /><span>พื้นที่ศึกษาอัลกุรอาน</span></div><button onClick={() => router.push('/')} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50">หน้าหลัก</button></header>
    <div className="grid flex-1 lg:grid-cols-[260px_minmax(0,1fr)_420px]">
      <aside className="border-b border-slate-200 bg-white p-4 lg:border-b-0 lg:border-r"><div className="mb-6 flex items-center justify-between"><h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">สารบัญซูเราะฮ์</h2><span className="rounded-full bg-[#FEF9E7] px-2 py-1 text-[10px] font-bold text-[#8A6C11]">QURAN</span></div><nav className="mb-6 space-y-1 border-b border-slate-100 pb-5"><button className="flex w-full items-center gap-3 rounded-lg bg-[#E6F4F1] px-3 py-2 text-left text-sm font-semibold text-[#0E5E4F]"><span>▦</span> ดัชนีกุรอาน</button><button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"><span>⌁</span> เส้นทางการศึกษา</button><button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"><span>☆</span> รายการบันทึก</button></nav>{surahStatus === 'loading' && <p className="text-sm text-slate-400">กำลังโหลด...</p>}{surahStatus === 'error' && <p className="text-sm text-red-600">โหลดสารบัญไม่สำเร็จ</p>}<div className="grid max-h-64 grid-cols-2 gap-2 overflow-y-auto lg:max-h-[calc(100vh-130px)] lg:grid-cols-1">{surahs.map((item) => { const id = numberOf(item, 0); return <button key={id} onClick={() => selectSurah(id)} className={`rounded-xl px-3 py-2 text-left text-sm transition ${id === surah ? 'bg-[#e6eee8] font-semibold text-[#193b35]' : 'hover:bg-slate-50'}`}><span className="mr-2 text-xs text-slate-400">{id}</span>{item.name_th ?? item.transliteration ?? item.name ?? `ซูเราะฮ์ ${id}`}</button>; })}</div></aside>
      <section className="min-w-0 border-b border-slate-200 bg-[#F5F7F6] p-5 lg:border-b-0 lg:p-10"><div className="mx-auto max-w-3xl"><div className="mb-8 flex items-center justify-between"><div><p className="text-xs uppercase tracking-widest text-[#b27b45]">ซูเราะฮ์ {selectedSurah?.name_th ?? selectedSurah?.name ?? surah}</p><h1 className="mt-1 text-2xl font-semibold text-[#193b35]">อายะฮ์ {ayah}</h1></div><button onClick={() => router.push('/')} className="rounded-lg border px-3 py-2 text-sm hover:bg-white">หน้าหลัก</button></div>{contentStatus === 'loading' && <div className="space-y-4"><div className="h-36 animate-pulse rounded-2xl bg-slate-200" /><div className="h-8 animate-pulse rounded bg-slate-200" /></div>}{contentStatus === 'error' && <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">{error}<button onClick={() => selectAyah(ayah)} className="ml-3 underline">ลองใหม่</button></div>}{contentStatus === 'empty' && <div className="rounded-2xl border bg-white p-8 text-center text-slate-500">ไม่พบข้อมูลอายะฮ์นี้</div>}{contentStatus === 'success' && <><div className={`${amiriQuran.className} rounded-2xl bg-white p-8 text-right text-4xl leading-[2.1] text-[#193b35] shadow-sm md:text-5xl`} dir="rtl" lang="ar">{arabic || 'ไม่มีข้อความอาหรับจากแหล่งข้อมูล'}</div>{translation ? <div className="mt-5 rounded-2xl border border-[#dbe8df] bg-[#eef6f0] p-6 text-lg leading-8">{translation}</div> : <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-800">ยังไม่มีคำแปลภาษาไทยสำหรับอายะฮ์นี้</div>}<div className="mt-5 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3"><button disabled className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-400">▶ เสียงยังไม่พร้อม</button><button disabled className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-400">☆ บันทึก</button><span className="ml-auto text-xs text-slate-400">อายะฮ์ {ayah}</span></div><div className="mt-6 flex flex-wrap gap-2">{ayahs.map((item) => { const id = numberOf(item, 0); return <button key={id} onClick={() => selectAyah(id)} className={`h-9 min-w-9 rounded-lg border px-2 text-sm ${id === ayah ? 'border-[#193b35] bg-[#193b35] text-white' : 'bg-white hover:border-[#193b35]'}`}>{id}</button>; })}</div></>}</div></section>
      <aside className="flex min-h-[520px] flex-col border-l border-slate-200 bg-white"><div className="border-b p-5"><div className="mb-4 flex gap-5 border-b border-slate-100 text-sm"><button className="border-b-2 border-[#0E5E4F] pb-3 font-semibold text-[#0E5E4F]">ตัฟซีร</button><button disabled className="pb-3 text-slate-400">Quiz</button><button disabled className="pb-3 text-slate-400">Cards</button></div><p className="text-xs font-bold uppercase tracking-widest text-slate-400">คำอธิบายอายะฮ์</p><div className="mt-4 grid grid-cols-2 gap-2">{agents.map((item) => <button key={item.id} onClick={() => setAgent(item.id)} className={`rounded-lg border px-2 py-2 text-xs ${agent === item.id ? 'border-[#193b35] bg-[#e6eee8] text-[#193b35]' : 'hover:bg-slate-50'}`}>{item.label}</button>)}</div><button onClick={loadTafsir} disabled={tafsirStatus === 'loading' || contentStatus !== 'success'} className="mt-4 w-full rounded-xl bg-[#193b35] px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{tafsirStatus === 'loading' ? 'กำลังค้นคว้า...' : 'ขอคำอธิบาย'}</button></div><div className="flex-1 overflow-y-auto p-5">{tafsirStatus === 'idle' && <p className="text-sm leading-7 text-slate-500">เลือกตัวแทนและกด “ขอคำอธิบาย” เพื่อเริ่มศึกษา</p>}{tafsirStatus === 'error' && <p className="rounded-xl bg-amber-50 p-4 text-sm leading-7 text-amber-800">ยังไม่สามารถรับคำอธิบายจากบริการได้ กรุณาลองใหม่ภายหลัง</p>}{tafsir && <div><div className="mb-4 flex items-center justify-between"><h2 className="font-semibold text-[#193b35]">{tafsir.agent_id ?? agent}</h2><EvidenceBadge status={tafsir.evidence_status} /></div><p className="whitespace-pre-wrap text-sm leading-7">{tafsir.answer ?? tafsir.explanation ?? 'ไม่มีคำอธิบายจากบริการ'}</p>{Array.isArray(tafsir.citations) && tafsir.citations.length > 0 ? <div className="mt-6 border-t pt-4"><h3 className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-400">แหล่งอ้างอิง</h3>{tafsir.citations.map((citation: RecordValue, index: number) => <div key={index} className="mb-3 rounded-lg bg-slate-50 p-3 text-xs leading-5"><strong>{citation.work_title ?? citation.source_id ?? 'แหล่งข้อมูล'}</strong><br />{citation.author ?? ''}{citation.edition ? ` · ${citation.edition}` : ''}{citation.page ? ` · หน้า ${citation.page}` : ''}</div>)}</div> : <p className="mt-6 border-t pt-4 text-xs italic text-slate-500">ไม่มีแหล่งอ้างอิงแนบมากับคำอธิบายนี้</p>}{Array.isArray(tafsir.limitations) && tafsir.limitations.length > 0 && <div className="mt-5 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800"><strong>ข้อจำกัด</strong><br />{tafsir.limitations.join(' ')}</div>}</div>}</div></aside>
    </div>
  </main>;
}
