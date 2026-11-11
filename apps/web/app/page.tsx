'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '../src/lib/api/client';
import type {
  AgentAnalysisResponse,
  AgentAnalysisValidation,
  AgentOutput,
  SuggestedFollowUp,
  TargetStudioArtifactData,
  TranslationAudioCapabilities,
} from '../src/lib/api/client';
import { amiriQuran, notoSansThai } from '../src/components/ui/fonts';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Bookmark, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Sparkles } from 'lucide-react';
import { SourcesPanel, StudioPanel, StudyContext } from '../src/components/workspace/WorkspacePanels';
import { ReaderAudioControls } from '../src/components/workspace/ReaderAudioControls';
import { SuggestedFollowUps } from '../src/components/workspace/SuggestedFollowUps';
import { WorkspaceMobileTabs } from '../src/components/workspace/WorkspaceMobileTabs';
import type { WorkspaceMobileView } from '../src/components/workspace/WorkspaceMobileTabs';
import { createReaderAudioPlayback } from '../src/lib/quran/reader-audio-playback';
import type {
  ReaderAudioLanguage,
  ReaderAudioMode,
  ReaderAudioPlaybackState,
  ReaderAudioSpeed,
  ReaderTranslationVoiceEngine,
  ReaderAudioVoice,
  ReaderSpeechUtterance,
} from '../src/lib/quran/reader-audio-playback';
import { buildTtsSettings, mapLanguageToEdition, resolveTranslationVoiceEngine } from '../src/lib/quran/reader-audio-settings';
import {
  getWorkspaceShortcutAction,
  readWorkspaceLayout,
  serializeWorkspaceLayout,
  WORKSPACE_LAYOUT_STORAGE_KEY,
} from '../src/lib/workspace-layout';

type DataRecord = Record<string, unknown>;
type Status = 'idle' | 'loading' | 'success' | 'error' | 'empty';
type CachedTafsir = { passage: DataRecord; translationError: string };
type DialogueMessage = {
  id: string;
  contextKey: string;
  question: string;
  status: 'loading' | 'success' | 'error';
  answer?: AgentAnalysisResponse;
  error?: string;
  sessionId?: string;
  messageId?: string;
  suggestions: SuggestedFollowUp[];
  suggestionsStatus: 'loading' | 'success' | 'error';
};

const thaiTranslationCache = new Map<number, Promise<unknown>>();

const agents = [
  { id: 'ibn_kathir', label: 'Ibn Kathir', thai: 'อิบนุกะษีร', available: true },
  { id: 'al_tabari', label: 'Al-Tabari', thai: 'อัฏ-เฏาะบะรี', available: true },
  { id: 'al_qurtubi', label: 'Al-Qurtubi', thai: 'อัลกุรฏุบี', available: true },
  { id: 'ibn_ashur', label: 'Ibn Ashur', thai: 'อิบนุอาชูร', available: false },
  { id: 'al_saadi', label: "Al-Sa'di", thai: 'อัสสะอฺดี', available: true },
  { id: 'al_zuhayli', label: 'Al-Zuhayli', thai: 'วะฮ์บะฮ์ อัซซุฮัยลี', available: false },
];

const evidence = [
  { title: 'VERIFIED', description: 'ตรวจสอบกับแหล่งข้อมูลที่ผ่านการยืนยัน', color: 'bg-emerald-100 text-emerald-800' },
  { title: 'SOURCE-ATTRIBUTED', description: 'พบแหล่งอ้างอิงและระบุที่มาได้ชัดเจน', color: 'bg-blue-100 text-blue-800' },
  { title: 'SCHOLARLY-DIFFERENCE', description: 'แสดงทัศนะที่แตกต่างอย่างเป็นธรรม', color: 'bg-amber-100 text-amber-800' },
  { title: 'UNVERIFIED', description: 'ข้อมูลยังอยู่ระหว่างการตรวจสอบ', color: 'bg-slate-100 text-slate-600' },
  { title: 'AI-SYNTHESIS', description: 'สรุปเพื่อการเรียนรู้ ไม่ใช่คำอ้างอิงโดยตรง', color: 'bg-violet-100 text-violet-800' },
];

function isRecord(value: unknown): value is DataRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function listOf(value: unknown): DataRecord[] {
  if (Array.isArray(value)) return value.filter(isRecord);
  if (!isRecord(value)) return [];
  for (const key of ['data', 'surahs', 'ayahs', 'translations']) {
    if (Array.isArray(value[key])) return (value[key] as unknown[]).filter(isRecord);
  }
  return [];
}

function requiredQuranListOf(value: unknown, label: string): DataRecord[] {
  let collection: unknown;
  if (Array.isArray(value)) {
    collection = value;
  } else if (isRecord(value)) {
    const key = ['data', 'surahs', 'ayahs', 'translations'].find((name) => name in value);
    if (key) collection = value[key];
  }
  if (!Array.isArray(collection)) {
    throw new Error(`${label} มีรูปแบบข้อมูลไม่ถูกต้อง`);
  }
  const records = collection.filter(isRecord);
  if (records.length !== collection.length) {
    throw new Error(`${label} มีรูปแบบข้อมูลไม่ถูกต้อง`);
  }
  return records;
}

function textOf(value: unknown): string {
  if (typeof value === 'string') return value;
  if (!isRecord(value)) return '';
  for (const key of ['text', 'text_uthmani', 'arabic_text', 'translation', 'translated_text']) {
    if (typeof value[key] === 'string') return value[key];
  }
  return '';
}

async function getLocalQuran<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, signal ? { signal } : undefined);
  if (!response.ok) {
    const body: unknown = await response.json();
    const detail = isRecord(body) && typeof body.detail === 'string' ? body.detail : 'โหลดข้อมูลอัลกุรอานไม่สำเร็จ';
    throw new Error(detail);
  }
  return response.json();
}

function getThaiTranslation(surah: number): Promise<unknown> {
  const cached = thaiTranslationCache.get(surah);
  if (cached) return cached;

  const request = getLocalQuran<unknown>(`/api/quran/surahs/${surah}/?edition=th.thai`);
  thaiTranslationCache.set(surah, request);
  void request.catch(() => {
    if (thaiTranslationCache.get(surah) === request) thaiTranslationCache.delete(surah);
  });
  return request;
}

function translationParagraphs(value: string): string[] {
  return value.split(/\r?\n\s*\r?\n/).map((paragraph) => paragraph.trim()).filter(Boolean);
}

function stringOf(value: unknown, ...keys: string[]): string {
  if (!isRecord(value)) return '';
  for (const key of keys) {
    if (typeof value[key] === 'string' && value[key]) return value[key] as string;
  }
  return '';
}

function safeHttpUrl(value: unknown): string {
  if (typeof value !== 'string') return '';
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.toString() : '';
  } catch {
    return '';
  }
}

function createUuid(): string {
  const bytes = window.crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function numberOf(value: unknown, fallback: number): number {
  if (!isRecord(value)) return fallback;
  const number = Number(value.numberInSurah ?? value.number_in_surah ?? value.number ?? value.surah_number ?? value.ayah_number);
  return Number.isFinite(number) ? number : fallback;
}

function Icon({ name, className = 'h-5 w-5' }: { name: 'search' | 'menu' | 'book' | 'chat' | 'cards' | 'user' | 'play' | 'spark'; className?: string }) {
  const common = { className, fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, viewBox: '0 0 24 24', 'aria-hidden': true as const };
  if (name === 'search') return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>;
  if (name === 'menu') return <svg {...common}><path d="M4 6h16M4 12h16M4 18h16" /></svg>;
  if (name === 'book') return <svg {...common}><path d="M5 4.5h14v16H5z" /><path d="M9 4.5v16" /></svg>;
  if (name === 'chat') return <svg {...common}><path d="M4 5h16v12H9l-5 3z" /></svg>;
  if (name === 'cards') return <svg {...common}><rect x="6" y="6" width="13" height="15" rx="1" /><path d="M3 17V3h13" /></svg>;
  if (name === 'user') return <svg {...common}><circle cx="12" cy="8" r="3.5" /><path d="M5 21a7 7 0 0 1 14 0" /></svg>;
  if (name === 'play') return <svg {...common} fill="currentColor" stroke="none"><path d="M8 5v14l11-7z" /></svg>;
  return <svg {...common}><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z" /></svg>;
}

function EvidenceBadge({ status }: { status?: string }) {
  if (!status) return null;
  const colors: Record<string, string> = {
    VERIFIED: 'bg-emerald-100 text-emerald-800',
    'SOURCE-ATTRIBUTED': 'bg-blue-100 text-blue-800',
    'SCHOLARLY-DIFFERENCE': 'bg-amber-100 text-amber-800',
    UNVERIFIED: 'bg-slate-100 text-slate-700',
    'AI-SYNTHESIS': 'bg-violet-100 text-violet-800',
  };
  return <span className={`inline-flex rounded-full px-3 py-1 text-[10px] font-bold tracking-wide ${colors[status] ?? colors.UNVERIFIED}`}>{status}</span>;
}

function AgentAnswerCard({
  agentType,
  output,
  validation,
}: {
  agentType: string;
  output: AgentOutput;
  validation?: AgentAnalysisValidation['agent_validations'][string];
}) {
  const explanation = typeof output.explanation === 'string'
    ? output.explanation
    : output.explanation
      ? Object.values(output.explanation)
        .filter((value): value is string => typeof value === 'string')
        .join('\n\n')
      : '';

  return (
    <article className="rounded-xl border border-surface-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-bold text-surface-900">
          {agents.find((item) => item.id === agentType)?.label ?? agentType}
        </h4>
        <EvidenceBadge status={validation?.evidence_level ?? output.evidence_level ?? 'UNVERIFIED'} />
      </div>
      {output.status === 'failed' || output.error
        ? <p role="alert" className="mt-3 text-sm leading-6 text-amber-800">ไม่สามารถยืนยันคำตอบจากแหล่งที่อนุมัติได้: {output.error ?? 'การประมวลผลล้มเหลว'}</p>
        : <p className="mt-3 whitespace-pre-line text-sm leading-7 text-surface-700">{explanation || 'ไม่มีคำอธิบายจากเอเจนต์'}</p>}
      {validation && !validation.valid && (
        <p className="mt-3 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800">
          คำตอบนี้ยังไม่ผ่านการตรวจสอบ: {validation.errors.join(' · ')}
        </p>
      )}
      {output.citations?.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {output.citations.map((citation, index) => {
            const href = safeHttpUrl(citation.reference.url);
            const label = [
              citation.reference.scholar,
              citation.reference.book,
              citation.reference.volume && `เล่ม ${citation.reference.volume}`,
              citation.reference.page && `หน้า ${citation.reference.page}`,
            ].filter(Boolean).join(' · ') || `แหล่งอ้างอิง ${index + 1}`;
            return href
              ? <a
                key={`${citation.passage_id}-${index}`}
                href={href}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[10px] font-medium text-emerald-800 hover:bg-emerald-100"
              >
                [{index + 1}] {label} · {citation.evidence_status}
              </a>
              : <span
                key={`${citation.passage_id}-${index}`}
                className="rounded-full bg-surface-100 px-3 py-1.5 text-[10px] text-surface-700"
              >
                [{index + 1}] {label} · {citation.evidence_status}
              </span>;
          })}
        </div>
      ) : null}
    </article>
  );
}

function BrandMark() {
  return <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#0E5E4F] text-lg text-white">ق</span>;
}

