"use client";

import { useEffect, useState } from "react";

type Surah = {
  id: number;
  name_simple: string;
  name_arabic: string;
  verses_count: number;
};

type Ayah = {
  id: number;
  verse_key: string;
  text_uthmani: string;
};

type ApiCollection<T> = {
  [key: string]: T[] | undefined;
};

const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

function readCollection<T>(
  payload: unknown,
  collectionName: string,
  isItem: (item: unknown) => item is T,
): T[] {
  if (
    typeof payload !== "object" ||
    payload === null ||
    !(collectionName in payload)
  ) {
    throw new Error("ได้รับข้อมูลจาก API ในรูปแบบที่ไม่รู้จัก");
  }

  const collection = (payload as ApiCollection<unknown>)[collectionName];
  if (!Array.isArray(collection) || !collection.every(isItem)) {
    throw new Error("ข้อมูลจาก API ไม่ครบถ้วนหรือไม่ถูกต้อง");
  }
  return collection;
}

function isSurah(item: unknown): item is Surah {
  if (typeof item !== "object" || item === null) return false;
  const value = item as Record<string, unknown>;
  return (
    typeof value.id === "number" &&
    typeof value.name_simple === "string" &&
    typeof value.name_arabic === "string" &&
    typeof value.verses_count === "number"
  );
}

function isAyah(item: unknown): item is Ayah {
  if (typeof item !== "object" || item === null) return false;
  const value = item as Record<string, unknown>;
  return (
    typeof value.id === "number" &&
    typeof value.verse_key === "string" &&
    typeof value.text_uthmani === "string"
  );
}

async function fetchCollection<T>(
  path: string,
  collectionName: string,
  isItem: (item: unknown) => item is T,
  signal: AbortSignal,
): Promise<T[]> {
  const response = await fetch(`${apiBaseUrl}${path}`, { signal });
  if (!response.ok) {
    throw new Error("ไม่สามารถโหลดข้อมูลได้ โปรดลองอีกครั้ง");
  }
  return readCollection(await response.json(), collectionName, isItem);
}

export default function HomePage() {
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [selectedSurah, setSelectedSurah] = useState<number | null>(null);
  const [ayahs, setAyahs] = useState<Ayah[]>([]);
  const [selectedAyah, setSelectedAyah] = useState<string | null>(null);
  const [surahError, setSurahError] = useState<string | null>(null);
  const [ayahError, setAyahError] = useState<string | null>(null);
  const [loadingSurahs, setLoadingSurahs] = useState(true);
  const [loadingAyahs, setLoadingAyahs] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchCollection("/api/v1/surahs", "chapters", isSurah, controller.signal)
      .then((chapters) => {
        setSurahs(chapters);
        setSelectedSurah(chapters[0]?.id ?? null);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setSurahError(
            error instanceof Error ? error.message : "เกิดข้อผิดพลาดในการโหลดซูเราะฮ์",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingSurahs(false);
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (selectedSurah === null) return;

    const controller = new AbortController();
    setLoadingAyahs(true);
    setAyahError(null);
    setAyahs([]);
    setSelectedAyah(null);

    fetchCollection(
      `/api/v1/surahs/${selectedSurah}/ayahs`,
      "verses",
      isAyah,
      controller.signal,
    )
      .then(setAyahs)
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setAyahError(
            error instanceof Error ? error.message : "เกิดข้อผิดพลาดในการโหลดอายะฮ์",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingAyahs(false);
      });

    return () => controller.abort();
  }, [selectedSurah]);

  const selectedAyahData = ayahs.find((ayah) => ayah.verse_key === selectedAyah);

  return (
    <main className="reader-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">QURAN AI</p>
          <h1>อ่านอัลกุรอาน · ศึกษาด้วยหลักฐาน</h1>
        </div>
        <span className="language-badge">ภาษาไทย · النص العربي</span>
      </header>

      <div className="reader-grid">
        <nav className="surah-panel" aria-label="เลือกซูเราะฮ์">
          <h2>ซูเราะฮ์</h2>
          {loadingSurahs && <p role="status">กำลังโหลดรายชื่อซูเราะฮ์…</p>}
          {surahError && (
            <div className="error-box" role="alert">
              <p>{surahError}</p>
              <p>ตรวจสอบว่า Quran AI API กำลังทำงาน แล้วลองโหลดหน้าใหม่</p>
            </div>
          )}
          {!loadingSurahs && !surahError && (
            <label className="surah-select-label">
              เลือกซูเราะฮ์
              <select
                value={selectedSurah ?? ""}
                onChange={(event) => setSelectedSurah(Number(event.target.value))}
              >
                {surahs.map((surah) => (
                  <option key={surah.id} value={surah.id}>
                    {surah.id}. {surah.name_simple} — {surah.name_arabic}
                  </option>
                ))}
              </select>
            </label>
          )}
          {selectedSurah !== null && (
            <p className="muted">
              {surahs.find((surah) => surah.id === selectedSurah)?.verses_count ?? 0} อายะฮ์
            </p>
          )}
        </nav>

        <section className="ayah-panel" aria-label="เนื้อหาอัลกุรอาน">
          <div className="section-heading">
            <div>
              <p className="eyebrow">QURAN READER</p>
              <h2>
                {surahs.find((surah) => surah.id === selectedSurah)?.name_simple ??
                  "กำลังเตรียมข้อมูล"}
              </h2>
            </div>
            <p className="muted">เลือกอายะฮ์เพื่อดูสถานะการศึกษา</p>
          </div>

          {loadingAyahs && <p role="status">กำลังโหลดอายะฮ์…</p>}
          {ayahError && <p className="error-box" role="alert">{ayahError}</p>}
          {!loadingAyahs && !ayahError && (
            <ol className="ayah-list">
              {ayahs.map((ayah) => (
                <li key={ayah.id}>
                  <button
                    className={`ayah-card${selectedAyah === ayah.verse_key ? " selected" : ""}`}
                    type="button"
                    aria-pressed={selectedAyah === ayah.verse_key}
                    onClick={() => setSelectedAyah(ayah.verse_key)}
                  >
                    <span className="ayah-reference">{ayah.verse_key}</span>
                    <span className="arabic-text" lang="ar" dir="rtl">
                      {ayah.text_uthmani}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          )}
        </section>

        <aside className="study-panel" aria-label="ข้อมูลการศึกษา">
          <p className="eyebrow">TAFSIR STUDY</p>
          <h2>ศึกษาอายะฮ์</h2>
          {selectedAyahData ? (
            <>
              <p className="selected-reference">อายะฮ์ {selectedAyahData.verse_key}</p>
              <p className="muted">
                อาหรับจาก Quran.com API · ยังไม่ได้โหลดคำแปลภาษาไทย
              </p>
            </>
          ) : (
            <p className="muted">เลือกอายะฮ์จากรายการเพื่อเริ่มศึกษา</p>
          )}
          <div className="notice-box">
            <strong>Ibn Kathir Tafsir Agent</strong>
            <p>
              ยังไม่พร้อมให้คำอธิบาย: ระบบต้องมีข้อความตัฟซีรที่ได้รับอนุญาต
              และผ่านการตรวจสอบแหล่งที่มาก่อน จึงจะแสดงคำอธิบายและ citation
            </p>
          </div>
          <p className="disclaimer">
            ระบบนี้เป็นเครื่องมือช่วยค้นคว้า ไม่ใช่คำวินิจฉัยทางศาสนา
          </p>
        </aside>
      </div>
    </main>
  );
}
