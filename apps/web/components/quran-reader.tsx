"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

type Surah = {
  number: number;
  name: string;
  englishName: string;
  englishNameTranslation: string;
  numberOfAyahs: number;
  revelationType: string;
};

type SurahBackground = {
  surah_number: number;
  surah_name: string;
  short_text: string;
  text: string;
  language: "id";
  source: string;
  source_id: string;
  rights_status: string;
  rights_allowed_uses: string[];
};

type MushafLayoutLine = {
  line_number: number;
  line_type: "ayah" | "basmallah" | "surah_name";
  is_centered: boolean;
  surah_number?: number;
  verse_keys?: string[];
};

type MushafLayoutPage = {
  name: string;
  page_number: number;
  total_pages: number;
  lines_per_page: number;
  font_name: string;
  font_status: string;
  glyph_rendering_enabled: boolean;
  source: string;
  source_id: string;
  rights_status: string;
  lines: MushafLayoutLine[];
};

type Ayah = {
  number: number;
  numberInSurah: number;
  text: string;
  translation?: string;
  audio?: string;
  script_type?: string;
  font_family?: string;
  words?: Array<{ position: number; text: string; location: string }>;
  page_number?: number;
  juz_number?: number;
  hizb_number?: number;
};

type Agent = {
  id: string;
  label: string;
  author: string;
  author_ar: string;
  source_language: "ar" | "id";
  database_available: boolean;
  enabled: boolean;
  rights_status: string;
  verification_status: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  author?: string;
  agentKey?: string;
  error?: boolean;
  sources?: ChatResult["sources"];
};

type ChatResult = {
  answer_th?: string | null;
  disclaimer_th?: string;
  sources?: Array<{
    book: string;
    book_ar: string;
    author: string;
    author_ar: string;
    language: string;
    ayah_range: string;
    original_text: string;
    resource_url?: string | null;
    rights_status: string;
    verification_status: string;
    evidence_status: string;
  }>;
};

const languageNames: Record<string, string> = {
  ar: "อาหรับ",
  id: "อินโดนีเซีย",
};

const STUDY_STORAGE_KEY = "quran-ai-study-v1";

type StudyRecord = {
  surahNumber: number;
  ayahNumber: number;
  surahName: string;
  ayahText: string;
  timestamp: number;
};

type StudyStorage = {
  bookmarks: StudyRecord[];
  history: StudyRecord[];
};

const EMPTY_STUDY_STORAGE: StudyStorage = { bookmarks: [], history: [] };

function isStudyRecord(value: unknown): value is StudyRecord {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    Number.isInteger(record.surahNumber) &&
    Number(record.surahNumber) >= 1 &&
    Number(record.surahNumber) <= 114 &&
    Number.isInteger(record.ayahNumber) &&
    Number(record.ayahNumber) > 0 &&
    typeof record.surahName === "string" &&
    typeof record.ayahText === "string" &&
    typeof record.timestamp === "number"
  );
}

async function responseJson<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as
    | T
    | { detail?: string; error?: string };
  if (!response.ok) {
    const errorPayload = payload as { detail?: string; error?: string };
    throw new Error(
      errorPayload.detail ?? errorPayload.error ?? "เกิดข้อผิดพลาด โปรดลองอีกครั้ง",
    );
  }
  return payload as T;
}

async function fetchQuranData<T>(
  proxyPath: string,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(proxyPath, { cache: "no-store", signal });
  return responseJson<T>(response);
}