function Landing() {
  const router = useRouter();
  const openReader = () => router.push('/?view=reader');
  const scholars = [
    ['IK', 'Ibn Kathir', 'เน้นรายงานและคำอธิบายจากแหล่งดั้งเดิม'],
    ['AT', 'Al-Tabari', 'รวบรวมรายงานและวิเคราะห์ภาษา'],
    ['AQ', 'Al-Qurtubi', 'พิจารณาประเด็นนิติศาสตร์อิสลาม'],
    ['IA', 'Ibn Ashur', 'วิเคราะห์ภาษาและวัตถุประสงค์'],
    ['AS', "Al-Sa'di", 'อธิบายอย่างชัดเจนและนำไปใช้ได้'],
    ['WZ', 'Wahbah Al-Zuhayli', 'มุมมองร่วมสมัยและเปรียบเทียบฟิกฮ์'],
  ];

  return (
    <main className={`${notoSansThai.className} min-h-screen bg-[#F5F7F6] text-[#1E293B]`}>
      <header className="sticky top-0 z-30 border-b border-[#073B32]/10 bg-white/95 backdrop-blur">
        <div className="mx-auto max-w-7xl px-5 lg:px-10">
          <div className="flex h-[68px] items-center justify-between gap-3">
            <a href="#" className="flex items-center gap-2.5 font-bold tracking-tight text-[#073B32]"><BrandMark />QURAN AI</a>
            <nav aria-label="เมนูหลัก" className="hidden items-center gap-8 text-sm text-slate-600 md:flex">
              <a className="hover:text-[#0E5E4F]" href="#features">หลักฐาน</a>
              <a className="hover:text-[#0E5E4F]" href="#scholars">แนวตัฟซีร</a>
              <a className="hover:text-[#0E5E4F]" href="#learning">เรียนรู้</a>
              <a className="hover:text-[#0E5E4F]" href="/courses">หลักสูตร</a>
              <a className="hover:text-[#0E5E4F]" href="#plans">แพ็กเกจ</a>
            </nav>
            <div className="flex shrink-0 items-center gap-2">
              <button onClick={openReader} className="rounded-full border border-[#d6e0dc] bg-white px-3 py-2 text-xs font-semibold text-[#073B32] hover:bg-[#F5F7F6] sm:px-4">เข้าสู่ระบบ</button>
              <button onClick={openReader} className="rounded-full bg-[#0E5E4F] px-3 py-2 text-xs font-semibold text-white hover:bg-[#073B32] sm:px-4">เริ่มอ่านฟรี</button>
            </div>
          </div>
          <nav aria-label="เมนูหลัก" className="flex gap-2 overflow-x-auto border-t border-slate-100 py-2 text-xs text-slate-600 [scrollbar-width:thin] md:hidden">
            <a className="shrink-0 rounded-full bg-[#F5F7F6] px-3 py-2 hover:bg-[#E6F4F1]" href="#features">หลักฐาน</a>
            <a className="shrink-0 rounded-full bg-[#F5F7F6] px-3 py-2 hover:bg-[#E6F4F1]" href="#scholars">แนวตัฟซีร</a>
            <a className="shrink-0 rounded-full bg-[#F5F7F6] px-3 py-2 hover:bg-[#E6F4F1]" href="#learning">เรียนรู้</a>
            <a className="shrink-0 rounded-full bg-[#F5F7F6] px-3 py-2 hover:bg-[#E6F4F1]" href="/courses">หลักสูตร</a>
            <a className="shrink-0 rounded-full bg-[#F5F7F6] px-3 py-2 hover:bg-[#E6F4F1]" href="#plans">แพ็กเกจ</a>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-5 pb-16 pt-14 text-center md:pb-20 md:pt-20">
        <p className="mx-auto w-fit rounded-full bg-[#E6F4F1] px-4 py-1.5 text-[11px] font-semibold text-[#0E5E4F]">พื้นที่ศึกษาอัลกุรอานอย่างมีหลักฐาน</p>
        <h1 className="mx-auto mt-5 max-w-3xl text-3xl font-bold leading-tight tracking-tight text-[#073B32] sm:text-4xl md:text-5xl">
          ศึกษาอัลกุรอานและตัฟซีร<br className="hidden sm:block" /> อย่างมีหลักฐาน ทุกบรรทัด
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-600 md:text-base">
          อ่านอายะฮ์ เปรียบเทียบกับทัศนะนักปราชญ์ และทบทวนด้วยเครื่องมือการเรียนรู้
          โดยแยกหลักฐานและคำอธิบาย AI ให้เห็นชัดเจน
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button onClick={openReader} className="rounded-lg bg-[#0E5E4F] px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-[#073B32]">เริ่มอ่านฟรี</button>
          <a href="#features" className="rounded-lg border border-[#cbd9d4] bg-white px-5 py-3 text-sm font-semibold text-[#073B32] hover:bg-slate-50">ดูวิธีตรวจสอบหลักฐาน</a>
        </div>

        <div className="mx-auto mt-10 max-w-5xl overflow-hidden rounded-2xl border border-[#d9e3df] bg-white text-left shadow-[0_24px_60px_-32px_rgba(7,59,50,.35)]">
          <div className="flex h-9 items-center gap-1.5 border-b border-slate-100 bg-[#fbfcfc] px-4">
            <i className="h-2 w-2 rounded-full bg-slate-300" /><i className="h-2 w-2 rounded-full bg-slate-300" /><i className="h-2 w-2 rounded-full bg-slate-300" />
            <span className="ml-3 text-[10px] text-slate-400">quran.ai / reader</span>
          </div>
          <div className="grid min-h-[245px] md:grid-cols-[150px_minmax(0,1fr)_250px]">
            <div className="hidden border-r border-slate-100 bg-[#fafcfb] p-4 md:block">
              <p className="mb-3 text-[10px] font-bold text-slate-500">สารบัญ</p>
              <div className="rounded-lg bg-[#E6F4F1] px-3 py-2 text-[10px] font-semibold text-[#0E5E4F]">1 · อัลฟาติฮะฮ์</div>
              <div className="mt-2 px-3 py-2 text-[10px] text-slate-500">2 · อัลบะเกาะเราะฮ์</div>
              <div className="mt-2 px-3 py-2 text-[10px] text-slate-500">3 · อาล อิมรอน</div>
            </div>
            <div className="flex min-h-[210px] flex-col items-center justify-center bg-[#F8FAF9] p-6 text-center">
              <p className="text-[10px] font-semibold text-slate-400">ตัวอย่างพื้นที่อ่าน</p>
              <div className={`${amiriQuran.className} my-5 h-12 w-4/5 rounded-xl bg-white`} aria-hidden="true" />
              <div className="h-2 w-2/3 rounded-full bg-[#e8eeeb]" />
              <p className="mt-3 text-[10px] text-slate-400">ข้อความและคำแปลจะแสดงจาก API เมื่อเปิด Reader</p>
            </div>
            <div className="hidden border-l border-slate-100 p-4 md:block">
              <div className="flex items-center justify-between gap-2 text-[10px] font-semibold text-[#073B32]">Tafsir Agent <EvidenceBadge status="SOURCE-ATTRIBUTED" /></div>
              <div className="mt-3 rounded-lg border border-slate-100 p-3"><div className="h-2 rounded bg-slate-100" /><div className="mt-2 h-2 w-4/5 rounded bg-slate-100" /><div className="mt-2 h-2 w-3/5 rounded bg-slate-100" /></div>
              <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-[#073B32]">สรุปเพื่อการเรียนรู้ <EvidenceBadge status="AI-SYNTHESIS" /></div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-5 py-14 md:py-16">
          <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#9A7914]">ความโปร่งใส</p>
          <h2 className="mt-2 text-2xl font-bold leading-snug text-[#073B32] md:text-3xl">รู้ทันที่มาของข้อความได้จากไหน</h2>
          <p className="mt-2 max-w-2xl text-xs leading-6 text-slate-600 md:text-sm">ทุกคำอธิบายแยกสถานะหลักฐานอย่างชัดเจน หากยังไม่มีข้อมูลที่ตรวจสอบได้ ระบบจะแจ้งข้อจำกัดแทนการสร้างคำตอบ</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {evidence.map((item) => <article key={item.title} className="min-h-24 rounded-xl border border-slate-200 p-4"><span className={`rounded-full px-2 py-1 text-[9px] font-bold ${item.color}`}>{item.title}</span><p className="mt-3 text-[11px] leading-5 text-slate-600">{item.description}</p></article>)}
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#efdfaa] bg-[#FEF9E7] px-4 py-3 text-[11px] leading-5 text-[#604d17]">
            <span><strong>เมื่อหลักฐานไม่พอ:</strong> ระบบจะแจ้งว่า “The available classical sources are insufficient to establish this specific detail.”</span>
            <EvidenceBadge status="UNVERIFIED" />
          </div>
        </div>
      </section>

      <section id="scholars" className="mx-auto max-w-5xl px-5 py-14 md:py-16">
        <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#9A7914]">ตัฟซีร 6 สำนัก</p>
        <h2 className="mt-2 text-2xl font-bold leading-snug text-[#073B32] md:text-3xl">หกเอเจนต์ หกมุมมอง ไม่สวมบทเป็นนักปราชญ์</h2>
        <p className="mt-2 max-w-2xl text-xs leading-6 text-slate-600 md:text-sm">แต่ละเอเจนต์ยึดวิธีพิจารณาตามแนวทาง และระบุในฐานะ “Agent: ตามหนังสือ …” เสมอ</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {scholars.map(([initials, name, description]) => <article key={name} className="rounded-xl border border-slate-200 bg-white p-4"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E6F4F1] text-[10px] font-bold text-[#0E5E4F]">{initials}</span><h3 className="mt-3 text-xs font-bold text-slate-800">{name}</h3><p className="mt-1 text-[10px] leading-5 text-slate-500">{description}</p></article>)}
        </div>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-xs font-bold text-slate-800">เมทริกซ์ข้อคิดเห็น: เทียบกับหลักฐานอ้างอิง</h3><span className="flex gap-2"><EvidenceBadge status="VERIFIED" /><EvidenceBadge status="SCHOLARLY-DIFFERENCE" /></span></div>
          <div className="mt-4 grid grid-cols-[80px_repeat(3,1fr)] items-center gap-2 text-[9px] text-slate-500 sm:grid-cols-[110px_repeat(3,1fr)]">
            <span />
            {scholars.slice(0, 3).map(([, name]) => <span key={name} className="truncate font-semibold text-slate-600">{name}</span>)}
            {[1, 2].map((row) => <div key={row} className="contents"><span>ประเด็นที่ {row}</span><span className={`h-7 rounded-md ${row === 1 ? 'bg-[#d9efeb]' : 'bg-[#FEF0C0]'}`} /><span className={`h-7 rounded-md ${row === 1 ? 'bg-[#d9efeb]' : 'bg-blue-100'}`} /><span className={`h-7 rounded-md ${row === 1 ? 'bg-[#d9efeb]' : 'bg-[#FEF0C0]'}`} /></div>)}
          </div>
          <p className="mt-3 text-[10px] text-slate-400">ภาพประกอบรูปแบบการเปรียบเทียบ · เนื้อหาจริงต้องมาจากผล API</p>
        </div>
      </section>

      <section id="learning" className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-5 py-14 md:py-16">
          <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#9A7914]">เรียนรู้ให้เข้าใจ</p>
          <h2 className="mt-2 text-2xl font-bold text-[#073B32] md:text-3xl">จากการอ่าน สู่ความเข้าใจที่อยู่ติดตัว</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              ['คอร์สแบบบทสั้น 5–10 นาที', 'ทฤษฎี แบบฝึกหัด และสรุป พร้อมเส้นทางการเรียน'],
              ['แฟลชการ์ดพลิก 3 มิติ', 'ทบทวนคำศัพท์และความเข้าใจอย่างเป็นขั้นตอน'],
              ['แบบทดสอบปรับระดับได้', 'เลือก 5, 10 หรือ 20 ข้อ และดูคำอธิบายประกอบ'],
              ['พื้นที่ศึกษาจากเอกสาร PDF', 'อ่านเอกสารพร้อมพื้นที่จดบันทึกและค้นคว้า'],
            ].map(([title, description]) => <article key={title} className="min-h-40 rounded-xl border border-slate-200 p-4"><h3 className="text-xs font-bold text-slate-800">{title}</h3><p className="mt-2 text-[10px] leading-5 text-slate-500">{description}</p><div className="mt-5 flex h-9 items-end gap-2" aria-hidden="true"><div className="h-5 w-1/3 rounded-md bg-[#E6F4F1]" /><div className="h-8 w-1/3 rounded-md bg-[#FEF9E7]" /><div className="h-6 w-1/4 rounded-md bg-slate-100" /></div><p className="mt-3 text-[9px] font-semibold text-slate-400">ตัวอย่างแนวคิด · ยังไม่เปิดใช้งาน</p></article>)}
          </div>
        </div>
      </section>

      <section id="plans" className="mx-auto max-w-5xl px-5 py-14 md:py-16">
        <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#9A7914]">แพ็กเกจ</p>
        <h2 className="mt-2 text-2xl font-bold text-[#073B32] md:text-3xl">เริ่มฟรี อัปเกรดเมื่อพร้อม</h2>
        <div className="mt-6 grid max-w-3xl gap-3 sm:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white p-5"><h3 className="text-xs font-bold">ฟรี</h3><p className="mt-3 text-3xl font-bold text-[#073B32]">$0</p><ul className="mt-4 space-y-2 text-[10px] text-slate-600"><li>• เข้าถึงสารบัญและ Reader</li><li>• คำแปลตามข้อมูลที่มี</li><li>• ศึกษาผ่าน Al-Sa'di</li></ul><button onClick={openReader} className="mt-5 w-full rounded-lg border border-[#cbd9d4] py-2 text-xs font-semibold text-[#073B32] hover:bg-[#F5F7F6]">เริ่มอ่านฟรี</button></article>
          <article className="rounded-xl border border-[#073B32] bg-[#073B32] p-5 text-white"><div className="flex items-center justify-between"><h3 className="text-xs font-bold">Premium Scholar</h3><span className="rounded-full bg-[#C9A227] px-2 py-1 text-[9px] font-bold text-[#073B32]">ตัวอย่าง</span></div><p className="mt-3 text-3xl font-bold">$5.99 <span className="text-[10px] font-normal text-white/70">ต่อเดือน · ราคาเสนอ</span></p><ul className="mt-4 space-y-2 text-[10px] text-white/80"><li>• เข้าถึงเอเจนต์ที่รองรับ</li><li>• เปรียบเทียบมุมมองนักปราชญ์</li><li>• เครื่องมือทบทวนการเรียนรู้</li></ul><button disabled className="mt-5 w-full cursor-not-allowed rounded-lg bg-[#C9A227] py-2 text-xs font-semibold text-[#073B32] opacity-80">ยังไม่เปิดให้สมัคร</button></article>
        </div>
        <p className="mt-3 text-[10px] text-slate-400">แพ็กเกจ Premium เป็นเพียงตัวอย่างจากแบบออกแบบ ยังไม่มีการเรียกเก็บเงินหรือสมัครใช้งาน</p>
      </section>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-5 py-7 text-[10px] text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span className="font-bold text-[#073B32]">QURAN AI</span><span>พื้นที่ศึกษาอัลกุรอานโดยยึดหลักฐานและความโปร่งใส</span><nav className="flex gap-4"><a href="#features">หลักฐาน</a><a href="#scholars">นักปราชญ์</a><a href="#plans">แพ็กเกจ</a></nav></div>
      </footer>
    </main>
  );
}

export default function Home() {
  return <Suspense fallback={<main className="min-h-screen bg-[#F5F7F6]" />}><Workspace /></Suspense>;
}

function Workspace() {
  const params = useSearchParams();
  const router = useRouter();
  const reader = params?.get('view') === 'reader';
  if (!reader) return <Landing />;
  const surah = Number(params?.get('surah')) || 1;
  const ayah = Number(params?.get('ayah')) || 1;
  return <Reader initialSurah={surah} initialAyah={ayah} />;
}

function Reader({ initialSurah, initialAyah }: { initialSurah: number; initialAyah: number }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [surahs, setSurahs] = useState<DataRecord[]>([]);
  const [surah, setSurah] = useState(initialSurah);
  const [ayah, setAyah] = useState(initialAyah);
  const [contentRequestVersion, setContentRequestVersion] = useState(0);
  const [ayahs, setAyahs] = useState<DataRecord[]>([]);
  const [translationsByAyah, setTranslationsByAyah] = useState<Record<number, string>>({});
  const [audioByAyah, setAudioByAyah] = useState<Record<number, string>>({});
  const [translationStatus, setTranslationStatus] = useState<Status>('idle');
  const [agent, setAgent] = useState(agents[0].id);
  const [tafsir, setTafsir] = useState<DataRecord | null>(null);
  const [surahStatus, setSurahStatus] = useState<Status>('loading');
  const [contentStatus, setContentStatus] = useState<Status>('idle');
  const [tafsirStatus, setTafsirStatus] = useState<Status>('idle');
  const [error, setError] = useState('');
  const [ayahTranslationError, setAyahTranslationError] = useState('');
  const [audioError, setAudioError] = useState('');
  const [playbackMode, setPlaybackMode] = useState<ReaderAudioMode>('recitation');
  const [playbackLanguage, setPlaybackLanguage] = useState<ReaderAudioLanguage>('th');
  const [playbackSettingsOpen, setPlaybackSettingsOpen] = useState(false);
  const [translationVoiceChoice, setTranslationVoiceEngine] = useState<ReaderTranslationVoiceEngine | null>(null);
  const [playbackSpeed, setPlaybackSpeed] = useState<ReaderAudioSpeed>(1);
  const [translationAudioCapabilities, setTranslationAudioCapabilities] = useState<TranslationAudioCapabilities | null>(null);
  const [translationAudioCapabilityError, setTranslationAudioCapabilityError] = useState('');
  const [playbackState, setPlaybackState] = useState<ReaderAudioPlaybackState>('idle');
  const [playbackStatus, setPlaybackStatus] = useState('พร้อมเล่นเสียง');
  const [translationError, setTranslationError] = useState('');
  const [search, setSearch] = useState('');
  const [arabicFontSize, setArabicFontSize] = useState(36);
  const [mobileSurahMenuOpen, setMobileSurahMenuOpen] = useState(false);
  const [mobileView, setMobileView] = useState<WorkspaceMobileView>('reader');
  const [centerView, setCenterView] = useState<'reader' | 'dialogue'>('reader');
  const [dialogueMode, setDialogueMode] = useState<'tafsir' | 'explain' | 'compare'>('tafsir');
  const [questionDraft, setQuestionDraft] = useState('');
  const [dialogueMessages, setDialogueMessages] = useState<DialogueMessage[]>([]);
  const chatContextKey = `${surah}:${ayah}`;
  const chatSessionRef = useRef<{ contextKey: string; epoch: number; sessionId: string | null }>({
    contextKey: `${initialSurah}:${initialAyah}`,
    epoch: 0,
    sessionId: null,
  });
  if (chatSessionRef.current.contextKey !== chatContextKey) {
    chatSessionRef.current = {
      contextKey: chatContextKey,
      epoch: chatSessionRef.current.epoch + 1,
      sessionId: null,
    };
  }
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [studioOpen, setStudioOpen] = useState(true);
  const [selectedSources, setSelectedSources] = useState<string[]>(['quran']);
  const [panelLayout, setPanelLayout] = useState({ sources: 24, reader: 49, studio: 27 });
  const audioRef = useRef<HTMLAudioElement>(null);
  const playbackControllerRef = useRef<ReturnType<typeof createReaderAudioPlayback> | null>(null);
  const playbackAyahChangeRef = useRef<(nextAyah: number) => void>(() => {});
  const spokenTranslationLoaderRef = useRef<
    (targetSurah: number, language: ReaderAudioLanguage, signal: AbortSignal) => Promise<Record<number, string>>
  >(async () => ({}));
  const spokenTranslationCache = useRef(new Map<string, Record<number, string>>());
  const translationAudioCapabilitiesRef = useRef<TranslationAudioCapabilities | null>(null);
  translationAudioCapabilitiesRef.current = translationAudioCapabilities;
  const tafsirCache = useRef(new Map<string, CachedTafsir>());
  const tafsirRequests = useRef(new Map<string, Promise<CachedTafsir>>());
  const activeTafsirKey = useRef(`${initialSurah}:${initialAyah}:${agents[0].id}`);
  const comparisonQuery = useQuery({
    queryKey: ['agents', 'compare', surah, ayah],
    queryFn: () => apiClient.compareAgents(surah, ayah),
    enabled: centerView === 'dialogue' && dialogueMode === 'compare',
    retry: false,
    staleTime: 60_000,
  });

  useEffect(() => {
    const request = new AbortController();
    void apiClient.getTranslationAudioCapabilities(request.signal)
      .then((capabilities) => {
        if (request.signal.aborted) return;
        setTranslationAudioCapabilities(capabilities);
        setTranslationAudioCapabilityError('');
      })
      .catch((failure: unknown) => {
        if (request.signal.aborted) return;
        setTranslationAudioCapabilities(null);
        setTranslationAudioCapabilityError(
          failure instanceof Error ? failure.message : 'could not check AI audio availability',
        );
      });
    return () => request.abort();
  }, []);

  useEffect(() => {
    const savedLayout = readWorkspaceLayout(window.localStorage);
    setSourcesOpen(savedLayout.sourcesOpen);
    setStudioOpen(savedLayout.studioOpen);
    setPanelLayout(savedLayout.panelLayout);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(WORKSPACE_LAYOUT_STORAGE_KEY, serializeWorkspaceLayout({
      sourcesOpen,
      studioOpen,
      panelLayout,
    }));
  }, [panelLayout, sourcesOpen, studioOpen]);

  useEffect(() => {
    const onShortcut = (event: KeyboardEvent) => {
      const action = getWorkspaceShortcutAction(event.key, event.target);
      if (action === null) return;
      event.preventDefault();
      if (action === 'toggle-sources') {
        setSourcesOpen((open) => !open);
      } else if (action === 'toggle-studio') {
        setStudioOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', onShortcut);
    return () => window.removeEventListener('keydown', onShortcut);
  }, []);

  useEffect(() => {
    setSurah(initialSurah);
    setAyah(initialAyah);
  }, [initialSurah, initialAyah]);

  useEffect(() => {
    setDialogueMessages([]);
    setQuestionDraft('');
  }, [surah, ayah]);

  useEffect(() => {
    getLocalQuran<unknown>('/api/quran/surahs/')
      .then((data) => {
        const items = requiredQuranListOf(data, 'สารบัญซูเราะฮ์');
        setSurahs(items);
        setSurahStatus(items.length ? 'success' : 'empty');
      })
      .catch((failure: unknown) => {
        setSurahStatus('error');
        setError(failure instanceof Error ? failure.message : 'โหลดสารบัญไม่สำเร็จ');
      });
  }, []);

  useEffect(() => {
    let cancelled = false;
    setContentStatus('loading');
    setError('');
    setTranslationsByAyah({});
    setAudioByAyah({});
    setTranslationStatus('loading');
    setAyahTranslationError('');
    setAudioError('');
    setTafsir(null);
    getLocalQuran<unknown>(`/api/quran/surahs/${surah}/ayahs/`).then((surahData) => {
      if (cancelled) return;
      const items = requiredQuranListOf(surahData, 'ข้อมูลอายะฮ์');
      setAyahs(items);
      setContentStatus(items.length ? 'success' : 'empty');
    }).catch((failure: unknown) => {
      if (!cancelled) {
        setContentStatus('error');
        setError(failure instanceof Error ? failure.message : 'ไม่สามารถโหลดข้อมูลอายะฮ์ได้');
      }
    });
    getThaiTranslation(surah).then((translationData) => {
      if (cancelled) return;
      const translations: Record<number, string> = {};
      for (const verse of listOf(translationData)) {
        const number = numberOf(verse, 0);
        const text = textOf(verse).replace(/\u200B/g, '').trim();
        if (number > 0 && text) translations[number] = text;
      }
      setTranslationsByAyah(translations);
      setTranslationStatus('success');
    }).catch((failure: unknown) => {
      if (!cancelled) {
        setTranslationStatus('error');
        setAyahTranslationError(failure instanceof Error ? failure.message : 'โหลดคำแปลภาษาไทยไม่สำเร็จ');
      }
    });
    getLocalQuran<unknown>(`/api/quran/surahs/${surah}/?edition=ar.alafasy`).then((audioData) => {
      if (cancelled) return;
      const audio: Record<number, string> = {};
      for (const verse of listOf(audioData)) {
        const number = numberOf(verse, 0);
        const url = stringOf(verse, 'audio');
        if (number > 0 && url) audio[number] = url;
      }
      setAudioByAyah(audio);
    }).catch((failure: unknown) => {
      if (!cancelled) setAudioError(failure instanceof Error ? failure.message : 'โหลดข้อมูลเสียงอ่านไม่สำเร็จ');
    });
    return () => { cancelled = true; };
  }, [contentRequestVersion, surah]);

  spokenTranslationLoaderRef.current = async (targetSurah, language, signal) => {
    const edition = language === 'th' ? 'th.thai' : language === 'en' ? 'en.sahih' : 'id.indonesian';
    const cacheKey = `${targetSurah}:${edition}`;
    const cached = spokenTranslationCache.current.get(cacheKey);
    if (cached) return cached;
    if (language === 'th' && targetSurah === surah && Object.keys(translationsByAyah).length > 0) {
      return translationsByAyah;
    }

    const data = await getLocalQuran<unknown>(
      `/api/quran/surahs/${targetSurah}/?edition=${edition}`,
      signal,
    );
    const translations: Record<number, string> = {};
    for (const verse of requiredQuranListOf(data, `คำแปลภาษา ${language}`)) {
      const number = numberOf(verse, 0);
      const text = textOf(verse).replace(/\u200B/g, '').trim();
      if (number > 0 && text) translations[number] = text;
    }
    if (!signal.aborted) spokenTranslationCache.current.set(cacheKey, translations);
    return translations;
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const synthesis = typeof window.speechSynthesis === 'undefined' ? null : window.speechSynthesis;
    const speech = synthesis
      ? {
          getVoices: () => synthesis.getVoices(),
          speak: (utterance: ReaderSpeechUtterance) => {
            const nativeUtterance = new SpeechSynthesisUtterance(utterance.text);
            nativeUtterance.lang = utterance.lang;
            nativeUtterance.rate = utterance.rate;
            const nativeVoice = synthesis.getVoices().find((voice) =>
              utterance.voice.voiceURI
                ? voice.voiceURI === utterance.voice.voiceURI
                : voice.lang === utterance.voice.lang && voice.name === utterance.voice.name,
            );
            if (!nativeVoice) throw new Error(`ไม่พบเสียงพูดภาษา ${utterance.lang} ในเบราว์เซอร์`);
            nativeUtterance.voice = nativeVoice;
            nativeUtterance.onend = () => utterance.onend?.();
            nativeUtterance.onerror = () => utterance.onerror?.();
            synthesis.speak(nativeUtterance);
          },
          cancel: () => synthesis.cancel(),
          addEventListener: (_type: 'voiceschanged', listener: () => void) => {
            synthesis.addEventListener('voiceschanged', listener);
          },
          removeEventListener: (_type: 'voiceschanged', listener: () => void) => {
            synthesis.removeEventListener('voiceschanged', listener);
          },
        }
      : null;
    const controller = createReaderAudioPlayback({
      audio,
      speech,
      createUtterance: (text: string, voice: ReaderAudioVoice) => ({
        text,
        lang: voice.lang,
        voice,
        rate: 1,
        onend: null,
        onerror: null,
      }),
      loadTranslations: (targetSurah, language, signal) =>
        spokenTranslationLoaderRef.current(targetSurah, language, signal),
      loadGeneratedTranslationAudio: async (targetSurah, targetAyah, language, speed, signal) => {
        const editionConfig = mapLanguageToEdition(language);
        if (!editionConfig) {
          throw new Error('AI audio is unavailable for the selected translation edition.');
        }
        const edition = editionConfig.edition;
        const capabilities = translationAudioCapabilitiesRef.current;
        if (
          !capabilities?.available
          || !capabilities.supported_languages.includes(language)
          || !capabilities.enabled_editions.includes(edition)
        ) {
          throw new Error('AI audio is unavailable for the selected translation edition.');
        }
        const generatedAudio = await apiClient.getTranslationAudio(
          targetSurah,
          targetAyah,
          edition,
          speed,
          signal,
        );
        return {
          url: URL.createObjectURL(generatedAudio.blob),
          cacheStatus: generatedAudio.cacheStatus,
        };
      },
      revokeGeneratedAudioUrl: (url) => URL.revokeObjectURL(url),
      onAyahChange: (nextAyah) => playbackAyahChangeRef.current(nextAyah),
      onStatus: setPlaybackStatus,
      onStateChange: setPlaybackState,
    });
    playbackControllerRef.current = controller;
    return () => {
      controller.dispose();
      playbackControllerRef.current = null;
    };
  }, []);

  const selectedSurah = useMemo(() => surahs.find((item) => numberOf(item, 0) === surah), [surahs, surah]);
  const surahName = stringOf(selectedSurah, 'name_th', 'name_simple', 'transliteration', 'name') || 'อัลกุรอาน';
  const rawAyahCount = Number(
    selectedSurah?.number_of_ayahs
      ?? selectedSurah?.ayah_count
      ?? selectedSurah?.verses_count
      ?? ayahs.length
  );
  const safeAyahCount = Number.isFinite(rawAyahCount) && rawAyahCount > 0 ? rawAyahCount : 0;
  const readingProgress = safeAyahCount ? Math.min((ayah / safeAyahCount) * 100, 100) : 0;
  const qpcFontPages = useMemo(
    () => Array.from(new Set(ayahs.map((item) => Number(item.page_number)).filter((page) => Number.isInteger(page) && page >= 1 && page <= 604))),
    [ayahs]
  );
  const filteredAyahs = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return ayahs;
    return ayahs.filter((item) => {
      const number = numberOf(item, 0);
      const verseText = textOf(item);
      return `${surah}:${number}`.includes(query) || String(number).includes(query) || verseText.includes(search.trim());
    });
  }, [ayahs, search, surah]);
  const activateTafsir = useCallback(async (targetSurah: number, targetAyah: number, targetAgent: string) => {
    const key = `${targetSurah}:${targetAyah}:${targetAgent}`;
    activeTafsirKey.current = key;
    setError('');

    const cached = tafsirCache.current.get(key);
    if (cached) {
      setTafsir(cached.passage);
      setTranslationError(cached.translationError);
      setTafsirStatus('success');
      return;
    }

    setTafsir(null);
    setTranslationError('');
    setTafsirStatus('loading');
    let request = tafsirRequests.current.get(key);
    if (!request) {
      request = (async () => {
        const response = await apiClient.getTafsirPassage(targetSurah, targetAyah, targetAgent);
        const passage = isRecord(response) && isRecord(response.data) ? response.data : null;
        if (!passage) throw new Error('เซิร์ฟเวอร์ส่งข้อมูลตัฟซีรในรูปแบบที่ไม่รู้จัก');

        let translatedPassage = passage;
        let translationError = '';
        if (!(typeof passage.thai_translation === 'string' && passage.thai_translation.trim())) {
          if (passage.translation_allowed !== true) {
            translationError = stringOf(passage, 'translation_block_reason') || 'แหล่งข้อมูลนี้ยังไม่ได้รับอนุมัติสำหรับการแปลด้วย AI';
          } else {
            try {
              const translationResponse = await apiClient.translateApiTafsirPassage(
                targetSurah,
                targetAyah,
                targetAgent,
              );
              const translationData = isRecord(translationResponse) && isRecord(translationResponse.data)
                ? translationResponse.data
                : null;
              const translatedText = stringOf(translationData, 'thai_translation');
              if (!translatedText) throw new Error('OpenAI ไม่ได้ส่งคำแปลกลับมา');
              translatedPassage = { ...passage, thai_translation: translatedText };
            } catch (failure) {
              translationError = failure instanceof Error ? failure.message : 'แปลตัฟซีรไม่สำเร็จ';
            }
          }
        }

        const result = { passage: translatedPassage, translationError };
        tafsirCache.current.set(key, result);
        return result;
      })().finally(() => {
        tafsirRequests.current.delete(key);
      });
      tafsirRequests.current.set(key, request);
    }

    try {
      const result = await request;
      if (activeTafsirKey.current !== key) return;
      setTafsir(result.passage);
      setTranslationError(result.translationError);
      setTafsirStatus('success');
    } catch (failure) {
      if (activeTafsirKey.current !== key) return;
      setError(failure instanceof Error ? failure.message : 'โหลดตัฟซีรไม่สำเร็จ');
      setTafsirStatus('error');
    }
  }, []);

  useEffect(() => {
    void activateTafsir(surah, ayah, agent);
  }, [activateTafsir, surah, ayah, agent]);

  const selectSurah = (value: number) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    setSurah(value);
    setAyah(1);
    setMobileSurahMenuOpen(false);
    setSearch('');
    activeTafsirKey.current = `${value}:1:${agent}`;
    void activateTafsir(value, 1, agent);
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set('view', 'reader');
    nextUrl.searchParams.set('surah', String(value));
    nextUrl.searchParams.set('ayah', '1');
    window.history.replaceState(null, '', nextUrl);
  };
  const updateAyahSelection = (value: number) => {
    setAyah(value);
    void activateTafsir(surah, value, agent);
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set('view', 'reader');
    nextUrl.searchParams.set('surah', String(surah));
    nextUrl.searchParams.set('ayah', String(value));
    window.history.replaceState(null, '', nextUrl);
  };
  playbackAyahChangeRef.current = (nextAyah) => {
    updateAyahSelection(nextAyah);
    const scrollToAyah = () => {
      const targets = document.querySelectorAll<HTMLElement>(`[data-reader-ayah="${nextAyah}"]`);
      const visibleTarget = Array.from(targets).find((target) => target.getClientRects().length > 0) ?? targets[0];
      visibleTarget?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
    };
    scrollToAyah();
  };
  const selectAyah = (value: number) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    updateAyahSelection(value);
  };
  const editionConfig = mapLanguageToEdition(playbackLanguage);
  const ttsSettings = buildTtsSettings(
    translationAudioCapabilities,
    editionConfig?.edition ?? '',
    playbackLanguage,
    translationAudioCapabilityError,
  );
  const aiVoiceAvailable = ttsSettings.aiVoiceAvailable;
  const translationVoiceEngine = resolveTranslationVoiceEngine(translationVoiceChoice, aiVoiceAvailable);
  const aiVoiceUnavailableReason = ttsSettings.aiVoiceUnavailableReason;
  const playbackOptions = () => ({
    surah,
    ayah,
    ayahNumbers: ayahs.map((item) => numberOf(item, 0)).filter((number) => number > 0),
    audioByAyah,
    mode: playbackMode,
    language: playbackLanguage,
    translationVoiceEngine,
    speed: playbackSpeed,
  });
  const listenToAyah = () => {
    const controller = playbackControllerRef.current;
    if (!controller) {
      setPlaybackStatus('ระบบเล่นเสียงยังไม่พร้อม กรุณาลองอีกครั้ง');
      return;
    }
    void controller.startSingle(playbackOptions());
  };
  const startAutoPlayback = () => {
    const controller = playbackControllerRef.current;
    if (!controller) {
      setPlaybackStatus('ระบบเล่นเสียงยังไม่พร้อม กรุณาลองอีกครั้ง');
      return;
    }
    setSearch('');
    void controller.startAuto(playbackOptions());
  };
  const stopPlayback = () => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
  };
  const changePlaybackMode = (mode: ReaderAudioMode) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    setPlaybackMode(mode);
  };
  const changePlaybackLanguage = (language: ReaderAudioLanguage) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    setPlaybackLanguage(language);
  };
  const changeTranslationVoiceEngine = (engine: ReaderTranslationVoiceEngine) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    setTranslationVoiceEngine(engine);
  };
  const changePlaybackSpeed = (speed: ReaderAudioSpeed) => {
    if (playbackState !== 'idle') playbackControllerRef.current?.stop();
    setPlaybackSpeed(speed);
  };
  const translationVoiceUnavailable = playbackMode !== 'recitation'
    && translationVoiceEngine === 'ai'
    && !aiVoiceAvailable;
  const playbackControls = (children: React.ReactNode) => (
    <ReaderAudioControls
      mode={playbackMode}
      language={playbackLanguage}
      playbackState={playbackState}
      settingsOpen={playbackSettingsOpen}
      onSettingsOpenChange={setPlaybackSettingsOpen}
      translationVoiceEngine={translationVoiceEngine}
      speed={playbackSpeed}
      aiVoiceAvailable={aiVoiceAvailable}
      aiVoiceUnavailableReason={aiVoiceUnavailableReason}
      status={translationVoiceUnavailable
        ? aiVoiceUnavailableReason
        : playbackStatus === 'พร้อมเล่นเสียง' && audioError
          ? `ยังโหลดเสียงอ่านไม่ได้: ${audioError}`
          : playbackStatus}
      listenDisabled={translationVoiceUnavailable || (playbackMode !== 'translation' && !audioUrl)}
      autoDisabled={translationVoiceUnavailable || ((playbackMode !== 'translation' && !audioUrl) || ayahs.length === 0)}
      onModeChange={changePlaybackMode}
      onLanguageChange={changePlaybackLanguage}
      onTranslationVoiceEngineChange={changeTranslationVoiceEngine}
      onSpeedChange={changePlaybackSpeed}
      onListen={listenToAyah}
      onAuto={startAutoPlayback}
      onStop={stopPlayback}
    >
      {children}
    </ReaderAudioControls>
  );
  const selectAgent = (agentId: string) => {
    setAgent(agentId);
    void activateTafsir(surah, ayah, agentId);
  };
  const tafsirSource = isRecord(tafsir?.source) ? tafsir.source : null;
  const tafsirLanguage = stringOf(tafsirSource, 'language_name').toLowerCase();
  const isArabicTafsir = tafsirLanguage.includes('arab');
  const hasThaiTranslation = typeof tafsir?.thai_translation === 'string' && tafsir.thai_translation.length > 0;
  const thaiTafsirParagraphs = translationParagraphs(stringOf(tafsir, 'thai_translation'));
  const selectedArabic = textOf(ayahs.find((item) => numberOf(item, 0) === ayah));
  const audioUrl = audioByAyah[ayah] ?? '';
  const tafsirApproved = tafsir?.translation_allowed === true;
  const openAiExplanation = () => {
    setDialogueMode('explain');
    setCenterView('dialogue');
    setMobileView('dialogue');
  };
  const updateDialogueMessage = (id: string, update: Partial<DialogueMessage>) => {
    setDialogueMessages((messages) => messages.map((message) => (
      message.id === id ? { ...message, ...update } : message
    )));
  };
  const askQuestions = async (prompts: string[]) => {
    const normalizedPrompts = prompts.map((prompt) => prompt.trim()).filter(Boolean);
    if (normalizedPrompts.length === 0 || normalizedPrompts.length > 4) return;

    const contextKey = chatContextKey;
    const contextEpoch = chatSessionRef.current.epoch;
    const sessionId = chatSessionRef.current.sessionId ?? createUuid();
    chatSessionRef.current.sessionId = sessionId;
    const messageId = createUuid();
    const question = normalizedPrompts.length === 1
      ? normalizedPrompts[0]
      : normalizedPrompts.map((prompt, index) => `${index + 1}. ${prompt}`).join('\n');
    const isBatch = normalizedPrompts.length > 1;
    const pendingMessage: DialogueMessage = {
      id: messageId,
      contextKey,
      question,
      status: 'loading',
      suggestions: [],
      suggestionsStatus: 'success',
    };
    setDialogueMessages((messages) => [...messages, pendingMessage]);

    try {
      const answer = await apiClient.getAgentExplanation(
        surah,
        ayah,
        agent,
        question,
        {
          sessionId,
          ...(isBatch ? { subquestions: normalizedPrompts } : {}),
        },
      );
      if (chatSessionRef.current.epoch !== contextEpoch) return;

      const responseSessionId = answer.data.session_id ?? sessionId;
      const responseMessageId = answer.data.message_id ?? undefined;
      chatSessionRef.current.sessionId = responseSessionId;
      const canLoadSuggestions = Boolean(responseMessageId && answer.data.followups_available);
      updateDialogueMessage(messageId, {
        answer,
        sessionId: responseSessionId,
        messageId: responseMessageId,
        status: 'success',
        suggestionsStatus: canLoadSuggestions ? 'loading' : 'success',
      });
      if (!canLoadSuggestions || !responseMessageId) return;

      try {
        const result = await apiClient.getChatSuggestions(responseSessionId, responseMessageId);
        if (chatSessionRef.current.epoch !== contextEpoch) return;
        updateDialogueMessage(messageId, {
          suggestions: result.suggestions.slice(0, 4),
          suggestionsStatus: 'success',
        });
      } catch {
        if (chatSessionRef.current.epoch !== contextEpoch) return;
        updateDialogueMessage(messageId, { suggestionsStatus: 'error' });
      }
    } catch (failure: unknown) {
      if (chatSessionRef.current.epoch !== contextEpoch) return;
      updateDialogueMessage(messageId, {
        error: failure instanceof Error ? failure.message : 'ยังสร้างคำตอบที่อ้างอิงหลักฐานไม่ได้',
        status: 'error',
        suggestionsStatus: 'error',
      });
    }
  };
  const refreshSuggestions = async (message: DialogueMessage) => {
    if (
      !message.sessionId
      || !message.messageId
      || message.contextKey !== chatContextKey
    ) return;
    const contextEpoch = chatSessionRef.current.epoch;
    updateDialogueMessage(message.id, { suggestionsStatus: 'loading' });
    try {
      const result = await apiClient.getChatSuggestions(message.sessionId, message.messageId);
      if (chatSessionRef.current.epoch !== contextEpoch) return;
      updateDialogueMessage(message.id, {
        suggestions: result.suggestions.slice(0, 4),
        suggestionsStatus: 'success',
      });
    } catch {
      if (chatSessionRef.current.epoch !== contextEpoch) return;
      updateDialogueMessage(message.id, { suggestionsStatus: 'error' });
    }
  };
  const submitQuestion = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = questionDraft.trim();
    if (question) {
      setQuestionDraft('');
      void askQuestions([question]);
    }
  };
  const visiblePanelLayout = useMemo<number[]>(() => {
    const sourceSize = panelLayout.sources ?? 24;
    const readerSize = panelLayout.reader ?? 49;
    const studioSize = panelLayout.studio ?? 27;
    if (sourcesOpen && studioOpen) {
      return [sourceSize, readerSize, studioSize];
    }
    if (sourcesOpen) {
      const total = sourceSize + readerSize;
      return [(sourceSize / total) * 100, (readerSize / total) * 100];
    }
    if (studioOpen) {
      const total = readerSize + studioSize;
      return [(readerSize / total) * 100, (studioSize / total) * 100];
    }
    return [100];
  }, [panelLayout, sourcesOpen, studioOpen]);
  const studyContext: StudyContext = {
    surah_number: surah,
    ayah_number: ayah,
    surah_name: surahName,
    arabic_text: selectedArabic,
    translation: translationsByAyah[ayah] ?? '',
    tafsir_text: tafsirApproved ? stringOf(tafsir, 'arabic_text') : '',
    tafsir_approved: tafsirApproved,
    tafsir_source: stringOf(tafsirSource, 'title') || '',
    tafsir_book_id: tafsirSource && typeof tafsirSource.book_id === 'string' ? tafsirSource.book_id : null,
  };
  const saveNote = async (title: string, content: string, noteContext: StudyContext) => {
    const { data } = await apiClient.createNote({
      title,
      content,
      surah_number: noteContext.surah_number,
      ayah_number: noteContext.ayah_number,
      source_label: noteContext.tafsir_approved ? noteContext.tafsir_source : 'อัลกุรอาน',
    });
    queryClient.setQueryData<DataRecord[]>(['workspace', 'notes'], (notes = []) => [data, ...notes]);
  };
  const saveStudioArtifactNote = async (artifact: TargetStudioArtifactData, noteContext: StudyContext) => {
    const quranSource = artifact.sources.find((source) => source.id === 'quran');
    if (!quranSource) throw new Error('Studio artifact is missing its Quran citation');
    const quranReference = quranSource.label.match(/^Quran (\d+:\d+)$/)?.[1];
    if (quranReference !== `${noteContext.surah_number}:${noteContext.ayah_number}`) {
      throw new Error('Studio artifact Quran citation does not match the selected ayah');
    }
    const tafsirSource = artifact.sources.find((source) => source.id.startsWith('tafsir-'));
    const sourceLabel = `Quran ${noteContext.surah_name} ${quranReference}`
      + (tafsirSource ? `; ${tafsirSource.label}` : '');
    const { data } = await apiClient.createNote({
      title: artifact.artifact.title,
      content: JSON.stringify(artifact),
      surah_number: noteContext.surah_number,
      ayah_number: noteContext.ayah_number,
      source_label: sourceLabel,
    });
    queryClient.setQueryData<DataRecord[]>(['workspace', 'notes'], (notes = []) => [data, ...notes]);
  };
  const toggleSource = (source: string) => {
    setSelectedSources((current) => current.includes(source)
      ? current.filter((value) => value !== source)
      : [...current, source]);
  };

  const tafsirPanel = (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="mb-4 flex items-center gap-6 border-b border-slate-100 text-sm">
          <button type="button" onClick={() => setDialogueMode('tafsir')} className={`border-b-2 pb-3 ${dialogueMode === 'tafsir' ? 'border-[#C9A227] font-semibold text-[#073B32]' : 'border-transparent text-slate-500'}`}>ตัฟซีร</button>
          <button type="button" onClick={() => setDialogueMode('explain')} className={`border-b-2 pb-3 ${dialogueMode === 'explain' ? 'border-[#C9A227] font-semibold text-[#073B32]' : 'border-transparent text-slate-500'}`}>ถาม AI</button>
          <button type="button" onClick={() => setDialogueMode('compare')} className={`border-b-2 pb-3 ${dialogueMode === 'compare' ? 'border-[#C9A227] font-semibold text-[#073B32]' : 'border-transparent text-slate-500'}`}>เทียบหลักฐาน</button>
          <button disabled title="ยังไม่เปิดใช้งาน" className="cursor-not-allowed pb-3 text-slate-400">ทบทวน</button>
        </div>
        <p className="text-xs text-slate-500">บริบทที่เลือกไว้: {surahName} {surah}:{ayah}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {agents.map((item) => <button key={item.id} onClick={() => selectAgent(item.id)} disabled={!item.available} title={item.available ? undefined : 'ยังไม่มีข้อมูลตัฟซีรชุดนี้ในฐานข้อมูล'} className={`rounded-full border px-3 py-2 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${agent === item.id ? 'border-[#0E5E4F] bg-[#0E5E4F] text-white' : 'border-[#d6e0dc] bg-white text-slate-700 hover:border-[#0E5E4F]'}`}>{item.label}</button>)}
        </div>
        <div className="mt-4 flex items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-slate-800">{stringOf(tafsirSource, 'title') || `${agents.find((item) => item.id === agent)?.label} Tafsir`}</h2>
          {tafsir && <EvidenceBadge status={stringOf(tafsir, 'evidence_status')} />}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {dialogueMode === 'tafsir' && <>
        {tafsirStatus === 'idle' && <div className="rounded-xl border border-slate-200 p-4 text-sm leading-7 text-slate-500">กำลังเตรียมตัฟซีร {agents.find((item) => item.id === agent)?.label}...</div>}
        {tafsirStatus === 'loading' && <div className="animate-pulse rounded-xl border border-slate-200 p-4"><div className="h-3 w-2/3 rounded bg-slate-200" /><div className="mt-4 h-3 rounded bg-slate-100" /><div className="mt-2 h-3 w-4/5 rounded bg-slate-100" /><div className="mt-2 h-3 w-3/5 rounded bg-slate-100" /></div>}
        {tafsirStatus === 'error' && <div className="rounded-xl bg-amber-50 p-4 text-sm leading-7 text-amber-800">{error || 'โหลดตัฟซีรไม่สำเร็จ กรุณาลองใหม่'}</div>}
        {tafsir && tafsirStatus === 'success' && <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs font-bold text-slate-700">{stringOf(tafsirSource, 'scholar')}</h3>
              <span className="text-[10px] text-slate-400">ต้นฉบับจาก Quran Foundation API</span>
            </div>
            <div className="rounded-xl border-l-4 border-[#0E5E4F] bg-[#F5F9F7] px-4 py-4">
              <p className="mb-2 text-[10px] font-bold tracking-wide text-[#0E5E4F]">คำแปลภาษาไทย</p>
              {thaiTafsirParagraphs.length
                ? thaiTafsirParagraphs.map((paragraph, index) => <p key={index} className="whitespace-pre-line text-sm leading-8 text-slate-700 [&+p]:mt-3">{paragraph}</p>)
                : <p className="text-sm leading-8 text-slate-500">ยังไม่มีคำแปลภาษาไทย</p>}
            </div>
            {hasThaiTranslation && <p className="mt-3 border-t border-slate-100 pt-3 text-[10px] leading-5 text-slate-400">แปลด้วย AI เพื่อช่วยในการศึกษา ควรตรวจเทียบกับต้นฉบับ</p>}
            {translationError && <p className="mt-3 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800">{translationError}</p>}
          </div>
          <details className="rounded-xl border border-slate-200 bg-white p-4">
            <summary className="cursor-pointer text-xs font-semibold text-slate-600">
              ดูต้นฉบับ{stringOf(tafsirSource, 'language_name') ? ` · ${stringOf(tafsirSource, 'language_name')}` : ''}
            </summary>
            <p
              dir={isArabicTafsir ? 'rtl' : 'ltr'}
              lang={isArabicTafsir ? 'ar' : 'en'}
              className={`${isArabicTafsir ? `${amiriQuran.className} text-right text-xl leading-[2.1]` : 'text-left text-sm leading-7'} mt-4 whitespace-pre-wrap text-slate-800`}
            >
              {stringOf(tafsir, 'arabic_text')}
            </p>
          </details>
          {tafsirSource && <div className="text-[10px] leading-5 text-slate-400">
            <span>{stringOf(tafsirSource, 'title')}</span>
            {stringOf(tafsirSource, 'edition') && <span> · {stringOf(tafsirSource, 'edition')}</span>}
            {tafsirSource.page != null && <span> · หน้า {String(tafsirSource.page)}</span>}
            {stringOf(tafsirSource, 'url') && <a className="ml-1 underline" href={stringOf(tafsirSource, 'url')} target="_blank" rel="noreferrer">แหล่งที่มา</a>}
          </div>}
        </div>}
        </>}
        {dialogueMode === 'explain' && <div className="space-y-4">
          <form onSubmit={submitQuestion} className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-3 sm:flex-row">
            <label htmlFor="agent-question" className="sr-only">คำถามเกี่ยวกับอายะฮ์</label>
            <input id="agent-question" value={questionDraft} onChange={(event) => setQuestionDraft(event.target.value)}
              maxLength={2000}
              placeholder={`ถามเกี่ยวกับ ${surahName} ${surah}:${ayah}`}
              className="min-w-0 flex-1 rounded-lg border border-surface-200 px-3 py-2 text-sm outline-none focus:border-primary-800" />
            <button type="submit" disabled={!questionDraft.trim()} className="rounded-lg bg-[#0E5E4F] px-4 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">ถาม</button>
          </form>
          {dialogueMessages.filter((message) => message.contextKey === chatContextKey).length === 0
            && <p className="text-xs leading-6 text-surface-600">คำตอบจะถูกสร้างจากแหล่งตัฟซีรที่ผ่านการอนุมัติเท่านั้น และจะแสดงที่มาของทุก citation</p>}
          {dialogueMessages
            .filter((message) => message.contextKey === chatContextKey)
            .map((message) => (
              <div className="space-y-3" key={message.id}>
                <article className="ml-auto max-w-[90%] rounded-xl bg-primary-50 p-3">
                  <p className="text-[11px] font-semibold text-primary-800">คำถามของคุณ</p>
                  <p className="mt-1 whitespace-pre-line text-sm leading-6 text-surface-900">{message.question}</p>
                </article>
                {message.status === 'loading' && (
                  <div aria-label="กำลังสร้างคำตอบ" className="animate-pulse rounded-xl border border-surface-200 bg-white p-4" role="status">
                    <div className="h-3 w-2/3 rounded bg-surface-200" />
                    <div className="mt-4 h-3 rounded bg-surface-100" />
                    <div className="mt-2 h-3 w-4/5 rounded bg-surface-100" />
                  </div>
                )}
                {message.status === 'error' && (
                  <p role="alert" className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-800">
                    {message.error}
                  </p>
                )}
                {message.status === 'success' && message.answer && (
                  <div className="space-y-3">
                    {message.answer.data.sections?.length
                      ? message.answer.data.sections.map((section, index) => (
                        <section
                          aria-label={`คำตอบข้อที่ ${index + 1}`}
                          className="space-y-3 rounded-xl border border-surface-200 bg-surface-50 p-3"
                          key={`${message.id}-section-${index}`}
                        >
                          <h3 className="text-sm font-bold leading-6 text-surface-900">
                            ข้อ {index + 1}: {section.question}
                          </h3>
                          {Object.entries(section.agent_outputs).map(([agentType, output]) => (
                            <AgentAnswerCard
                              agentType={agentType}
                              key={`${message.id}-${index}-${agentType}`}
                              output={output}
                              validation={section.validation?.agent_validations[agentType]}
                            />
                          ))}
                        </section>
                      ))
                      : Object.entries(message.answer.data.agent_outputs).map(([agentType, output]) => (
                        <AgentAnswerCard
                          agentType={agentType}
                          key={`${message.id}-${agentType}`}
                          output={output}
                          validation={message.answer?.data.validation?.agent_validations[agentType]}
                        />
                      ))}
                    <SuggestedFollowUps
                      key={message.id}
                      onAsk={(prompts) => { void askQuestions(prompts); }}
                      onRefresh={() => { void refreshSuggestions(message); }}
                      status={message.suggestionsStatus}
                      suggestions={message.suggestions}
                    />
                  </div>
                )}
              </div>
            ))}
        </div>}
        {dialogueMode === 'compare' && <div className="space-y-3">
          <p className="text-xs leading-6 text-slate-500">แสดงความเห็นต่างได้เมื่อมีข้ออ้างจากนักวิชาการหลายท่านพร้อม citation ที่ตรวจสอบย้อนกลับได้ ระบบจะไม่อนุมานความเห็นต่างจากชื่อสำนักหรือข้อความที่ยังไม่มีหลักฐาน</p>
          {comparisonQuery.isFetching && <div className="animate-pulse rounded-xl border border-slate-200 bg-white p-4"><div className="h-3 w-2/3 rounded bg-slate-200" /><div className="mt-4 h-3 rounded bg-slate-100" /></div>}
          {comparisonQuery.isError && <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800">{comparisonQuery.error instanceof Error ? comparisonQuery.error.message : 'ยังไม่มีการเปรียบเทียบที่มีหลักฐานเพียงพอ'}</p>}
          {!comparisonQuery.isFetching && !comparisonQuery.isError && !comparisonQuery.data && <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-500">ยังไม่มีข้อมูลเปรียบเทียบที่ผ่านการตรวจสอบสำหรับอายะฮ์นี้</p>}
        </div>}
      </div>
      {tafsirStatus === 'error' && <div className="border-t border-slate-100 p-4">
        <button onClick={() => void activateTafsir(surah, ayah, agent)} className="w-full rounded-xl bg-[#0E5E4F] px-4 py-3 text-sm font-semibold text-white hover:bg-[#073B32]">ลองโหลดตัฟซีรอีกครั้ง</button>
      </div>}
    </div>
  );

  const renderReaderCanvas = () => (
    <section className="min-h-0 overflow-y-auto px-4 pb-8 pt-5 md:px-8 lg:px-6 lg:pt-7 xl:px-9">
      <style>{qpcFontPages.map((page) => `@font-face{font-family:"QpcV4Page${page}";src:url("https://static-cdn.tarteel.ai/qul/fonts/quran_fonts/v4/woff2/p${page}.woff2") format("woff2");font-display:swap}`).join('\n')}</style>
      <div className="mx-auto max-w-4xl">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div><h1 className="text-xl font-bold text-[#073B32] md:text-2xl">{surahName}</h1><p className="mt-1 text-sm text-slate-500">{surahName} · {safeAyahCount || '—'} อายะฮ์</p></div>
        </div>
        <div className="mb-4 rounded-2xl border border-[#dce4e1] bg-white p-4 shadow-[0_6px_20px_rgba(21,44,37,.04)]">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-sm font-bold text-[#073B32]">อายะฮ์ {ayah}</h2>
              <p className="mt-1 text-[10px] text-slate-500">จากทั้งหมด {safeAyahCount || '—'} อายะฮ์</p>
            </div>
            <div className="flex shrink-0 items-center gap-1 rounded-xl border border-slate-200 bg-[#F8FAF9] p-1" aria-label="ปรับขนาดอักษรอาหรับ">
              <button type="button" aria-label="ลดขนาดอักษรอาหรับ" disabled={arabicFontSize <= 28} onClick={() => setArabicFontSize((size) => Math.max(size - 4, 28))} className="grid h-8 w-8 place-items-center rounded-lg text-xs font-semibold text-slate-600 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40">A−</button>
              <span className="min-w-8 text-center text-[10px] tabular-nums text-slate-400">{arabicFontSize}</span>
              <button type="button" aria-label="เพิ่มขนาดอักษรอาหรับ" disabled={arabicFontSize >= 52} onClick={() => setArabicFontSize((size) => Math.min(size + 4, 52))} className="grid h-8 w-8 place-items-center rounded-lg text-xs font-semibold text-slate-600 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40">A+</button>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <button type="button" aria-label="อายะฮ์ก่อนหน้า" disabled={ayah <= 1} onClick={() => selectAyah(ayah - 1)} className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[#d6e0dc] text-lg text-[#0E5E4F] transition hover:bg-[#E6F4F1] disabled:cursor-not-allowed disabled:opacity-40">‹</button>
            <div className="min-w-0 flex-1">
              <div className="mb-1.5 flex items-center justify-between text-[10px] font-medium text-slate-500">
                <span>ตำแหน่งที่อ่าน</span>
                <span className="tabular-nums">{ayah} / {safeAyahCount || '—'}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-[#E6F4F1]" role="progressbar" aria-label="ความคืบหน้าในซูเราะฮ์" aria-valuemin={0} aria-valuemax={safeAyahCount || undefined} aria-valuenow={ayah}>
                <div className="h-full rounded-full bg-[#0E5E4F] transition-[width]" style={{ width: `${readingProgress}%` }} />
              </div>
            </div>
            <button type="button" aria-label="อายะฮ์ถัดไป" disabled={Boolean(safeAyahCount && ayah >= safeAyahCount)} onClick={() => selectAyah(ayah + 1)} className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[#d6e0dc] text-lg text-[#0E5E4F] transition hover:bg-[#E6F4F1] disabled:cursor-not-allowed disabled:opacity-40">›</button>
          </div>
        </div>
        <label className="mb-4 flex items-center gap-3 rounded-xl border border-[#d6e0dc] bg-white px-4 py-3 text-slate-500 md:hidden">
          <Icon name="search" className="h-4 w-4 shrink-0" />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ค้นหาอายะฮ์ หรือคำสำคัญ" className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500" />
        </label>

        {contentStatus === 'loading' && <div role="status" aria-label="กำลังโหลดอายะฮ์" aria-busy="true" className="space-y-4"><div className="h-48 animate-pulse rounded-2xl bg-slate-200" /><div className="h-48 animate-pulse rounded-2xl bg-slate-200" /></div>}
        {contentStatus === 'error' && <div role="alert" className="rounded-2xl border border-amber-200 bg-white p-6 text-center shadow-[0_6px_20px_rgba(21,44,37,.04)]"><span className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-amber-50 text-lg text-amber-700" aria-hidden="true">!</span><h2 className="mt-3 text-sm font-bold text-slate-800">ยังโหลดอายะฮ์ไม่ได้</h2><p className="mt-2 text-xs leading-6 text-slate-500">{error || 'ตรวจสอบการเชื่อมต่อ API แล้วลองใหม่'}</p><button onClick={() => setContentRequestVersion((version) => version + 1)} className="mt-4 rounded-xl bg-[#0E5E4F] px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-[#073B32]">ลองโหลดอีกครั้ง</button></div>}
        {contentStatus === 'empty' && <div role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500"><span className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-full bg-[#F5F7F6] text-[#0E5E4F]" aria-hidden="true"><Icon name="book" className="h-5 w-5" /></span><p className="font-medium text-slate-700">ไม่พบข้อมูลอายะฮ์นี้</p><p className="mt-1 text-xs text-slate-500">ลองเลือกซูเราะฮ์อื่นจากแผง Sources</p></div>}
        {contentStatus === 'success' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1 text-[10px] text-slate-400">
              <span>{search.trim() ? `พบ ${filteredAyahs.length} อายะฮ์` : 'ข้อความอัลกุรอาน · QPC v4'}</span>
              <span>แสดง {filteredAyahs.length} จาก {ayahs.length}</span>
            </div>
            {filteredAyahs.map((item) => {
              const id = numberOf(item, 0);
              const selected = id === ayah;
              const verse = selected ? selectedArabic : textOf(item);
              const verseTranslation = translationsByAyah[id] ?? '';
              return <article key={id} data-reader-ayah={id} className={`reader-ayah-card space-y-2 ${selected && playbackSettingsOpen ? 'reader-ayah-card-settings-open' : ''}`}>
                <button type="button" aria-current={selected ? 'location' : undefined} onClick={() => selectAyah(id)} className={`group block w-full rounded-2xl border p-5 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0E5E4F]/30 md:p-6 ${selected ? 'border-2 border-[#0E5E4F] bg-[#E6F4F1] shadow-[0_8px_24px_rgba(14,94,79,.08)]' : 'border-[#dce4e1] bg-white hover:border-[#9bbdb3] hover:bg-[#fbfdfc]'}`}>
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-500"><span className={`grid h-8 min-w-8 place-items-center rounded-full px-2 tabular-nums ${selected ? 'bg-[#0E5E4F] text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-[#E6F4F1] group-hover:text-[#0E5E4F]'}`}>{id}</span>{selected && <span className="rounded-full bg-white/80 px-2.5 py-1 text-[10px] text-[#0E5E4F]">อายะฮ์ที่เลือก</span>}</div>
                  <p className={`${amiriQuran.className} mt-5 text-right leading-[2.1] text-slate-900`} style={{ fontSize: `${arabicFontSize}px`, fontFamily: `QpcV4Page${item.page_number}, ${amiriQuran.style.fontFamily}` }} dir="rtl" lang="ar">{verse || 'ไม่มีข้อความอาหรับจากแหล่งข้อมูล'}</p>
                  {verseTranslation
                    ? <span className="mt-4 block rounded-xl border-l-2 border-[#0E5E4F]/40 bg-white/70 px-3 py-3 text-left">
                      <span className="mb-1 block text-[10px] font-semibold text-[#0E5E4F]">คำแปลไทย</span>
                      <span className="block whitespace-pre-line text-sm leading-7 text-slate-700">{verseTranslation}</span>
                    </span>
                    : <p className={`mt-4 border-t pt-4 text-xs leading-6 ${ayahTranslationError ? 'border-amber-200 text-amber-700' : 'border-[#0E5E4F]/10 text-slate-400'}`}>{translationStatus === 'loading' ? 'กำลังโหลดคำแปลภาษาไทย...' : ayahTranslationError ? `ยังโหลดคำแปลภาษาไทยไม่ได้: ${ayahTranslationError}` : 'ไม่มีคำแปลภาษาไทยสำหรับอายะฮ์นี้'}</p>}
                </button>
                {selected && playbackControls(
                  <>
                    <button type="button" data-reader-action="save" onClick={() => { void saveNote(`${surahName} ${surah}:${ayah}`, [selectedArabic, translationsByAyah[ayah] ?? ''].filter(Boolean).join('\n\n'), studyContext).catch((failure: unknown) => setError(failure instanceof Error ? failure.message : 'บันทึกโน้ตไม่สำเร็จ')); }} className="reader-action-button reader-action-secondary">
                      <Bookmark aria-hidden="true" size={18} />
                      <span>บันทึกลงโน้ต</span>
                    </button>
                    <button type="button" data-reader-action="ask" onClick={() => { setCenterView('dialogue'); setMobileView('dialogue'); }} className="reader-action-button reader-action-secondary">
                      <Sparkles aria-hidden="true" size={18} />
                      <span>ถาม AI</span>
                    </button>
                  </>,
                )}
              </article>;
            })}
            {filteredAyahs.length === 0 && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">ไม่พบอายะฮ์ที่ตรงกับคำค้น</p>}
          </div>
        )}
      </div>
    </section>
  );

  return (
    <main className={`${notoSansThai.className} flex h-dvh flex-col overflow-hidden bg-[#F5F7F6] text-[#1E293B]`}>
      <audio ref={audioRef} preload="none" className="sr-only" aria-hidden="true" data-testid="reader-playback-audio" />
      <header className="z-20 flex h-[68px] shrink-0 items-center justify-between gap-4 border-b border-[#dce4e1] bg-white px-4 lg:h-[76px] lg:px-7">
        <div className="flex min-w-0 items-center gap-3 lg:min-w-[190px]">
          <button type="button" aria-label="เปิดเมนูซูเราะฮ์" aria-expanded={mobileSurahMenuOpen} aria-controls="mobile-surah-menu" onClick={() => setMobileSurahMenuOpen(true)} className="rounded-lg p-2 text-[#073B32] hover:bg-slate-50 lg:hidden"><Icon name="menu" /></button>
          <button onClick={() => router.push('/')} className="hidden items-center gap-2.5 font-bold tracking-tight text-[#073B32] lg:flex"><BrandMark />QURAN AI</button>
          <div className="text-center lg:hidden"><p className="text-sm font-bold text-[#073B32]">{surahName}</p><p className="text-[10px] text-slate-500">อายะฮ์ {ayah} · {safeAyahCount || '—'} อายะฮ์</p></div>
        </div>
        <label className="hidden max-w-xl flex-1 items-center gap-3 rounded-xl border border-[#cbd9d4] bg-[#F5F7F6] px-4 py-2.5 text-slate-500 md:flex">
          <Icon name="search" className="h-4 w-4 shrink-0" />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ค้นหาอายะฮ์ เช่น 2:255 หรือคำสำคัญ" className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500" />
        </label>
        <div className="flex min-w-0 items-center justify-end gap-2 sm:min-w-[190px]">
          <div className="hidden items-center gap-1 lg:flex">
            <button type="button" onClick={() => setSourcesOpen((open) => !open)} aria-label={sourcesOpen ? 'ย่อแผง Sources' : 'เปิดแผง Sources'} title="Sources · ["
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">{sourcesOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}</button>
            <button type="button" onClick={() => setStudioOpen((open) => !open)} aria-label={studioOpen ? 'ย่อแผง Studio' : 'เปิดแผง Studio'} title="Studio · ]"
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">{studioOpen ? <PanelRightClose size={17} /> : <PanelRightOpen size={17} />}</button>
          </div>
          <span className="hidden items-center rounded-full border border-[#efdfaa] bg-[#FEF9E7] px-4 py-2 text-xs font-semibold text-[#80640e] sm:inline-flex">สตรีค [N] วัน</span>
          <button aria-label="โปรไฟล์" className="grid h-10 w-10 place-items-center rounded-full bg-[#E6F4F1] text-sm font-bold text-[#0E5E4F]">ผ</button>
        </div>
      </header>

      <div className="hidden min-h-0 flex-1 lg:flex">
        <PanelGroup key={`${sourcesOpen}-${studioOpen}`} direction="horizontal"
          onLayout={(sizes) => setPanelLayout((current) => ({
            ...current,
            ...(sourcesOpen ? { sources: sizes[0] } : {}),
            reader: sizes[sourcesOpen ? 1 : 0],
            ...(studioOpen ? { studio: sizes[sizes.length - 1] } : {}),
          }))}
          className="min-h-0 flex-1">
        {sourcesOpen && <Panel id="sources" defaultSize={visiblePanelLayout[0]} minSize={18} maxSize={34} className="min-w-0 overflow-hidden border-r border-[#dce4e1]">
          <SourcesPanel surahs={surahs} surah={surah} onSelectSurah={selectSurah} selectedSources={selectedSources}
            onToggleSource={toggleSource} tafsirApproved={tafsirApproved} context={studyContext} />
        </Panel>}
        {sourcesOpen && <PanelResizeHandle className="w-1.5 bg-slate-100 transition hover:bg-[#0E5E4F]/30" />}

        <Panel id="reader" defaultSize={visiblePanelLayout[sourcesOpen ? 1 : 0]} minSize={34} className="min-w-0 overflow-hidden bg-[#F5F7F6]">
          <div className="flex h-full min-h-0 flex-col">
            <div className="flex shrink-0 items-center gap-1 border-b border-[#dce4e1] bg-white px-5 pt-2">
              <button type="button" onClick={() => setCenterView('reader')} className={`border-b-2 px-3 py-2 text-xs font-semibold ${centerView === 'reader' ? 'border-[#C9A227] text-[#073B32]' : 'border-transparent text-slate-400'}`}>Reader</button>
              <button type="button" onClick={() => setCenterView('dialogue')} className={`border-b-2 px-3 py-2 text-xs font-semibold ${centerView === 'dialogue' ? 'border-[#C9A227] text-[#073B32]' : 'border-transparent text-slate-400'}`}>Grounded dialogue</button>
              <span className="ml-auto hidden items-center gap-1 text-[9px] text-slate-400 xl:flex"><Sparkles size={12} /> AI-SYNTHESIS จะแยกจากหลักฐานต้นฉบับ</span>
            </div>
            {centerView === 'reader' ? (
        <section className="min-h-0 overflow-y-auto px-4 pb-10 pt-5 md:px-8 lg:px-6 lg:pt-7 xl:px-9">
          <style>{qpcFontPages.map((page) => `@font-face{font-family:"QpcV4Page${page}";src:url("https://static-cdn.tarteel.ai/qul/fonts/quran_fonts/v4/woff2/p${page}.woff2") format("woff2");font-display:swap}`).join('\n')}</style>
          <div className="mx-auto max-w-4xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div><h1 className="text-xl font-bold text-[#073B32] md:text-2xl">{surahName}</h1><p className="mt-1 text-sm text-slate-500">{surahName} · {safeAyahCount || '—'} อายะฮ์</p></div>
            </div>
            <div className="mb-4 rounded-2xl border border-[#dce4e1] bg-white p-4 shadow-[0_6px_20px_rgba(21,44,37,.04)]">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-bold text-[#073B32]">อายะฮ์ {ayah}</h2>
                  <p className="mt-1 text-[10px] text-slate-500">จากทั้งหมด {safeAyahCount || '—'} อายะฮ์</p>
                </div>
                <div className="flex shrink-0 items-center gap-1 rounded-xl border border-slate-200 bg-[#F8FAF9] p-1" aria-label="ปรับขนาดอักษรอาหรับ">
                  <button type="button" aria-label="ลดขนาดอักษรอาหรับ" disabled={arabicFontSize <= 28} onClick={() => setArabicFontSize((size) => Math.max(size - 4, 28))} className="grid h-8 w-8 place-items-center rounded-lg text-xs font-semibold text-slate-600 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40">A−</button>
                  <span className="min-w-8 text-center text-[10px] tabular-nums text-slate-400">{arabicFontSize}</span>
                  <button type="button" aria-label="เพิ่มขนาดอักษรอาหรับ" disabled={arabicFontSize >= 52} onClick={() => setArabicFontSize((size) => Math.min(size + 4, 52))} className="grid h-8 w-8 place-items-center rounded-lg text-xs font-semibold text-slate-600 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40">A+</button>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <button type="button" aria-label="อายะฮ์ก่อนหน้า" disabled={ayah <= 1} onClick={() => selectAyah(ayah - 1)} className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[#d6e0dc] text-lg text-[#0E5E4F] transition hover:bg-[#E6F4F1] disabled:cursor-not-allowed disabled:opacity-40">‹</button>
                <div className="min-w-0 flex-1">
                  <div className="mb-1.5 flex items-center justify-between text-[10px] font-medium text-slate-500">
                    <span>ตำแหน่งที่อ่าน</span>
                    <span className="tabular-nums">{ayah} / {safeAyahCount || '—'}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-[#E6F4F1]" role="progressbar" aria-label="ความคืบหน้าในซูเราะฮ์" aria-valuemin={0} aria-valuemax={safeAyahCount || undefined} aria-valuenow={ayah}>
                    <div className="h-full rounded-full bg-[#0E5E4F] transition-[width]" style={{ width: `${readingProgress}%` }} />
                  </div>
                </div>
                <button type="button" aria-label="อายะฮ์ถัดไป" disabled={Boolean(safeAyahCount && ayah >= safeAyahCount)} onClick={() => selectAyah(ayah + 1)} className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[#d6e0dc] text-lg text-[#0E5E4F] transition hover:bg-[#E6F4F1] disabled:cursor-not-allowed disabled:opacity-40">›</button>
              </div>
            </div>
            <label className="mb-4 flex items-center gap-3 rounded-xl border border-[#d6e0dc] bg-white px-4 py-3 text-slate-500 md:hidden">
              <Icon name="search" className="h-4 w-4 shrink-0" />
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ค้นหาอายะฮ์ หรือคำสำคัญ" className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500" />
            </label>

            {contentStatus === 'loading' && <div role="status" aria-label="กำลังโหลดอายะฮ์" aria-busy="true" className="space-y-4"><div className="h-48 animate-pulse rounded-2xl bg-slate-200" /><div className="h-48 animate-pulse rounded-2xl bg-slate-200" /></div>}
            {contentStatus === 'error' && <div role="alert" className="rounded-2xl border border-amber-200 bg-white p-6 text-center shadow-[0_6px_20px_rgba(21,44,37,.04)]"><span className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-amber-50 text-lg text-amber-700" aria-hidden="true">!</span><h2 className="mt-3 text-sm font-bold text-slate-800">ยังโหลดอายะฮ์ไม่ได้</h2><p className="mt-2 text-xs leading-6 text-slate-500">{error || 'ตรวจสอบการเชื่อมต่อ API แล้วลองใหม่'}</p><button onClick={() => setContentRequestVersion((version) => version + 1)} className="mt-4 rounded-xl bg-[#0E5E4F] px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-[#073B32]">ลองโหลดอีกครั้ง</button></div>}
            {contentStatus === 'empty' && <div role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500"><span className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-full bg-[#F5F7F6] text-[#0E5E4F]" aria-hidden="true"><Icon name="book" className="h-5 w-5" /></span><p className="font-medium text-slate-700">ไม่พบข้อมูลอายะฮ์นี้</p><p className="mt-1 text-xs text-slate-500">ลองเลือกซูเราะฮ์อื่นจากแผง Sources</p></div>}
            {contentStatus === 'success' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between px-1 text-[10px] text-slate-400">
                  <span>{search.trim() ? `พบ ${filteredAyahs.length} อายะฮ์` : 'ข้อความอัลกุรอาน · QPC v4'}</span>
                  <span>แสดง {filteredAyahs.length} จาก {ayahs.length}</span>
                </div>
                {filteredAyahs.map((item) => {
                  const id = numberOf(item, 0);
                  const selected = id === ayah;
                  const verse = selected ? selectedArabic : textOf(item);
                  const verseTranslation = translationsByAyah[id] ?? '';
                  return <article key={id} data-reader-ayah={id} className={`reader-ayah-card space-y-2 ${selected && playbackSettingsOpen ? 'reader-ayah-card-settings-open' : ''}`}>
                    <button type="button" aria-current={selected ? 'location' : undefined} onClick={() => selectAyah(id)} className={`group block w-full rounded-2xl border p-5 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0E5E4F]/30 md:p-6 ${selected ? 'border-2 border-[#0E5E4F] bg-[#E6F4F1] shadow-[0_8px_24px_rgba(14,94,79,.08)]' : 'border-[#dce4e1] bg-white hover:border-[#9bbdb3] hover:bg-[#fbfdfc]'}`}>
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-500"><span className={`grid h-8 min-w-8 place-items-center rounded-full px-2 tabular-nums ${selected ? 'bg-[#0E5E4F] text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-[#E6F4F1] group-hover:text-[#0E5E4F]'}`}>{id}</span>{selected && <span className="rounded-full bg-white/80 px-2.5 py-1 text-[10px] text-[#0E5E4F]">อายะฮ์ที่เลือก</span>}</div>
                      <p className={`${amiriQuran.className} mt-5 text-right leading-[2.1] text-slate-900`} style={{ fontSize: `${arabicFontSize}px`, fontFamily: `QpcV4Page${item.page_number}, ${amiriQuran.style.fontFamily}` }} dir="rtl" lang="ar">{verse || 'ไม่มีข้อความอาหรับจากแหล่งข้อมูล'}</p>
                      {verseTranslation
                        ? <span className="mt-4 block rounded-xl border-l-2 border-[#0E5E4F]/40 bg-white/70 px-3 py-3 text-left">
                          <span className="mb-1 block text-[10px] font-semibold text-[#0E5E4F]">คำแปลไทย</span>
                          <span className="block whitespace-pre-line text-sm leading-7 text-slate-700">{verseTranslation}</span>
                        </span>
                        : <p className={`mt-4 border-t pt-4 text-xs leading-6 ${ayahTranslationError ? 'border-amber-200 text-amber-700' : 'border-[#0E5E4F]/10 text-slate-400'}`}>{translationStatus === 'loading' ? 'กำลังโหลดคำแปลภาษาไทย...' : ayahTranslationError ? `ยังโหลดคำแปลภาษาไทยไม่ได้: ${ayahTranslationError}` : 'ไม่มีคำแปลภาษาไทยสำหรับอายะฮ์นี้'}</p>}
                    </button>
                    {selected && playbackControls(
                      <>
                        <button type="button" data-reader-action="save" onClick={() => { void saveNote(`${surahName} ${surah}:${ayah}`, [selectedArabic, translationsByAyah[ayah] ?? ''].filter(Boolean).join('\n\n'), studyContext).catch((failure: unknown) => setError(failure instanceof Error ? failure.message : 'บันทึกโน้ตไม่สำเร็จ')); }} className="reader-action-button reader-action-secondary">
                          <Bookmark aria-hidden="true" size={18} />
                          <span>บันทึกลงโน้ต</span>
                        </button>
                        <button type="button" data-reader-action="ask" onClick={openAiExplanation} className="reader-action-button reader-action-secondary">
                          <Sparkles aria-hidden="true" size={18} />
                          <span>ถาม AI</span>
                        </button>
                      </>,
                    )}
                  </article>;
                })}
                {filteredAyahs.length === 0 && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">ไม่พบอายะฮ์ที่ตรงกับคำค้น</p>}
              </div>
            )}
          </div>
        </section>
            ) : <div className="min-h-0 flex-1 overflow-y-auto bg-white">{tafsirPanel}</div>}
          </div>
        </Panel>
        {studioOpen && <PanelResizeHandle className="w-1.5 bg-slate-100 transition hover:bg-[#0E5E4F]/30" />}
        {studioOpen && <Panel id="studio" defaultSize={visiblePanelLayout[visiblePanelLayout.length - 1]} minSize={23} maxSize={40} className="min-w-0 overflow-hidden border-l border-[#dce4e1]">
          <StudioPanel context={studyContext} selectedSources={selectedSources} onSaveArtifact={saveNote} onSaveTargetArtifact={saveStudioArtifactNote} />
        </Panel>}
        </PanelGroup>
      </div>

      <div className="flex min-h-0 flex-1 flex-col lg:hidden">
        <WorkspaceMobileTabs activeView={mobileView} onSelect={setMobileView} />
        <div data-testid="mobile-view-content" className="min-h-0 flex-1 overflow-y-auto">
          {mobileView === 'reader' && renderReaderCanvas()}
          {mobileView === 'sources' && <SourcesPanel surahs={surahs} surah={surah} onSelectSurah={selectSurah} selectedSources={selectedSources}
            onToggleSource={toggleSource} tafsirApproved={tafsirApproved} context={studyContext} />}
          {mobileView === 'dialogue' && tafsirPanel}
          {mobileView === 'studio' && <StudioPanel context={studyContext} selectedSources={selectedSources} onSaveArtifact={saveNote} onSaveTargetArtifact={saveStudioArtifactNote} />}
        </div>
      </div>

      {mobileSurahMenuOpen && <div className="fixed inset-0 z-40 lg:hidden">
        <button type="button" aria-label="ปิดเมนูซูเราะฮ์" onClick={() => setMobileSurahMenuOpen(false)} className="absolute inset-0 bg-slate-950/30" />
        <aside id="mobile-surah-menu" aria-label="เมนูและสารบัญอัลกุรอาน" className="absolute inset-y-0 left-0 flex w-[min(88vw,360px)] flex-col bg-white shadow-2xl">
          <div className="flex h-[68px] shrink-0 items-center justify-between border-b border-slate-200 px-5">
            <div><p className="text-sm font-bold text-[#073B32]">เมนูหลัก</p><p className="text-[10px] text-slate-500">สารบัญอัลกุรอาน · 114 ซูเราะฮ์</p></div>
            <button type="button" aria-label="ปิดเมนูซูเราะฮ์" onClick={() => setMobileSurahMenuOpen(false)} className="grid h-9 w-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100">×</button>
          </div>
          <nav aria-label="สารบัญซูเราะฮ์" className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3 [scrollbar-width:thin]">
            {surahStatus === 'loading' && <p className="px-3 py-2 text-sm text-slate-400">กำลังโหลดสารบัญ...</p>}
            {surahStatus === 'error' && <p className="px-3 py-2 text-sm text-red-600">โหลดสารบัญไม่สำเร็จ</p>}
            {surahs.map((item) => {
              const id = numberOf(item, 0);
              const name = stringOf(item, 'name_th', 'name_simple', 'transliteration', 'name') || 'ไม่ทราบชื่อ';
              return <button type="button" key={id} onClick={() => selectSurah(id)} aria-current={id === surah ? 'page' : undefined} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${id === surah ? 'bg-[#E6F4F1] font-semibold text-[#073B32]' : 'text-slate-700 hover:bg-slate-50'}`}><span className="w-7 shrink-0 text-right text-xs tabular-nums text-slate-400">{id}</span><span>{name}</span></button>;
            })}
          </nav>
          <div className="shrink-0 border-t border-slate-200 p-3">
            <p className="mb-1 px-3 text-[10px] font-bold text-slate-500">คลังของฉัน</p>
            <a href="/courses" className="block w-full rounded-lg px-3 py-2 text-left text-xs font-semibold text-[#0E5E4F] hover:bg-[#E6F4F1]">คอร์สเรียน</a>
            {['บุ๊กมาร์ก', 'แฟลชการ์ด', 'เอกสาร PDF'].map((item) => <button disabled key={item} title="ยังไม่เปิดใช้งาน" className="block w-full cursor-not-allowed rounded-lg px-3 py-2 text-left text-xs text-slate-400">{item} · เร็วๆ นี้</button>)}
          </div>
        </aside>
      </div>}

    </main>
  );
}
