'use client';

import {
  ArrowDownToLine,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  FileAudio,
  FileText,
  Layers3,
  LoaderCircle,
  Plus,
  Save,
  Sparkles,
  Trash2,
  Video,
  WandSparkles,
} from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import {
  apiClient,
  StudyNote,
  StudioArtifactRequest,
  StudioArtifactResponse,
} from '../../lib/api/client';
import { StudioArtifactView } from './StudioArtifactView';
import { validateStudioArtifactEdit } from '../../lib/studio-artifact-validation';
import type {
  LegacyStudioArtifactData,
  StudioArtifactEnvelope,
  StudioArtifactSource,
  TargetStudioArtifactData,
  TargetStudioArtifactKind,
} from '../../lib/api/client';

type DataRecord = Record<string, unknown>;
type ArtifactKind = StudioArtifactRequest['kind'];

export type StudyContext = {
  surah_number: number;
  ayah_number: number;
  surah_name: string;
  arabic_text: string;
  translation: string;
  tafsir_text: string;
  tafsir_approved: boolean;
  tafsir_source: string;
  tafsir_book_id: string | null;
};

const artifactOptions: { kind: ArtifactKind; label: string; caption: string; icon: typeof FileText }[] = [
  { kind: 'audio', label: 'Audio Overview', caption: 'สคริปต์พอดแคสต์ 2 ผู้ดำเนินรายการ', icon: FileAudio },
  { kind: 'report', label: 'Report', caption: 'รายงานสรุปและประเด็นศึกษา', icon: FileText },
  { kind: 'slides', label: 'Slides', caption: 'สไลด์สำหรับใช้สอน', icon: Layers3 },
  { kind: 'video', label: 'Video overview', caption: 'สตอรีบอร์ดพร้อมบทบรรยาย', icon: Video },
  { kind: 'flashcards', label: 'Flashcards', caption: 'การ์ดทบทวนคำศัพท์และความเข้าใจ', icon: BookOpen },
  { kind: 'quiz', label: 'Quiz', caption: 'แบบทดสอบ 3 ตัวเลือก', icon: Check },
  { kind: 'infographic', label: 'Infographic', caption: 'โครงภาพสรุปประเด็นสำคัญ', icon: Sparkles },
  { kind: 'comparison', label: 'Ikhtilaf matrix', caption: 'ตารางเปรียบเทียบทัศนะจากแหล่งที่เลือก', icon: Layers3 },
];

const tafsirSources = [
  { id: 'ibn_kathir', label: 'อิบนุกะษีร', available: true },
  { id: 'al_tabari', label: 'อัฏเฏาะบะรี', available: true },
  { id: 'al_qurtubi', label: 'อัลกุรฏุบี', available: true },
  { id: 'ibn_ashur', label: 'อิบนุอาชูร', available: false },
  { id: 'al_saadi', label: 'อัสสะอฺดี', available: true },
  { id: 'al_zuhayli', label: 'อัซซุฮัยลี', available: false },
];