export default function QuranReader() {
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [surahNumber, setSurahNumber] = useState(1);
  const [surahSearch, setSurahSearch] = useState("");
  const [surahBackground, setSurahBackground] = useState<SurahBackground | null>(null);
  const [surahBackgroundLoading, setSurahBackgroundLoading] = useState(false);
  const [surahBackgroundError, setSurahBackgroundError] = useState("");
  const [mushafPageNumber, setMushafPageNumber] = useState(1);
  const [mushafLayoutOpen, setMushafLayoutOpen] = useState(false);
  const [mushafLayout, setMushafLayout] = useState<MushafLayoutPage | null>(null);
  const [mushafLayoutLoading, setMushafLayoutLoading] = useState(false);
  const [mushafLayoutError, setMushafLayoutError] = useState("");
  const [ayahs, setAyahs] = useState<Ayah[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAyah, setSelectedAyah] = useState<Ayah | null>(null);
  const [selectedAyahSurahNumber, setSelectedAyahSurahNumber] = useState<number | null>(null);
  const [selectedAgentKey, setSelectedAgentKey] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [studyTab, setStudyTab] = useState<"overview" | "sources">("overview");
  const [compareMode, setCompareMode] = useState(false);
  const [compareAgentKeys, setCompareAgentKeys] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [translationError, setTranslationError] = useState("");
  const [audioError, setAudioError] = useState("");
  const [audioAyah, setAudioAyah] = useState<Ayah | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [studyStorage, setStudyStorage] = useState<StudyStorage>(EMPTY_STUDY_STORAGE);
  const [storageReady, setStorageReady] = useState(false);
  const [storageWritable, setStorageWritable] = useState(true);
  const [storageError, setStorageError] = useState("");
  const [studyList, setStudyList] = useState<"bookmarks" | "history" | null>(null);
  const [pendingStudy, setPendingStudy] = useState<StudyRecord | null>(null);
  const [loadingSurahs, setLoadingSurahs] = useState(true);
  const [loadingAyahs, setLoadingAyahs] = useState(false);
  const [loadedSurahNumber, setLoadedSurahNumber] = useState(0);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [sending, setSending] = useState(false);
  const [readerError, setReaderError] = useState("");
  const [agentError, setAgentError] = useState("");
  const [chatError, setChatError] = useState("");
  const audioRef = useRef<HTMLAudioElement>(null);
  const lastRead = studyStorage.history[0] ?? null;

  const studyAyah = useCallback((ayah: Ayah, selectedSurahNumber: number) => {
    const surah = surahs.find((item) => item.number === selectedSurahNumber);
    const record: StudyRecord = {
      surahNumber: selectedSurahNumber,
      ayahNumber: ayah.numberInSurah,
      surahName: surah?.name ?? `ซูเราะฮ์ ${selectedSurahNumber}`,
      ayahText: ayah.text,
      timestamp: Date.now(),
    };
    setStudyStorage((current) => ({
      ...current,
      history: [
        record,
        ...current.history.filter(
          (item) =>
            item.surahNumber !== record.surahNumber ||
            item.ayahNumber !== record.ayahNumber,
        ),
      ].slice(0, 20),
    }));
    setSelectedAyahSurahNumber(selectedSurahNumber);
    setSelectedAyah(ayah);
    setStudyTab("overview");
    setMessages([]);
    setDraft("");
    setChatError("");
    const ayahRow = document.getElementById(
      `ayah-${selectedSurahNumber}-${ayah.numberInSurah}`,
    );
    ayahRow?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [surahs]);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agentKey(agent) === selectedAgentKey) ?? null,
    [agents, selectedAgentKey],
  );
  const filteredSurahs = useMemo(() => {
    const query = surahSearch.trim().toLocaleLowerCase();
    if (!query) return surahs;
    return surahs.filter((surah) =>
      [
        String(surah.number),
        surah.name,
        surah.englishName,
        surah.englishNameTranslation,
      ].some((value) => value.toLocaleLowerCase().includes(query)),
    );
  }, [surahSearch, surahs]);
  const citationSources = useMemo(
    () => messages.flatMap((message) => message.sources ?? []),
    [messages],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchQuranData<{ data: Surah[] }>(
      "/api/quran/surahs",
      controller.signal,
    )
      .then((result) => setSurahs(result.data))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setReaderError(
            error instanceof Error ? error.message : "โหลดรายชื่อซูเราะฮ์ไม่สำเร็จ",
          );
        }
      })
      .finally(() => setLoadingSurahs(false));

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setSurahBackground(null);
    setSurahBackgroundError("");
    setSurahBackgroundLoading(true);
    fetchQuranData<{ data: SurahBackground }>(
      `/api/quran/surahs/${surahNumber}/info`,
      controller.signal,
    )
      .then((result) => setSurahBackground(result.data))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setSurahBackgroundError(
            error instanceof Error ? error.message : "โหลดข้อมูลบริบทซูเราะฮ์ไม่สำเร็จ",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSurahBackgroundLoading(false);
      });

    return () => controller.abort();
  }, [surahNumber]);

  useEffect(() => {
    if (!mushafLayoutOpen) return;
    const controller = new AbortController();
    setMushafLayout(null);
    setMushafLayoutError("");
    setMushafLayoutLoading(true);
    fetchQuranData<{ data: MushafLayoutPage }>(
      `/api/quran/mushaf/15-line/pages/${mushafPageNumber}`,
      controller.signal,
    )
      .then((result) => setMushafLayout(result.data))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setMushafLayoutError(
            error instanceof Error ? error.message : "โหลดข้อมูลผังหน้ามุศหัฟไม่สำเร็จ",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setMushafLayoutLoading(false);
      });

    return () => controller.abort();
  }, [mushafLayoutOpen, mushafPageNumber]);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingAyahs(true);
    setLoadedSurahNumber(0);
    setReaderError("");
    setTranslationError("");
    setAudioError("");
    audioRef.current?.pause();
    setAyahs([]);
    setAudioAyah(null);
    setIsPlaying(false);
    fetchQuranData<{ data: { ayahs: Ayah[] } }>(
      `/api/quran/surahs/${surahNumber}?edition=quran-uthmani`,
      controller.signal,
    )
      .then(async (arabicResult) => {
        const [translationResult, recitationResult] = await Promise.allSettled([
          fetchQuranData<{ data: { ayahs: Ayah[] } }>(
            `/api/quran/surahs/${surahNumber}?edition=th.thai`,
            controller.signal,
          ),
          fetchQuranData<{ data: { ayahs: Ayah[] } }>(
            `/api/quran/surahs/${surahNumber}?edition=ar.alafasy`,
            controller.signal,
          ),
        ]);
        if (controller.signal.aborted) return;
        const translations =
          translationResult.status === "fulfilled"
            ? new Map(
                translationResult.value.data.ayahs.map((ayah) => [
                  ayah.numberInSurah,
                  ayah.text.replace(/\u200B/g, "").trim(),
                ]),
              )
            : null;
        const audio =
          recitationResult.status === "fulfilled"
            ? new Map(
                recitationResult.value.data.ayahs.map((ayah) => [
                  ayah.numberInSurah,
                  ayah.audio,
                ]),
              )
            : null;
        setAyahs(
          arabicResult.data.ayahs.map((ayah) => ({
            ...ayah,
            ...(translations?.has(ayah.numberInSurah)
              ? { translation: translations.get(ayah.numberInSurah) }
              : {}),
            ...(audio?.has(ayah.numberInSurah)
              ? { audio: audio.get(ayah.numberInSurah) }
              : {}),
          })),
        );
        setLoadedSurahNumber(surahNumber);
        if (!translations) setTranslationError("โหลดคำแปลภาษาไทยไม่สำเร็จ");
        if (!audio) setAudioError("โหลดข้อมูลเสียงอ่านไม่สำเร็จ");
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setReaderError(
            error instanceof Error ? error.message : "โหลดอายะฮ์ไม่สำเร็จ",
          );
          setAyahs([]);
          setPendingStudy(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingAyahs(false);
      });

    return () => controller.abort();
  }, [surahNumber]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STUDY_STORAGE_KEY);
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (!parsed || typeof parsed !== "object") {
          throw new Error("ข้อมูลการอ่านที่บันทึกไว้มีรูปแบบไม่ถูกต้อง");
        }
        const savedData = parsed as Record<string, unknown>;
        const bookmarks = savedData.bookmarks;
        const history = savedData.history;
        if (!Array.isArray(bookmarks) || !Array.isArray(history)) {
          throw new Error("ข้อมูลการอ่านที่บันทึกไว้มีรูปแบบไม่ถูกต้อง");
        }
        if (!bookmarks.every(isStudyRecord) || !history.every(isStudyRecord)) {
          throw new Error("รายการอายะฮ์ที่บันทึกไว้มีรูปแบบไม่ถูกต้อง");
        }
        setStudyStorage({ bookmarks, history });
      }
    } catch (error) {
      setStorageWritable(false);
      setStorageError(
        error instanceof Error
          ? error.message
          : "อ่านข้อมูลการบันทึกในอุปกรณ์นี้ไม่สำเร็จ",
      );
    } finally {
      setStorageReady(true);
    }
  }, []);

  useEffect(() => {
    if (!storageReady || !storageWritable) return;
    try {
      window.localStorage.setItem(STUDY_STORAGE_KEY, JSON.stringify(studyStorage));
    } catch (error) {
      setStorageWritable(false);
      setStorageError(
        error instanceof Error
          ? "บันทึกข้อมูลในอุปกรณ์ไม่สำเร็จ พื้นที่จัดเก็บอาจเต็ม"
          : "บันทึกข้อมูลในอุปกรณ์ไม่สำเร็จ",
      );
    }
  }, [storageReady, storageWritable, studyStorage]);

  useEffect(() => {
    if (
      !pendingStudy ||
      pendingStudy.surahNumber !== surahNumber ||
      loadedSurahNumber !== surahNumber ||
      loadingAyahs
    ) return;
    const ayah = ayahs.find((item) => item.numberInSurah === pendingStudy.ayahNumber);
    if (!ayah) {
      setPendingStudy(null);
      setReaderError(`ไม่พบอายะฮ์ ${pendingStudy.surahNumber}:${pendingStudy.ayahNumber}`);
      return;
    }
    setPendingStudy(null);
    studyAyah(ayah, pendingStudy.surahNumber);
  }, [ayahs, loadedSurahNumber, loadingAyahs, pendingStudy, studyAyah, surahNumber]);

  useEffect(() => {
    if (!selectedAyah) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedAyah(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [selectedAyah]);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/tafsir/agents", {
      signal: controller.signal,
      cache: "no-store",
    })
      .then((response) => responseJson<{ agents: Agent[] }>(response))
      .then((result) => {
        setAgents(result.agents);
        const firstAgent =
          result.agents.find((agent) => agent.enabled) ?? result.agents[0];
        if (firstAgent) setSelectedAgentKey(agentKey(firstAgent));
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setAgentError(
            error instanceof Error ? error.message : "โหลดรายชื่อแหล่งตัฟซีรไม่สำเร็จ",
          );
        }
      })
      .finally(() => setLoadingAgents(false));

    return () => controller.abort();
  }, []);

  function openTafsir(ayah: Ayah) {
    studyAyah(ayah, surahNumber);
  }

  function jumpToStudy(record: StudyRecord) {
    setStudyList(null);
    if (record.surahNumber === surahNumber && !loadingAyahs) {
      const ayah = ayahs.find((item) => item.numberInSurah === record.ayahNumber);
      if (ayah) {
        studyAyah(ayah, record.surahNumber);
        return;
      }
    }
    setPendingStudy(record);
    setSurahNumber(record.surahNumber);
  }

  function toggleBookmark(ayah: Ayah) {
    const isSaved = studyStorage.bookmarks.some(
      (item) => item.surahNumber === surahNumber && item.ayahNumber === ayah.numberInSurah,
    );
    const surah = surahs.find((item) => item.number === surahNumber);
    const record: StudyRecord = {
      surahNumber,
      ayahNumber: ayah.numberInSurah,
      surahName: surah?.name ?? `ซูเราะฮ์ ${surahNumber}`,
      ayahText: ayah.text,
      timestamp: Date.now(),
    };
    setStudyStorage((current) => ({
      ...current,
      bookmarks: isSaved
        ? current.bookmarks.filter(
            (item) =>
              item.surahNumber !== surahNumber ||
              item.ayahNumber !== ayah.numberInSurah,
          )
        : [record, ...current.bookmarks],
    }));
  }

  function playAyah(ayah: Ayah) {
    const player = audioRef.current;
    if (!player || !ayah.audio) {
      setAudioError("ไม่มีเสียงอ่านสำหรับอายะฮ์นี้");
      return;
    }
    setAudioError("");
    if (audioAyah?.number === ayah.number && !player.paused) {
      player.pause();
      return;
    }
    setAudioAyah(ayah);
    player.src = ayah.audio;
    player.load();
    player.play().catch(() => {
      setAudioError("เล่นเสียงไม่สำเร็จ โปรดลองอีกครั้ง");
      setIsPlaying(false);
    });
  }

  function toggleCompareAgent(key: string) {
    setCompareAgentKeys((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, key],
    );
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAyah || selectedAyahSurahNumber === null || sending) return;
    const question = draft.trim();
    if (!question) return;

    const targetAgents = compareMode
      ? agents.filter(
          (agent) => agent.enabled && compareAgentKeys.includes(agentKey(agent)),
        )
      : selectedAgent?.enabled
        ? [selectedAgent]
        : [];
    if (compareMode ? targetAgents.length < 2 : targetAgents.length === 0) {
      setChatError(
        compareMode
          ? "การเปรียบเทียบต้องเลือกแหล่งตัฟซีรที่ผ่านการตรวจสอบสิทธิ์อย่างน้อยสองแหล่ง"
          : "แหล่งตัฟซีรนี้ยังไม่พร้อมให้ใช้งาน",
      );
      return;
    }

    const conversation = [...messages, { role: "user" as const, content: question }];
    setMessages(conversation);
    setDraft("");
    setChatError("");
    setSending(true);

    try {
      const history = messages;
      const responses = await Promise.all(
        targetAgents.map(async (agent): Promise<ChatMessage> => {
          try {
            const agentHistory = history
              .filter(
                (message) =>
                  !message.error &&
                  (message.role === "user" || message.agentKey === agentKey(agent)),
              )
              .slice(-10)
              .map(({ role, content }) => ({ role, content }));
            const response = await fetch("/api/tafsir/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                surah: selectedAyahSurahNumber,
                ayah: selectedAyah.numberInSurah,
                scholar_id: agent.id,
                source_language: agent.source_language,
                message: question,
                history: agentHistory,
              }),
            });
            const result = await responseJson<ChatResult>(response);
            return {
              role: "assistant",
              content: result.answer_th ?? "ยังไม่มีคำอธิบาย",
              author: agent.author,
              agentKey: agentKey(agent),
              sources: result.sources ?? [],
            };
          } catch (error) {
            return {
              role: "assistant",
              content:
                error instanceof Error
                  ? error.message
                  : "ขออภัย แหล่งตัฟซีรนี้ยังตอบคำถามไม่ได้",
              author: agent.author,
              agentKey: agentKey(agent),
              error: true,
            };
          }
        }),
      );
      setMessages([...conversation, ...responses]);
    } catch (error) {
      if (!compareMode) setMessages(messages);
      setDraft(question);
      setChatError(
        error instanceof Error ? error.message : "ส่งคำถามไม่สำเร็จ โปรดลองอีกครั้ง",
      );
    } finally {
      setSending(false);
    }
  }

  const currentSurah = surahs.find((surah) => surah.number === surahNumber);
  const studySurahNumber = selectedAyahSurahNumber ?? surahNumber;
  const firstAyahIncludesBasmala = ayahs[0]?.text
    .replace(/^\uFEFF/, "")
    .trimStart()
    .startsWith("بِسْمِ");

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Quran AI หน้าแรก">
          <span className="brand-mark" aria-hidden="true">ق</span>
          <span className="brand-copy">
            <strong>QURAN AI</strong>
            <small>อ่าน · ใคร่ครวญ · เข้าใจ</small>
          </span>
        </a>
        <div className="topbar-right">
          <span className="topbar-note">พื้นที่ศึกษาอัลกุรอาน</span>
          <span className="locale-pill">ไทย</span>
        </div>
      </header>

      <div className="study-workspace">
        <aside className="surah-sidebar" aria-label="นำทางอัลกุรอาน">
          <div className="sidebar-heading">
            <span className="section-kicker">LIBRARY</span>
            <h2>คลังอัลกุรอาน</h2>
          </div>
          <div className="sidebar-shortcuts">
            <button
              type="button"
              className={studyList === "bookmarks" ? "sidebar-shortcut is-active" : "sidebar-shortcut"}
              aria-pressed={studyList === "bookmarks"}
              onClick={() => setStudyList((current) => current === "bookmarks" ? null : "bookmarks")}
            >
              <span aria-hidden="true">☆</span>
              <span>บันทึกไว้</span>
              <small>{studyStorage.bookmarks.length}</small>
            </button>
            <button
              type="button"
              className={studyList === "history" ? "sidebar-shortcut is-active" : "sidebar-shortcut"}
              aria-pressed={studyList === "history"}
              onClick={() => setStudyList((current) => current === "history" ? null : "history")}
            >
              <span aria-hidden="true">◷</span>
              <span>ประวัติอ่าน</span>
            </button>
          </div>
          {studyList && (
            <section className="study-list-panel" aria-label={studyList === "bookmarks" ? "อายะฮ์ที่บันทึกไว้" : "ประวัติการอ่าน"}>
              <div className="study-list-heading">
                <h3>{studyList === "bookmarks" ? "อายะฮ์ที่บันทึกไว้" : "อายะฮ์ที่ศึกษาเมื่อเร็ว ๆ นี้"}</h3>
                <button type="button" className="text-button" onClick={() => setStudyList(null)}>
                  ปิด
                </button>
              </div>
              {(studyList === "bookmarks" ? studyStorage.bookmarks : studyStorage.history).length === 0 ? (
                <p className="study-list-empty">
                  {studyList === "bookmarks" ? "ยังไม่มีอายะฮ์ที่บันทึกไว้ กด “บันทึก” ใต้ข้อความอายะฮ์เพื่อเก็บไว้อ่านภายหลัง" : "อายะฮ์ที่เปิดศึกษาไว้จะแสดงที่นี่"}
                </p>
              ) : (
                <ul>
                  {(studyList === "bookmarks" ? studyStorage.bookmarks : studyStorage.history).map((record) => (
                    <li key={`${record.surahNumber}:${record.ayahNumber}`}>
                      <button
                        type="button"
                        className="study-list-item"
                        onClick={() => jumpToStudy(record)}
                      >
                        <strong>{record.surahName} · {record.surahNumber}:{record.ayahNumber}</strong>
                        <span lang="ar" dir="rtl">{record.ayahText}</span>
                      </button>
                      {studyList === "bookmarks" && (
                        <button
                          type="button"
                          className="remove-bookmark"
                          aria-label={`ลบอายะฮ์ ${record.surahNumber}:${record.ayahNumber} จากรายการบันทึก`}
                          onClick={() =>
                            setStudyStorage((current) => ({
                              ...current,
                              bookmarks: current.bookmarks.filter(
                                (item) =>
                                  item.surahNumber !== record.surahNumber ||
                                  item.ayahNumber !== record.ayahNumber,
                              ),
                            }))
                          }
                        >
                          ลบ
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
          {lastRead && (
            <button type="button" className="sidebar-last-read" onClick={() => jumpToStudy(lastRead)}>
              <span>อ่านต่อจากเดิม</span>
              <strong>{lastRead.surahName} · {lastRead.surahNumber}:{lastRead.ayahNumber}</strong>
            </button>
          )}
          <label className="surah-search">
            <span className="sr-only">ค้นหาซูเราะฮ์</span>
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              value={surahSearch}
              onChange={(event) => setSurahSearch(event.target.value)}
              placeholder="ค้นหาซูเราะฮ์"
              aria-label="ค้นหาซูเราะฮ์"
            />
          </label>
          <nav className="surah-list" aria-label="รายการซูเราะฮ์">
            {loadingSurahs && <p className="sidebar-status">กำลังโหลดซูเราะฮ์…</p>}
            {!loadingSurahs && filteredSurahs.length === 0 && (
              <p className="sidebar-status">ไม่พบซูเราะฮ์ที่ค้นหา</p>
            )}
            {filteredSurahs.map((surah) => (
              <button
                type="button"
                key={surah.number}
                className={surah.number === surahNumber ? "surah-list-item is-active" : "surah-list-item"}
                aria-current={surah.number === surahNumber ? "page" : undefined}
                onClick={() => setSurahNumber(surah.number)}
              >
                <span className="surah-list-number">{surah.number}</span>
                <span className="surah-list-name">
                  <strong>{surah.englishName}</strong>
                  <small>{surah.englishNameTranslation}</small>
                </span>
                <span className="surah-list-arabic" lang="ar" dir="rtl">{surah.name}</span>
              </button>
            ))}
          </nav>
          <p className="sidebar-footnote">١١٤ ซูเราะฮ์ · มุศหัฟมาตรฐาน</p>
        </aside>

      <section className="reader-section" aria-label="เครื่องอ่านอัลกุรอาน">
        <div className="reader-toolbar">
          <div className="reader-title">
            <span className="section-kicker">
              {currentSurah ? `SURAH ${String(currentSurah.number).padStart(3, "0")}` : "QURAN READER"}
            </span>
            <h2>{currentSurah?.englishName ?? "อัลกุรอาน"}</h2>
          </div>
          <div className="reader-tools">
            <div className="surah-navigation" aria-label="นำทางระหว่างซูเราะฮ์">
              <button
                type="button"
                className="secondary-button"
                aria-label="ซูเราะฮ์ก่อนหน้า"
                disabled={surahNumber <= 1 || loadingSurahs}
                onClick={() => setSurahNumber((number) => Math.max(1, number - 1))}
              >
                ← ก่อนหน้า
              </button>
              <label className="surah-picker">
                <span>เลือกซูเราะฮ์</span>
                <select
                  value={surahNumber}
                  onChange={(event) => setSurahNumber(Number(event.target.value))}
                  disabled={loadingSurahs || surahs.length === 0}
                  aria-label="เลือกซูเราะฮ์"
                >
                  {surahs.map((surah) => (
                    <option key={surah.number} value={surah.number}>
                      {surah.number}. {surah.name} — {surah.englishName}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="secondary-button"
                aria-label="ซูเราะฮ์ถัดไป"
                disabled={surahNumber >= 114 || loadingSurahs}
                onClick={() => setSurahNumber((number) => Math.min(114, number + 1))}
              >
                ถัดไป →
              </button>
            </div>
            <div className="script-status">
              <strong>อุษมานี</strong>
              <small>QPC V4 Tajweed ยังไม่เผยแพร่</small>
            </div>
          </div>
        </div>

        {lastRead && (
          <div className="continue-reading">
            <div>
              <span>อ่านล่าสุด</span>
              <strong>{lastRead.surahName} · อายะฮ์ {lastRead.ayahNumber}</strong>
            </div>
            <button type="button" className="text-button" onClick={() => jumpToStudy(lastRead)}>
              อ่านต่อ →
            </button>
          </div>
        )}

        {storageError && <p className="notice notice-error" role="status">{storageError} ข้อมูลส่วนนี้เก็บในอุปกรณ์ของคุณเท่านั้น</p>}
        <div className="audio-player" hidden={!audioAyah}>
          {audioAyah && (
            <span>เสียงอ่าน · อัลอะฟาซี · อายะฮ์ {surahNumber}:{audioAyah.numberInSurah}</span>
          )}
          <audio
            ref={audioRef}
            controls
            preload="none"
            aria-label={
              audioAyah
                ? `เสียงอ่านอายะฮ์ ${surahNumber}:${audioAyah.numberInSurah} โดยอัลอะฟาซี`
                : "เครื่องเล่นเสียงอ่าน"
            }
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onError={() => setAudioError("โหลดไฟล์เสียงไม่สำเร็จ")}
          />
        </div>

        {currentSurah && (
          <div className="surah-heading">
            <div className="surah-ornament" aria-hidden="true">۞</div>
            <span className="surah-translation">{currentSurah.englishNameTranslation}</span>
            <h3 lang="ar" dir="rtl">{currentSurah.name}</h3>
            <p>
              ซูเราะฮ์ที่ {currentSurah.number} <span>·</span>{" "}
              {currentSurah.numberOfAyahs} อายะฮ์ <span>·</span>{" "}
              {currentSurah.revelationType === "Meccan" ? "มักกียะฮ์" : "มะดะนียะฮ์"}
            </p>
          </div>
        )}

        {surahBackgroundLoading && (
          <p className="surah-background-status" role="status">กำลังโหลดบริบทซูเราะฮ์…</p>
        )}
        {surahBackgroundError && (
          <p className="notice notice-warning surah-background-status" role="status">
            {surahBackgroundError}
          </p>
        )}
        {surahBackground && (
          <details className="surah-background">
            <summary>อ่านบริบทซูเราะฮ์ · ภาษาอินโดนีเซีย</summary>
            <div className="surah-background-content">
              {surahBackground.short_text && (
                <p className="surah-background-summary">{surahBackground.short_text}</p>
              )}
              <details className="surah-background-full">
                <summary>อ่านรายละเอียดฉบับเต็ม</summary>
                <div className="surah-background-paragraphs">
                  {surahBackground.text.split(/\n{2,}/).map((paragraph, index) => (
                    <p key={`${surahBackground.surah_number}-${index}`}>{paragraph}</p>
                  ))}
                </div>
              </details>
              <p className="surah-background-attribution">
                ที่มา: {surahBackground.source} · เนื้อหาบริบทเพื่อประกอบการอ่าน ไม่ใช่คำวินิจฉัยตัฟซีร
              </p>
            </div>
          </details>
        )}

        <details
          className="mushaf-layout"
          open={mushafLayoutOpen}
          onToggle={(event) => setMushafLayoutOpen(event.currentTarget.open)}
        >
          <summary>ผังมุศหัฟ KFGQPC V4 · 15 บรรทัด · 604 หน้า</summary>
          <div className="mushaf-layout-content">
            <div className="mushaf-layout-controls">
              <button
                type="button"
                className="secondary-button"
                disabled={mushafPageNumber <= 1 || mushafLayoutLoading}
                onClick={() => setMushafPageNumber((page) => Math.max(1, page - 1))}
              >
                ← ก่อนหน้า
              </button>
              <label>
                หน้า
                <input
                  type="number"
                  min={1}
                  max={604}
                  value={mushafPageNumber}
                  onChange={(event) => {
                    const page = Number(event.currentTarget.value);
                    if (Number.isInteger(page) && page >= 1 && page <= 604) {
                      setMushafPageNumber(page);
                    }
                  }}
                  aria-label="เลือกหน้ามุศหัฟ"
                />
                / 604
              </label>
              <button
                type="button"
                className="secondary-button"
                disabled={mushafPageNumber >= 604 || mushafLayoutLoading}
                onClick={() => setMushafPageNumber((page) => Math.min(604, page + 1))}
              >
                ถัดไป →
              </button>
            </div>
            {mushafLayoutLoading && <p role="status">กำลังโหลดผังหน้า…</p>}
            {mushafLayoutError && (
              <p className="notice-error" role="status">{mushafLayoutError}</p>
            )}
            {mushafLayout && (
              <>
                <p className="mushaf-layout-note">
                  แสดงเฉพาะตำแหน่งบรรทัดและช่วงอายะฮ์ ไม่แสดง glyph V4 เพราะฟอนต์ยังไม่เผยแพร่
                  · สิทธิ์แสดงผล: {mushafLayout.rights_status}
                </p>
                <ol className="mushaf-layout-lines">
                  {mushafLayout.lines.map((line) => {
                    const surahTitle = line.surah_number
                      ? surahs.find((item) => item.number === line.surah_number)?.name
                      : null;
                    const content =
                      line.line_type === "surah_name"
                        ? `ชื่อซูเราะฮ์${surahTitle ? ` · ${surahTitle}` : ""}`
                        : line.line_type === "basmallah"
                          ? "บิสมิลลาฮ์"
                          : line.verse_keys?.join(" · ") ?? "ตำแหน่งอายะฮ์";
                    return (
                      <li
                        key={`${mushafLayout.page_number}-${line.line_number}`}
                        className={line.is_centered ? "is-centered" : ""}
                      >
                        <span>บรรทัด {line.line_number}</span>
                        <strong dir="auto">{content}</strong>
                      </li>
                    );
                  })}
                </ol>
              </>
            )}
          </div>
        </details>

        {readerError && <p className="notice notice-error" role="alert">{readerError}</p>}
        {translationError && <p className="notice notice-warning" role="status">{translationError} แต่ยังอ่านอาหรับและศึกษาส่วนอื่นได้</p>}
        {audioError && <p className="notice notice-warning" role="status">{audioError}</p>}
        {loadingAyahs && <div className="loading-state"><span className="spinner" /> กำลังโหลดอายะฮ์…</div>}
        {!loadingAyahs && ayahs.length > 0 && (
          <div className="ayah-list">
            {surahNumber !== 1 && surahNumber !== 9 && !firstAyahIncludesBasmala && (
              <div className="basmala" lang="ar" dir="rtl">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
            )}
            {ayahs.map((ayah) => (
              <article
                className={`ayah-row${lastRead?.surahNumber === surahNumber && lastRead.ayahNumber === ayah.numberInSurah ? " is-last-read" : ""}`}
                id={`ayah-${surahNumber}-${ayah.numberInSurah}`}
                key={ayah.number}
              >
                <button
                  type="button"
                  className="ayah-text"
                  lang="ar"
                  dir="rtl"
                  onClick={() => openTafsir(ayah)}
                  aria-label={`เลือกอายะฮ์ ${surahNumber}:${ayah.numberInSurah} เพื่อศึกษาตัฟซีร`}
                >
                  {ayah.text}
                  <span className="ayah-end" aria-hidden="true">
                    <span>{toArabicDigits(ayah.numberInSurah)}</span>
                  </span>
                </button>
                {ayah.words && ayah.words.length > 0 && (
                  <details className="ayah-words">
                    <summary>ดูคำตามตำแหน่ง</summary>
                    <div className="ayah-word-list" lang="ar" dir="rtl">
                      {ayah.words.map((word) => (
                        <span key={word.location} title={word.location}>
                          <small>{toArabicDigits(word.position)}</small> {word.text}
                        </span>
                      ))}
                    </div>
                  </details>
                )}
                <p className="ayah-translation" lang="th">
                  {ayah.translation ?? (translationError ? "ยังไม่มีคำแปลสำหรับอายะฮ์นี้" : "กำลังโหลดคำแปล…")}
                </p>
                <div className="ayah-actions">
                  <button
                    type="button"
                    className="ayah-action"
                    aria-pressed={studyStorage.bookmarks.some(
                      (item) => item.surahNumber === surahNumber && item.ayahNumber === ayah.numberInSurah,
                    )}
                    onClick={() => toggleBookmark(ayah)}
                  >
                    {studyStorage.bookmarks.some(
                      (item) => item.surahNumber === surahNumber && item.ayahNumber === ayah.numberInSurah,
                    ) ? "★ บันทึกแล้ว" : "☆ บันทึก"}
                  </button>
                  <button
                    type="button"
                    className="ayah-action"
                    onClick={() => playAyah(ayah)}
                    disabled={!ayah.audio}
                    aria-label={`${audioAyah?.number === ayah.number && isPlaying ? "หยุด" : "ฟัง"}เสียงอ่านอายะฮ์ ${surahNumber}:${ayah.numberInSurah}`}
                  >
                    {audioAyah?.number === ayah.number && isPlaying ? "Ⅱ หยุด" : "▶ ฟัง"}
                  </button>
                  <button
                    type="button"
                    className="ayah-study"
                    onClick={() => openTafsir(ayah)}
                    aria-label={`ศึกษาอายะฮ์ ${surahNumber}:${ayah.numberInSurah}`}
                  >
                    <span aria-hidden="true">✦</span> ศึกษาตัฟซีร
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
        <div className="source-note">
          <span className="source-note-icon" aria-hidden="true">ⓘ</span>
          <span>
            ข้อความอาหรับและเสียงอ่าน:{" "}
            <a href="https://alquran.cloud/" target="_blank" rel="noreferrer">
              AlQuran.cloud API · Uthmani · อัลอะฟาซี
            </a>
            {" · "}
            คำแปลไทย:{" "}
            <a href="https://api.alquran.cloud/v1/edition/th.thai" target="_blank" rel="noreferrer">
              King Fahad Quran Complex
            </a>
            {" · "}ผังหน้า KFGQPC V4 ใช้ข้อมูล QUL ในเครื่อง · บุ๊กมาร์กและประวัติเก็บในอุปกรณ์นี้
          </span>
        </div>
      </section>

        <aside className="tafsir-panel" aria-label="แผงศึกษาตัฟซีร">
          {selectedAyah ? (
            <section
              className="tafsir-panel-content"
              aria-labelledby="dialog-title"
            >
            <header className="dialog-header">
              <div>
                <span className="section-kicker">AYAH STUDY</span>
                <h2 id="dialog-title">ศึกษาอายะฮ์ {studySurahNumber}:{selectedAyah.numberInSurah}</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                onClick={() => setSelectedAyah(null)}
                aria-label="ปิดหน้าต่าง"
              >×</button>
            </header>

            <div className="dialog-ayah" lang="ar" dir="rtl">{selectedAyah.text}</div>
            <div className="dialog-translation" lang="th">
              <span>คำแปลไทย · King Fahad Quran Complex</span>
              <p>{selectedAyah.translation ?? "ยังไม่มีคำแปลสำหรับอายะฮ์นี้"}</p>
            </div>

            <nav className="study-tabs" aria-label="เนื้อหาการศึกษา">
              <button
                type="button"
                aria-pressed={studyTab === "overview"}
                className={studyTab === "overview" ? "is-active" : ""}
                onClick={() => setStudyTab("overview")}
              >
                ภาพรวม
              </button>
              <button
                type="button"
                aria-pressed={studyTab === "sources"}
                className={studyTab === "sources" ? "is-active" : ""}
                onClick={() => setStudyTab("sources")}
              >
                แหล่งอ้างอิง <span>{citationSources.length}</span>
              </button>
            </nav>

            {studyTab === "overview" ? (
              <>
            <label className="agent-picker">
              <span>เลือกหนังสือตัฟซีร</span>
              <select
                value={selectedAgentKey}
                onChange={(event) => setSelectedAgentKey(event.target.value)}
                disabled={loadingAgents || agents.length === 0}
              >
                {agents.map((agent) => (
                  <option key={agentKey(agent)} value={agentKey(agent)}>
                    {agent.label} · {languageNames[agent.source_language] ?? agent.source_language}
                  </option>
                ))}
              </select>
            </label>

            <div className="comparison-tools">
              <button
                type="button"
                className="secondary-button"
                aria-pressed={compareMode}
                onClick={() => {
                  const enableComparison = !compareMode;
                  setCompareMode(enableComparison);
                  if (enableComparison && selectedAgent?.enabled) {
                    setCompareAgentKeys([agentKey(selectedAgent)]);
                  }
                  setChatError("");
                }}
              >
                {compareMode ? "ปิดโหมดเปรียบเทียบ" : "เปรียบเทียบหลายตำรา"}
              </button>
              <p>เปรียบเทียบแหล่งที่ได้รับอนุญาตทีละเล่ม โดยแยกข้อความและที่มา</p>
            </div>

            {compareMode && (
              <fieldset className="compare-sources">
                <legend>เลือกอย่างน้อย 2 แหล่งที่พร้อมใช้งาน</legend>
                {agents.map((agent) => (
                  <label key={agentKey(agent)} className={!agent.enabled ? "compare-source is-disabled" : "compare-source"}>
                    <input
                      type="checkbox"
                      checked={compareAgentKeys.includes(agentKey(agent))}
                      disabled={!agent.enabled || loadingAgents}
                      onChange={() => toggleCompareAgent(agentKey(agent))}
                    />
                    <span>
                      <strong>{agent.author}</strong>
                      <small>
                        {languageNames[agent.source_language] ?? agent.source_language}
                        {" · "}
                        {agent.enabled
                          ? "พร้อมใช้งาน"
                          : `ยังไม่อนุมัติ (${agent.rights_status})`}
                      </small>
                    </span>
                  </label>
                ))}
              </fieldset>
            )}

            {agentError && <p className="notice notice-error" role="alert">{agentError}</p>}
            {loadingAgents && <div className="inline-loading"><span className="spinner" /> กำลังตรวจสอบแหล่งตัฟซีร…</div>}

            {selectedAgent && !selectedAgent.enabled && (
              <div className="rights-notice" role="status">
                <span className="rights-icon" aria-hidden="true">⌑</span>
                <div>
                  <strong>แหล่งข้อมูลยังไม่พร้อมให้ใช้งาน</strong>
                  <p>
                    {selectedAgent.database_available
                      ? "ต้องตรวจสอบสิทธิ์การแสดงผล การอ้างข้อความ และการประมวลผล AI ของหนังสือเล่มนี้ก่อน"
                      : "ยังไม่พบฐานข้อมูลของหนังสือเล่มนี้ในระบบ"}
                  </p>
                  <small>สถานะสิทธิ์: {rightsStatusLabel(selectedAgent.rights_status)} · ตรวจสอบเนื้อหา: {selectedAgent.verification_status}</small>
                </div>
              </div>
            )}

            <div className="chat-transcript" aria-live="polite">
              {messages.length === 0 && !compareMode && (
                <div className="chat-empty">
                  <span aria-hidden="true">✧</span>
                  <p>เลือกหนังสือ แล้วถามเกี่ยวกับอายะฮ์นี้</p>
                  <small>คำตอบจะอ้างอิงจากข้อความในหนังสือที่เลือก</small>
                </div>
              )}
              {messages.length === 0 && compareMode && (
                <div className="chat-empty">
                  <span aria-hidden="true">✧</span>
                  <p>เลือกอย่างน้อยสองแหล่งที่ผ่านการตรวจสอบสิทธิ์</p>
                  <small>แต่ละแหล่งจะตอบแยกจากกัน ไม่รวมความเห็นเป็นคำตอบเดียว</small>
                </div>
              )}
              {messages.map((message, index) => (
                <div
                  className={`chat-message ${message.role === "user" ? "chat-user" : message.error ? "chat-assistant chat-error" : "chat-assistant"}`}
                  key={`${message.role}-${index}`}
                >
                  {message.role === "assistant" && (
                    <span className="message-label">
                      {message.error ? "ยังตอบจากแหล่งนี้ไม่ได้" : `คำอธิบาย AI · ${message.author ?? "แหล่งตัฟซีร"}`}
                    </span>
                  )}
                  <p>{message.content}</p>
                </div>
              ))}
              {sending && <div className="inline-loading"><span className="spinner" /> กำลังอ่านแหล่งอ้างอิง…</div>}
            </div>

            {chatError && <p className="notice notice-error" role="alert">{chatError}</p>}

            <form className="chat-form" onSubmit={sendMessage}>
              <label className="sr-only" htmlFor="question">พิมพ์คำถาม</label>
              <textarea
                id="question"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={compareMode ? "ถามเพื่อเปรียบเทียบคำอธิบายจากแต่ละตำรา…" : "ถามเกี่ยวกับความหมายหรือคำอธิบาย…"}
                maxLength={2000}
                rows={2}
                disabled={compareMode ? agents.filter((agent) => agent.enabled && compareAgentKeys.includes(agentKey(agent))).length < 2 || sending : !selectedAgent?.enabled || sending}
              />
              <button
                className="send-button"
                type="submit"
                disabled={compareMode ? agents.filter((agent) => agent.enabled && compareAgentKeys.includes(agentKey(agent))).length < 2 || !draft.trim() || sending : !selectedAgent?.enabled || !draft.trim() || sending}
              >
                {sending ? "กำลังส่ง…" : "ส่งคำถาม"} <span aria-hidden="true">↗</span>
              </button>
            </form>

            <p id="panel-disclaimer" className="dialog-disclaimer">
              คำตอบสร้างโดย AI ไม่ใช่คำพูดของอุละมาอ์ และไม่ใช่ฟัตวา
            </p>
              </>
            ) : (
              <section className="citation-list" aria-label="แหล่งอ้างอิงจากคำตอบ">
                {citationSources.length === 0 ? (
                  <div className="chat-empty">
                    <span aria-hidden="true">⌑</span>
                    <p>ยังไม่มีรายการอ้างอิง</p>
                    <small>อ้างอิงจะแสดงเมื่อได้รับคำตอบจากแหล่งที่ได้รับอนุญาต</small>
                  </div>
                ) : (
                  citationSources.map((source, index) => (
                    <article className="source-card" key={`${source.book}-${index}`}>
                      <div className="source-card-heading">
                        <strong>{source.book}</strong>
                        <span>{source.author} · {languageNames[source.language] ?? source.language}</span>
                      </div>
                      <div
                        className="source-original"
                        lang={source.language}
                        dir={source.language === "ar" ? "rtl" : "auto"}
                      >
                        {source.original_text}
                      </div>
                      <div className="source-meta">
                        <span>อายะฮ์ {source.ayah_range}</span>
                        <span>สิทธิ์: {rightsStatusLabel(source.rights_status)}</span>
                        <span>{source.evidence_status}</span>
                        {source.resource_url && (
                          <a href={source.resource_url} target="_blank" rel="noreferrer">
                            ดูแหล่งข้อมูล ↗
                          </a>
                        )}
                      </div>
                    </article>
                  ))
                )}
              </section>
            )}
          </section>
          ) : (
            <div className="tafsir-empty">
              <span className="tafsir-empty-mark" aria-hidden="true">۞</span>
              <span className="section-kicker">AYAH STUDY</span>
              <h2>พื้นที่ศึกษาอายะฮ์</h2>
              <p>เลือกข้อความอายะฮ์จากหน้ามุศหัฟ เพื่ออ่านคำแปลและศึกษาแหล่งตัฟซีรที่ตรวจสอบสิทธิ์แล้ว</p>
              <div className="tafsir-empty-note">
                <strong>หลักการอ้างอิง</strong>
                <span>คำอธิบาย AI และต้นฉบับจากตำราจะแสดงแยกกัน พร้อมสถานะสิทธิ์และที่มา</span>
              </div>
            </div>
          )}
        </aside>
      </div>

      <footer className="page-footer">
        <span>QURAN AI <i>·</i> เครื่องมือศึกษา ไม่ใช่คำวินิจฉัยทางศาสนา</span>
        <span>คำอธิบายที่สร้างโดย AI จะแสดงแยกจากต้นฉบับและระบุแหล่งที่มา</span>
      </footer>
    </main>
  );
}

function agentKey(agent: Agent): string {
  return `${agent.id}:${agent.source_language}`;
}

function toArabicDigits(value: number): string {
  return String(value).replace(/[0-9]/g, (digit) => "٠١٢٣٤٥٦٧٨٩"[Number(digit)]);
}

function rightsStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    approved: "อนุมัติแล้ว",
    pending: "รอตรวจสอบ",
    rejected: "ไม่อนุมัติ",
    unknown: "ไม่ทราบ",
  };
  return labels[status] ?? status;
}