function isRecord(value: unknown): value is DataRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function arrayOf(value: unknown): DataRecord[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function stringOf(value: unknown, key: string): string {
  return isRecord(value) && typeof value[key] === 'string' ? value[key] : '';
}

function isTargetStudioArtifactKind(value: unknown): value is TargetStudioArtifactKind {
  return value === 'audio' || value === 'quiz' || value === 'infographic';
}

function isLegacyStudioArtifactKind(value: unknown): value is LegacyStudioArtifactData['kind'] {
  return value === 'report' || value === 'slides' || value === 'video'
    || value === 'flashcards' || value === 'comparison';
}

function isStudioArtifactSource(value: unknown): value is StudioArtifactSource {
  return isRecord(value)
    && typeof value.id === 'string'
    && value.id.length > 0
    && typeof value.label === 'string'
    && value.label.length > 0
    && typeof value.url === 'string'
    && value.url.startsWith('https://');
}

function isTargetStudioArtifactData(value: unknown): value is TargetStudioArtifactData {
  if (
    !isRecord(value)
    || !isTargetStudioArtifactKind(value.kind)
    || !isRecord(value.artifact)
    || typeof value.artifact.title !== 'string'
    || typeof value.artifact.summary !== 'string'
    || !Array.isArray(value.sources)
    || !value.sources.every(isStudioArtifactSource)
    || !value.sources.some((source) => source.id === 'quran')
    || value.evidence_status !== 'AI-SYNTHESIS'
  ) {
    return false;
  }
  return true;
}

function isLegacyStudioArtifactData(value: unknown): value is LegacyStudioArtifactData {
  return isRecord(value)
    && isLegacyStudioArtifactKind(value.kind)
    && typeof value.title === 'string'
    && typeof value.summary === 'string'
    && ['sections', 'slides', 'scenes', 'questions', 'flashcards', 'rows', 'sources']
      .every((key) => Array.isArray(value[key]))
    && typeof value.evidence_status === 'string';
}

function isAudioStudioArtifact(artifact: StudioArtifactEnvelope): artifact is Extract<StudioArtifactEnvelope, { content: { segments: unknown[] } }> {
  return 'segments' in artifact.content;
}

function isQuizStudioArtifact(artifact: StudioArtifactEnvelope): artifact is Extract<StudioArtifactEnvelope, { content: { questions: unknown[] } }> {
  return 'questions' in artifact.content;
}

function isInfographicStudioArtifact(artifact: StudioArtifactEnvelope): artifact is Extract<StudioArtifactEnvelope, { content: { takeaway: string } }> {
  return 'takeaway' in artifact.content;
}

function targetDataWithArtifact(
  data: TargetStudioArtifactData,
  artifact: StudioArtifactEnvelope,
): TargetStudioArtifactData | null {
  switch (data.kind) {
    case 'audio':
      return isAudioStudioArtifact(artifact) ? { ...data, artifact } : null;
    case 'quiz':
      return isQuizStudioArtifact(artifact) ? { ...data, artifact } : null;
    case 'infographic':
      return isInfographicStudioArtifact(artifact) ? { ...data, artifact } : null;
  }
}

function normalizeTargetStudioArtifact(value: unknown): TargetStudioArtifactData | null {
  if (!isTargetStudioArtifactData(value)) return null;
  const validation = validateStudioArtifactEdit(value.kind, JSON.stringify(value.artifact));
  if (!validation.valid) return null;
  return targetDataWithArtifact(value, validation.artifact);
}

function ArtifactText({ artifact }: { artifact: DataRecord }) {
  const sections = arrayOf(artifact.sections);
  const slides = arrayOf(artifact.slides);
  const scenes = arrayOf(artifact.scenes);
  const questions = arrayOf(artifact.questions);
  const cards = arrayOf(artifact.flashcards);
  const rows = arrayOf(artifact.rows);
  const [answers, setAnswers] = useState<Record<number, number>>({});

  return (
    <div className="space-y-4">
      {sections.map((section, index) => (
        <section key={index} className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-[#073B32]">{stringOf(section, 'heading')}</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-600">{stringOf(section, 'text')}</p>
        </section>
      ))}
      {slides.map((slide, index) => (
        <section key={index} className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[#9A7914]">Slide {index + 1}</p>
          <h3 className="mt-1 text-sm font-bold text-[#073B32]">{stringOf(slide, 'title')}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
            {Array.isArray(slide.bullets) && slide.bullets.map((bullet, bulletIndex) => (
              <li key={bulletIndex}>{String(bullet)}</li>
            ))}
          </ul>
          {stringOf(slide, 'notes') && <p className="mt-3 border-t border-slate-100 pt-2 text-xs leading-5 text-slate-500">{stringOf(slide, 'notes')}</p>}
        </section>
      ))}
      {scenes.map((scene, index) => (
        <section key={index} className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-[100px_1fr]">
          <div className="grid aspect-video place-items-center rounded-lg bg-[#E6F4F1] text-[#0E5E4F]"><Video size={20} /></div>
          <div>
            <h3 className="text-sm font-semibold text-[#073B32]">ฉาก {index + 1}: {stringOf(scene, 'title')}</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">{stringOf(scene, 'visual_description')}</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{stringOf(scene, 'narration')}</p>
          </div>
        </section>
      ))}
      {cards.map((card, index) => (
        <details key={index} className="group rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-[#073B32]">{stringOf(card, 'front')}</summary>
          <p className="mt-3 border-t border-slate-100 pt-3 text-sm leading-6 text-slate-600">{stringOf(card, 'back')}</p>
        </details>
      ))}
      {questions.map((question, index) => (
        <section key={index} className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold leading-6 text-[#073B32]">{index + 1}. {stringOf(question, 'question')}</h3>
          <div className="mt-3 space-y-2">
            {Array.isArray(question.options) && question.options.map((option, optionIndex) => {
              const selected = answers[index] === optionIndex;
              const checked = selected && question.answer_index === optionIndex;
              const wrong = selected && question.answer_index !== optionIndex;
              return (
                <button key={optionIndex} type="button" onClick={() => setAnswers((current) => ({ ...current, [index]: optionIndex }))}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${checked ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : wrong ? 'border-rose-300 bg-rose-50 text-rose-800' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                  <span className="mr-2 text-xs text-slate-400">{String.fromCharCode(65 + optionIndex)}.</span>{String(option)}
                </button>
              );
            })}
          </div>
          {answers[index] != null && <p className="mt-3 text-xs leading-5 text-slate-500">{stringOf(question, 'explanation')}</p>}
        </section>
      ))}
      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-[#F5F9F7] text-[#073B32]"><tr><th className="px-3 py-2">ประเด็น</th><th className="px-3 py-2">ทัศนะจากแหล่งที่เลือก</th></tr></thead>
            <tbody>{rows.map((row, index) => <tr key={index} className="border-t border-slate-100"><td className="px-3 py-3 font-medium">{stringOf(row, 'claim')}</td><td className="px-3 py-3 text-slate-600">{stringOf(row, 'view')}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function SourcesPanel({
  surahs,
  surah,
  onSelectSurah,
  selectedSources,
  onToggleSource,
  tafsirApproved,
  context,
}: {
  surahs: DataRecord[];
  surah: number;
  onSelectSurah: (value: number) => void;
  selectedSources: string[];
  onToggleSource: (source: string) => void;
  tafsirApproved: boolean;
  context: StudyContext;
}) {
  const [surahsOpen, setSurahsOpen] = useState(true);
  const [notesOpen, setNotesOpen] = useState(true);
  const [activeNoteId, setActiveNoteId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState('');
  const [draftContent, setDraftContent] = useState('');
  const queryClient = useQueryClient();
  const notesQuery = useQuery({
    queryKey: ['workspace', 'notes'],
    queryFn: async () => (await apiClient.getNotes()).data,
  });
  const createNote = useMutation({
    mutationFn: (note: Omit<StudyNote, 'id' | 'created_at' | 'updated_at'>) => apiClient.createNote(note),
    onSuccess: ({ data }) => {
      queryClient.setQueryData<StudyNote[]>(['workspace', 'notes'], (notes = []) => [data, ...notes]);
      setActiveNoteId(data.id);
      setDraftTitle(data.title);
      setDraftContent(data.content);
    },
  });
  const updateNote = useMutation({
    mutationFn: ({ id, title, content }: { id: string; title: string; content: string }) =>
      apiClient.updateNote(id, { title, content }),
    onSuccess: ({ data }) => {
      queryClient.setQueryData<StudyNote[]>(['workspace', 'notes'], (notes = []) => notes.map((note) => note.id === data.id ? data : note));
    },
  });
  const deleteNote = useMutation({
    mutationFn: (id: string) => apiClient.deleteNote(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData<StudyNote[]>(['workspace', 'notes'], (notes = []) => notes.filter((note) => note.id !== id));
      if (activeNoteId === id) setActiveNoteId(null);
    },
  });
  const activeNote = useMemo(
    () => notesQuery.data?.find((note) => note.id === activeNoteId),
    [activeNoteId, notesQuery.data],
  );
  const createBlankNote = () => createNote.mutate({
    title: 'โน้ตใหม่',
    content: '',
    surah_number: null,
    ayah_number: null,
    source_label: '',
  });
  const saveSelectedAyah = () => {
    createNote.mutate({
      title: `${context.surah_name} ${context.surah_number}:${context.ayah_number}`,
      content: [context.arabic_text, context.translation, context.tafsir_approved ? context.tafsir_text : '']
        .filter(Boolean).join('\n\n'),
      surah_number: context.surah_number,
      ayah_number: context.ayah_number,
      source_label: context.tafsir_approved ? context.tafsir_source : 'อัลกุรอาน',
    });
  };
  const selectNote = (note: StudyNote) => {
    setActiveNoteId(note.id);
    setDraftTitle(note.title);
    setDraftContent(note.content);
  };

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-y-auto bg-white p-4 text-sm">
      <div className="mb-5">
        <h2 className="mb-3 text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">Sources & library</h2>
        <div className="space-y-1">
          <label className="flex items-start gap-2 rounded-lg px-2 py-2 text-xs text-slate-700">
            <input type="checkbox" checked={selectedSources.includes('quran')} onChange={() => onToggleSource('quran')} className="mt-0.5 accent-[#0E5E4F]" />
            <span><span className="block font-semibold">อัลกุรอาน · QPC v4</span><span className="text-[10px] text-slate-400">ข้อความอุษมานีและคำแปล</span></span>
          </label>
          {tafsirSources.map((source) => {
            const enabled = source.available && (source.id !== 'ibn_kathir' || tafsirApproved);
            return (
              <label key={source.id} title={enabled ? undefined : 'ยังไม่มีข้อมูลที่ผ่านการอนุมัติสำหรับแหล่งนี้'} className={`flex items-center gap-2 rounded-lg px-2 py-2 text-xs ${enabled ? 'text-slate-700' : 'text-slate-300'}`}>
                <input type="checkbox" disabled={!enabled} checked={enabled && selectedSources.includes('tafsir')}
                  onChange={() => onToggleSource('tafsir')} className="accent-[#0E5E4F]" />
                <span>{source.label}</span>
                {source.id === 'ibn_kathir' && tafsirApproved && <span className="ml-auto text-[9px] text-emerald-700">อนุมัติ</span>}
                {!enabled && <span className="ml-auto text-[9px]">ยังไม่พร้อม</span>}
              </label>
            );
          })}
          <label className="flex items-center gap-2 px-2 py-2 text-xs text-slate-300"><input type="checkbox" disabled />หลักสูตร Strapi <span className="ml-auto text-[9px]">ยังไม่เชื่อม</span></label>
        </div>
      </div>

      <div className="border-t border-slate-100 pt-4">
        <button type="button" onClick={() => setSurahsOpen((open) => !open)} className="flex w-full items-center gap-2 text-left text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">
          {surahsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />} Surah explorer <span className="ml-auto">{surahs.length || 114}</span>
        </button>
        {surahsOpen && <nav aria-label="สารบัญซูเราะฮ์" className="mt-2 max-h-[34vh] space-y-0.5 overflow-y-auto pr-1">
          {surahs.map((item, index) => {
            const id = Number(item.number ?? item.id ?? index + 1);
            const name = String(item.name_th ?? item.name_simple ?? item.transliteration ?? item.name ?? `Surah ${id}`);
            const revelation = String(item.revelation_type ?? item.revelation_place ?? '').toLowerCase();
            const isMeccan = revelation.startsWith('makk') || revelation.startsWith('mecc');
            const region = revelation ? (isMeccan ? 'มักกียะฮ์' : 'มะดะนียะฮ์') : '';
            return <button key={id} type="button" onClick={() => onSelectSurah(id)} aria-current={surah === id ? 'page' : undefined}
              className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs ${surah === id ? 'bg-[#E6F4F1] font-semibold text-[#073B32]' : 'text-slate-600 hover:bg-slate-50'}`}>
              <span className="w-5 text-right tabular-nums text-slate-400">{id}</span><span className="min-w-0 flex-1 truncate">{name}</span>
              {region && <span className="text-[9px] text-slate-400">{region}</span>}
            </button>;
          })}
        </nav>}
      </div>

      <div className="mt-4 border-t border-slate-100 pt-4">
        <div className="flex items-center justify-between">
          <button type="button" onClick={() => setNotesOpen((open) => !open)} className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">
            {notesOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />} Personal notes
          </button>
          <button type="button" onClick={createBlankNote} disabled={createNote.isPending} aria-label="สร้างโน้ตใหม่" className="rounded-md p-1 text-[#0E5E4F] hover:bg-[#E6F4F1]"><Plus size={15} /></button>
        </div>
        <button type="button" onClick={saveSelectedAyah} disabled={createNote.isPending} className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-[#d6e0dc] px-2 py-2 text-xs font-medium text-[#0E5E4F] hover:bg-[#F5F9F7] disabled:opacity-50">
          <Save size={13} /> Save selected Ayah
        </button>
        {notesQuery.isError && <p role="alert" className="mt-2 text-[10px] text-rose-700">โหลดโน้ตไม่สำเร็จ: {notesQuery.error instanceof Error ? notesQuery.error.message : 'เกิดข้อผิดพลาด'}</p>}
        {createNote.isError && <p role="alert" className="mt-2 text-[10px] text-rose-700">บันทึกโน้ตไม่สำเร็จ</p>}
        {notesOpen && <div className="mt-2 space-y-1">
          {(notesQuery.data ?? []).map((note) => <button key={note.id} type="button" onClick={() => selectNote(note)} className={`w-full truncate rounded-lg px-2 py-2 text-left text-xs ${activeNoteId === note.id ? 'bg-[#F5F9F7] font-semibold text-[#073B32]' : 'text-slate-600 hover:bg-slate-50'}`}>{note.title}</button>)}
          {notesQuery.isLoading && <p className="px-2 py-2 text-[10px] text-slate-400">กำลังโหลดโน้ต...</p>}
          {activeNote && <div className="mt-2 rounded-xl border border-slate-200 p-3">
            <input value={draftTitle} onChange={(event) => setDraftTitle(event.target.value)} aria-label="ชื่อโน้ต" className="w-full border-b border-slate-100 pb-2 text-xs font-semibold text-[#073B32] outline-none" />
            <textarea value={draftContent} onChange={(event) => setDraftContent(event.target.value)} aria-label="เนื้อหาโน้ต" rows={5} className="mt-2 w-full resize-y text-xs leading-5 text-slate-600 outline-none" />
            {activeNote.surah_number && <p className="text-[9px] text-slate-400">{activeNote.source_label} · {activeNote.surah_number}:{activeNote.ayah_number}</p>}
            <div className="mt-2 flex justify-between">
              <button type="button" onClick={() => updateNote.mutate({ id: activeNote.id, title: draftTitle, content: draftContent })} disabled={updateNote.isPending}
                className="rounded-md bg-[#0E5E4F] px-2.5 py-1.5 text-[10px] font-semibold text-white disabled:opacity-50">{updateNote.isPending ? 'กำลังบันทึก...' : 'บันทึก'}</button>
              <button type="button" onClick={() => deleteNote.mutate(activeNote.id)} disabled={deleteNote.isPending} aria-label="ลบโน้ต" className="rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-700"><Trash2 size={14} /></button>
            </div>
          </div>}
        </div>}
      </div>
    </aside>
  );
}

export function StudioPanel({
  context,
  selectedSources,
  onSaveArtifact,
  onSaveTargetArtifact,
}: {
  context: StudyContext;
  selectedSources: string[];
  onSaveArtifact: (title: string, content: string, context: StudyContext) => Promise<void>;
  onSaveTargetArtifact: (data: TargetStudioArtifactData, context: StudyContext) => Promise<void>;
}) {
  const [kind, setKind] = useState<ArtifactKind>('report');
  const [artifact, setArtifact] = useState<StudioArtifactResponse['data'] | null>(null);
  const [targetPreview, setTargetPreview] = useState<TargetStudioArtifactData | null>(null);
  const [artifactContext, setArtifactContext] = useState<StudyContext | null>(null);
  const [editorText, setEditorText] = useState('');
  const [notice, setNotice] = useState('');
  const [generationError, setGenerationError] = useState('');
  const [actionError, setActionError] = useState('');
  const generate = useMutation({
    mutationFn: ({ request }: { request: StudioArtifactRequest; context: StudyContext }) =>
      apiClient.createStudioArtifact(request),
    retry: false,
    onSuccess: (response, variables) => {
      const responseValue: unknown = response;
      if (!isRecord(responseValue) || responseValue.success !== true) {
        setGenerationError('AI returned an invalid Studio artifact');
        return;
      }

      const responseData: unknown = responseValue.data;
      if (isTargetStudioArtifactKind(isRecord(responseData) ? responseData.kind : null)) {
        const validData = normalizeTargetStudioArtifact(responseData);
        if (!validData) {
          setGenerationError('AI returned an invalid Studio artifact');
          return;
        }
        setArtifact(validData);
        setTargetPreview(validData);
        setEditorText(JSON.stringify({
          title: validData.artifact.title,
          summary: validData.artifact.summary,
          content: validData.artifact.content,
        }, null, 2));
      } else if (isLegacyStudioArtifactData(responseData)) {
        setArtifact(responseData);
        setTargetPreview(null);
        setEditorText(JSON.stringify(responseData, null, 2));
      } else {
        setGenerationError('AI returned an invalid Studio artifact');
        return;
      }
      setArtifactContext(variables.context);
      setGenerationError('');
      setActionError('');
      setNotice('');
    },
  });
  const selectedKind = artifactOptions.find((option) => option.kind === kind);
  const targetArtifact = artifact && 'artifact' in artifact ? artifact : null;
  const targetEdit = useMemo(
    () => targetArtifact ? validateStudioArtifactEdit(targetArtifact.kind, editorText) : null,
    [editorText, targetArtifact],
  );
  const targetExportData = targetArtifact && targetEdit?.valid
    ? targetDataWithArtifact(targetArtifact, targetEdit.artifact)
    : null;
  const targetEditError = targetArtifact && targetEdit && !targetEdit.valid
    ? targetEdit.error
    : targetArtifact && targetEdit?.valid && !targetExportData
      ? 'Edited content does not match the generated artifact kind'
      : '';
  const updateEditorText = (value: string) => {
    setEditorText(value);
    setNotice('');
    setActionError('');
    if (!targetArtifact) return;

    const validation = validateStudioArtifactEdit(targetArtifact.kind, value);
    if (validation.valid) {
      const preview = targetDataWithArtifact(targetArtifact, validation.artifact);
      if (preview) setTargetPreview(preview);
    }
  };
  const generateArtifact = () => {
    setNotice('');
    setGenerationError('');
    setActionError('');
    generate.mutate({
      request: {
        kind,
        surah_number: context.surah_number,
        ayah_number: context.ayah_number,
        surah_name: context.surah_name,
        arabic_text: context.arabic_text,
        translation: context.translation,
        tafsir_book_id: context.tafsir_book_id,
        selected_sources: selectedSources,
      },
      context: { ...context },
    });
  };
  const downloadArtifact = () => {
    const content = targetArtifact
      ? targetExportData ? JSON.stringify(targetExportData, null, 2) : null
      : editorText;
    if (content === null) {
      setActionError(targetEditError || 'Correct the artifact before exporting');
      return;
    }
    const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${artifact?.kind ?? kind}-${context.surah_number}-${context.ayah_number}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const saveArtifact = async () => {
    if (!artifact) return;
    setActionError('');
    try {
      if ('artifact' in artifact) {
        if (!targetExportData || !artifactContext) {
          setActionError(targetEditError || 'Correct the artifact before saving');
          return;
        }
        await onSaveTargetArtifact(targetExportData, artifactContext);
      } else {
        await onSaveArtifact(artifact.title || 'Studio artifact', editorText, artifactContext ?? context);
      }
      setNotice('บันทึกลง Personal Notes แล้ว');
    } catch (failure) {
      setActionError(failure instanceof Error ? failure.message : 'บันทึก artifact ไม่สำเร็จ');
    }
  };

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-y-auto bg-[#fbfcfc]">
      <div className="border-b border-slate-200 px-4 py-4">
        <div className="flex items-center gap-2 text-[#073B32]"><WandSparkles size={16} /><h2 className="text-sm font-bold">Studio</h2></div>
        <p className="mt-1 text-[10px] text-slate-500">สร้างสื่อจากแหล่งที่เลือก · {context.surah_number}:{context.ayah_number}</p>
      </div>
      <div className="grid grid-cols-2 gap-2 p-3">
        {artifactOptions.map((option) => {
          const IconComponent = option.icon;
          return <button key={option.kind} type="button" onClick={() => setKind(option.kind)} className={`min-h-[74px] rounded-xl border p-2.5 text-left transition ${kind === option.kind ? 'border-[#0E5E4F] bg-[#E6F4F1]' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
            <span className="flex items-center gap-1.5 text-xs font-semibold text-[#073B32]"><IconComponent size={14} />{option.label}</span>
            <span className="mt-1.5 block text-[9px] leading-4 text-slate-500">{option.caption}</span>
          </button>;
        })}
      </div>
      <div className="px-3 pb-3">
        <button type="button" onClick={generateArtifact} disabled={generate.isPending || !selectedSources.includes('quran')} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0E5E4F] px-3 py-2.5 text-xs font-semibold text-white hover:bg-[#073B32] disabled:cursor-not-allowed disabled:opacity-50">
          {generate.isPending ? <LoaderCircle size={15} className="animate-spin" /> : <Sparkles size={15} />}
          {generate.isPending ? 'กำลังสร้าง...' : `สร้าง ${selectedKind?.label ?? 'Artifact'}`}
        </button>
        {(generate.isError || generationError) && <p role="alert" className="mt-2 rounded-lg bg-rose-50 p-2 text-[10px] leading-4 text-rose-700">{generationError || (generate.error instanceof Error ? generate.error.message : 'สร้างสื่อไม่สำเร็จ')}</p>}
        {actionError && <p role="alert" className="mt-2 rounded-lg bg-rose-50 p-2 text-[10px] leading-4 text-rose-700">{actionError}</p>}
        {notice && <p role="status" className="mt-2 rounded-lg bg-emerald-50 p-2 text-[10px] text-emerald-800">{notice}</p>}
      </div>
      <div className="min-h-0 flex-1 border-t border-slate-200 p-3">
        {!artifact && <div className="flex h-full min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 p-5 text-center">
          <WandSparkles size={20} className="text-slate-300" />
          <p className="mt-3 text-xs font-semibold text-slate-600">Artifact viewer</p>
          <p className="mt-1 text-[10px] leading-5 text-slate-400">เลือกชนิดสื่อและสร้างจากอายะฮ์กับแหล่งข้อมูลที่ทำเครื่องหมายไว้</p>
        </div>}
        {artifact && <div>
          {'artifact' in artifact ? (
            <StudioArtifactView data={targetPreview ?? artifact} />
          ) : (
            <>
              <div className="mb-3 flex items-start justify-between gap-2">
                <div><h3 className="text-sm font-bold text-[#073B32]">{artifact.title}</h3><p className="mt-1 text-[10px] leading-4 text-slate-500">{artifact.summary}</p></div>
                <span className="shrink-0 rounded-full bg-violet-100 px-2 py-1 text-[8px] font-bold text-violet-700">{artifact.evidence_status}</span>
              </div>
              <p className="mb-2 flex items-center gap-1 text-[9px] text-slate-400"><span className="rounded-full bg-[#E6F4F1] px-2 py-0.5 text-[#0E5E4F]">[1] {context.surah_name} {context.surah_number}:{context.ayah_number}</span>{context.tafsir_approved && selectedSources.includes('tafsir') && <span className="rounded-full bg-[#E6F4F1] px-2 py-0.5 text-[#0E5E4F]">[2] {context.tafsir_source}</span>}</p>
              <ArtifactText artifact={artifact} />
            </>
          )}
          <details className="mt-3 rounded-xl border border-slate-200 bg-white">
            <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-slate-600">แก้ไข artifact (JSON)</summary>
            <textarea
              value={editorText}
              onChange={(event) => updateEditorText(event.target.value)}
              aria-label="แก้ไข artifact JSON"
              aria-invalid={Boolean(targetEditError)}
              rows={10}
              className="w-full resize-y border-t border-slate-100 p-3 font-mono text-[10px] leading-4 text-slate-600 outline-none"
            />
            {targetEditError && <p role="alert" className="border-t border-rose-100 bg-rose-50 px-3 py-2 text-[10px] leading-4 text-rose-700">{targetEditError}</p>}
          </details>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button type="button" onClick={downloadArtifact} disabled={Boolean(targetArtifact && !targetExportData)} className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-2 text-[10px] font-semibold text-slate-600 disabled:cursor-not-allowed disabled:opacity-50"><ArrowDownToLine size={13} />ส่งออก JSON</button>
            <button type="button" onClick={() => void saveArtifact()} disabled={Boolean(targetArtifact && !targetExportData)} className="flex items-center justify-center gap-1.5 rounded-lg bg-[#E6F4F1] px-2 py-2 text-[10px] font-semibold text-[#0E5E4F] disabled:cursor-not-allowed disabled:opacity-50"><Save size={13} />Save to Note</button>
          </div>
          {kind === 'video' && <p className="mt-2 text-[9px] leading-4 text-slate-400">วิดีโอจัดทำเป็น storyboard; ไม่มีการเรนเดอร์ไฟล์วิดีโอจริง</p>}
        </div>}
      </div>
    </aside>
  );
}
