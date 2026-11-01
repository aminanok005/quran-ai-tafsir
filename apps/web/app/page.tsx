"use client";

import { FormEvent, useMemo, useState } from "react";

type IconName =
  | "book"
  | "bookmark"
  | "chevron"
  | "close"
  | "copy"
  | "dots"
  | "expand"
  | "headphones"
  | "help"
  | "moon"
  | "search"
  | "send"
  | "spark"
  | "sun"
  | "volume"
  | "menu";

const ayahs = [
  { number: 1, text: "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ" },
  { number: 2, text: "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ" },
  { number: 3, text: "الرَّحْمَٰنِ الرَّحِيمِ" },
  { number: 4, text: "مَالِكِ يَوْمِ الدِّينِ" },
  { number: 5, text: "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ" },
  { number: 6, text: "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ" },
  {
    number: 7,
    text: "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
  },
];

const agents = [
  "Al-Sa'di Tafsir Agent",
  "Ibn Kathir Tafsir Agent",
  "Al-Tabari Tafsir Agent",
  "Al-Qurtubi Tafsir Agent",
  "Ibn Ashur Tafsir Agent",
  "Al-Zuhayli Tafsir Agent",
];

function Icon({
  name,
  size = 18,
}: {
  name: IconName;
  size?: number;
}) {
  const shared = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
  };

  const paths: Record<IconName, React.ReactNode> = {
    book: (
      <>
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
        <path d="M4 5.5v16M8 7h8M8 11h7" />
      </>
    ),
    bookmark: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-4-6 4z" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    close: <path d="m18 6-12 12M6 6l12 12" />,
    copy: (
      <>
        <rect x="8" y="8" width="12" height="13" rx="2" />
        <path d="M16 8V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h2" />
      </>
    ),
    dots: (
      <>
        <circle cx="5" cy="12" r="1" />
        <circle cx="12" cy="12" r="1" />
        <circle cx="19" cy="12" r="1" />
      </>
    ),
    expand: (
      <>
        <path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M3 16v3a2 2 0 0 0 2 2h3" />
      </>
    ),
    headphones: (
      <>
        <path d="M3 14v-3a9 9 0 0 1 18 0v3" />
        <path d="M5 14h2a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2ZM17 14h2a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2Z" />
      </>
    ),
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.6 9a2.5 2.5 0 1 1 4.7 1.2c-.7 1.1-2.3 1.3-2.3 3M12 17.5h.01" />
      </>
    ),
    moon: <path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z" />,
    search: (
      <>
        <circle cx="10.8" cy="10.8" r="6.8" />
        <path d="m16 16 4.5 4.5" />
      </>
    ),
    send: (
      <>
        <path d="m21 3-7.5 18-3.8-7.7L2 9.5z" />
        <path d="M21 3 9.7 13.3" />
      </>
    ),
    spark: (
      <>
        <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
        <path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z" />
      </>
    ),
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
      </>
    ),
    volume: (
      <>
        <path d="M11 5 6 9H3v6h3l5 4z" />
        <path d="M15.5 8.5a5 5 0 0 1 0 7m3-10a9 9 0 0 1 0 13" />
      </>
    ),
    menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  };

  return <svg {...shared}>{paths[name]}</svg>;
}

export default function ReaderPage() {
  const [selectedAyah, setSelectedAyah] = useState(1);
  const [query, setQuery] = useState("");
  const [hasAsked, setHasAsked] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "sources">("overview");
  const [agent, setAgent] = useState(agents[0]);
  const [search, setSearch] = useState("");
  const [fontSize, setFontSize] = useState(34);
  const [bookmarks, setBookmarks] = useState<number[]>([]);
  const [darkMode, setDarkMode] = useState(false);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [notice, setNotice] = useState("");

  const visibleAyahs = useMemo(() => {
    const term = search.trim();
    return ayahs.filter((ayah) => !term || ayah.text.includes(term));
  }, [search]);

  const currentAyah = ayahs.find((ayah) => ayah.number === selectedAyah) ?? ayahs[0];
  const reference = `1:${currentAyah.number}`;

  const toggleBookmark = (number: number) => {
    setBookmarks((existing) =>
      existing.includes(number)
        ? existing.filter((item) => item !== number)
        : [...existing, number],
    );
    setNotice(bookmarks.includes(number) ? "นำออกจากรายการบันทึกแล้ว" : "บันทึกอายะฮ์แล้ว");
    window.setTimeout(() => setNotice(""), 2200);
  };

  const copyAyah = async (ayahNumber: number) => {
    const ayah = ayahs.find((item) => item.number === ayahNumber) ?? ayahs[0];
    try {
      await navigator.clipboard.writeText(`${ayah.text}  ۞  1:${ayah.number}`);
      setNotice("คัดลอกอายะฮ์แล้ว");
    } catch {
      setNotice("ไม่สามารถคัดลอกได้ในเบราว์เซอร์นี้");
    }
    window.setTimeout(() => setNotice(""), 2200);
  };

  const askQuestion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) return;
    setHasAsked(true);
    setActiveTab("overview");
  };

  return (
    <main className={`app-shell${darkMode ? " dark-mode" : ""}`}>
      <header className="topbar">
        <button
          className="icon-button mobile-menu"
          aria-label="เปิดเมนู"
          onClick={() => setMobileSidebar((open) => !open)}
        >
          <Icon name={mobileSidebar ? "close" : "menu"} />
        </button>
        <a className="brand" href="#" aria-label="QURAN AI หน้าหลัก">
          <span className="brand-mark"><Icon name="book" size={21} /></span>
          <span className="brand-name">QURAN<span>AI</span></span>
        </a>
        <div className="topbar-center">
          <span className="workspace-label">พื้นที่ศึกษา</span>
          <span className="topbar-divider" />
          <span className="breadcrumb">อัลกุรอาน <Icon name="chevron" size={14} /> อ่านและศึกษา</span>
        </div>
        <div className="topbar-actions">
          <span className="sample-pill"><span /> ตัวอย่างหน้าจอ</span>
          <button
            className="icon-button theme-button"
            aria-label={darkMode ? "ใช้โหมดสว่าง" : "ใช้โหมดมืด"}
            onClick={() => setDarkMode((enabled) => !enabled)}
          >
            <Icon name={darkMode ? "sun" : "moon"} />
          </button>
          <button className="profile-button" aria-label="บัญชีผู้ใช้">น</button>
        </div>
      </header>

      <div className="workspace">
        <aside className={`sidebar${mobileSidebar ? " sidebar-open" : ""}`}>
          <div className="sidebar-heading">
            <span className="eyebrow">ห้องสมุดของฉัน</span>
            <button className="icon-button sidebar-more" aria-label="ตัวเลือกเพิ่มเติม"><Icon name="dots" /></button>
          </div>
          <button className="nav-item nav-item-active">
            <Icon name="book" size={17} />
            <span>อ่านอัลกุรอาน</span>
          </button>
          <button className="nav-item" onClick={() => setNotice(bookmarks.length ? `บันทึกไว้ ${bookmarks.length} อายะฮ์` : "ยังไม่มีอายะฮ์ที่บันทึก")}>
            <Icon name="bookmark" size={17} />
            <span>รายการบันทึก</span>
            <span className="nav-count">{bookmarks.length || "—"}</span>
          </button>
          <div className="sidebar-section">
            <div className="section-title-row">
              <span className="eyebrow">บทอ่านตัวอย่าง</span>
              <span className="section-meta">1 บท</span>
            </div>
            <label className="surah-search">
              <Icon name="search" size={16} />
              <input
                aria-label="ค้นหาอายะฮ์ภาษาอาหรับ"
                placeholder="ค้นหาอายะฮ์ภาษาอาหรับ..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <kbd>/</kbd>
            </label>
            <button className="surah-item surah-item-active" onClick={() => setSelectedAyah(1)}>
              <span className="surah-number">01</span>
              <span className="surah-name-block">
                <span className="surah-name">อัลฟาติฮะฮ์</span>
                <span className="surah-subtitle">Al-Fātiḥah · 7 อายะฮ์</span>
              </span>
              <span className="surah-arabic" lang="ar">الفاتحة</span>
            </button>
            <div className="sidebar-empty-note">
              แสดงอัลฟาติฮะฮ์เพื่อทดลองรูปแบบการอ่าน<br />ยังไม่มีข้อมูลซูเราะฮ์อื่น
            </div>
          </div>
          <div className="reading-plan">
            <div className="plan-icon"><Icon name="spark" size={17} /></div>
            <div className="plan-copy">
              <strong>ตำแหน่งที่กำลังอ่าน</strong>
              <span>อัลฟาติฮะฮ์ · ตัวอย่าง</span>
            </div>
            <span className="plan-progress">{selectedAyah}/7</span>
            <div className="progress-track"><span style={{ width: `${(selectedAyah / ayahs.length) * 100}%` }} /></div>
            <span className="progress-caption">ตำแหน่งอายะฮ์ที่เลือก</span>
          </div>
          <div className="sidebar-footer">
            <button className="nav-item help-item" onClick={() => setNotice("ข้อมูลตัวอย่างนี้ยังไม่ได้เชื่อมต่อบริการ")}>
              <Icon name="help" size={17} /><span>ช่วยเหลือและคู่มือ</span>
            </button>
            <div className="privacy-note"><span className="privacy-dot" /> พื้นที่ศึกษาอย่างรอบคอบ</div>
          </div>
        </aside>

        <section className="reader-column" aria-label="ตัวอ่านอัลกุรอาน">
          <div className="reader-toolbar">
            <div className="reader-location">
              <span className="location-kicker">กำลังอ่าน</span>
              <strong>อัลฟาติฮะฮ์</strong>
              <span className="location-separator">/</span>
              <span className="location-detail">บทที่ 1</span>
            </div>
            <div className="reader-tools">
              <button
                className="tool-button font-control"
                aria-label="ลดขนาดตัวอักษรอาหรับ"
                onClick={() => setFontSize((size) => Math.max(26, size - 2))}
              >A−</button>
              <button
                className="tool-button font-control"
                aria-label="เพิ่มขนาดตัวอักษรอาหรับ"
                onClick={() => setFontSize((size) => Math.min(46, size + 2))}
              >A+</button>
              <span className="tool-divider" />
              <button className="tool-button" aria-label="เสียงอ่านยังไม่พร้อม" onClick={() => setNotice("เสียงอ่านยังไม่พร้อมใช้งานในตัวอย่างนี้")}><Icon name="headphones" size={17} /></button>
              <button className="tool-button" aria-label="ขยายหน้าจอ" onClick={() => setNotice("ปรับขนาดหน้าต่างเพื่ออ่านแบบเต็มจอ")}><Icon name="expand" size={17} /></button>
            </div>
          </div>

          <div className="reader-scroll">
            <div className="surah-intro">
              <div className="surah-intro-kicker"><span className="ornament">✳</span> บทเปิดคัมภีร์ <span className="ornament">✳</span></div>
              <h1 className="surah-title" lang="ar">سُورَةُ الْفَاتِحَةِ</h1>
              <div className="surah-title-thai">ซูเราะฮ์ อัลฟาติฮะฮ์</div>
              <div className="surah-metadata">
                <span>มักกียะฮ์</span><i />
                <span>7 อายะฮ์</span><i />
                <span>ญุซที่ 1</span>
              </div>
              <div className="basmala" lang="ar">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
            </div>

            <div className="reading-source-note">
              <span className="source-note-dot" />
              <span>เนื้อหาอาหรับตัวอย่าง · ยังไม่ได้ดึงจากแหล่งข้อมูล</span>
              <button aria-label="ข้อมูลแหล่งที่มา" onClick={() => setNotice("เชื่อมต่อ Quran API เพื่อใช้ข้อมูลที่ตรวจสอบแหล่งที่มาแล้ว")}><Icon name="help" size={15} /></button>
            </div>

            <div className="ayah-list" style={{ "--arabic-size": `${fontSize}px` } as React.CSSProperties}>
              {visibleAyahs.map((ayah) => {
                const isSelected = selectedAyah === ayah.number;
                const isBookmarked = bookmarks.includes(ayah.number);
                return (
                  <article
                    className={`ayah-card${isSelected ? " ayah-selected" : ""}`}
                    key={ayah.number}
                    onClick={() => {
                      setSelectedAyah(ayah.number);
                      setHasAsked(false);
                    }}
                  >
                    <div className="ayah-card-top">
                      <button
                        className={`ayah-number${isSelected ? " ayah-number-selected" : ""}`}
                        aria-label={`เลือกอายะฮ์ ${ayah.number}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedAyah(ayah.number);
                          setHasAsked(false);
                        }}
                      >
                        <span>{ayah.number.toString().padStart(2, "0")}</span>
                      </button>
                      <div className="ayah-actions">
                        <button className={`ayah-action${isBookmarked ? " action-saved" : ""}`} aria-label={isBookmarked ? "นำออกจากรายการบันทึก" : "บันทึกอายะฮ์"} onClick={(event) => { event.stopPropagation(); toggleBookmark(ayah.number); }}>
                          <Icon name="bookmark" size={16} />
                        </button>
                        <button className="ayah-action" aria-label="คัดลอกอายะฮ์" onClick={(event) => { event.stopPropagation(); void copyAyah(ayah.number); setSelectedAyah(ayah.number); }}>
                          <Icon name="copy" size={16} />
                        </button>
                        <button className="ayah-action" aria-label="เสียงอ่าน" onClick={(event) => { event.stopPropagation(); setNotice("เสียงอ่านยังไม่พร้อมใช้งานในตัวอย่างนี้"); }}>
                          <Icon name="volume" size={16} />
                        </button>
                      </div>
                    </div>
                    <p className="ayah-arabic" lang="ar" dir="rtl">{ayah.text}</p>
                    <div className="translation-placeholder">
                      <span className="translation-icon">ع</span>
                      <span>คำแปลภาษาไทยจะแสดงเมื่อยืนยันแหล่งที่มาแล้ว</span>
                    </div>
                    {isSelected && <div className="selected-context"><span /> กำลังศึกษาอายะฮ์นี้ <span className="context-reference">1:{ayah.number}</span></div>}
                  </article>
                );
              })}
              {visibleAyahs.length === 0 && (
                <div className="search-empty">
                  <Icon name="search" size={20} />
                  <strong>ไม่พบข้อความที่ตรงกัน</strong>
                  <span>ลองค้นหาคำภาษาอาหรับในซูเราะฮ์นี้</span>
                </div>
              )}
            </div>
            <div className="reader-endnote">
              <span className="endnote-line" />
              <span>สิ้นสุดซูเราะฮ์</span>
              <span className="endnote-line" />
            </div>
          </div>
          <div className="reader-bottom">
            <button className="surah-step" disabled><span>ก่อนหน้า</span></button>
            <span className="reading-progress-label">ซูเราะฮ์ที่ 1 จาก 114</span>
            <button className="surah-step" onClick={() => setNotice("ข้อมูลซูเราะฮ์ถัดไปยังไม่พร้อมใช้งาน")}><span>ถัดไป</span><Icon name="chevron" size={15} /></button>
          </div>
        </section>

        <aside className="tafsir-column" aria-label="ผู้ช่วยศึกษาตัฟซีร">
          <div className="tafsir-header">
            <div className="tafsir-title-row">
              <div className="tafsir-icon"><Icon name="spark" size={18} /></div>
              <div>
                <h2>ศึกษาอายะฮ์</h2>
                <span>ผู้ช่วยค้นคว้าตัฟซีร</span>
              </div>
              <button className="icon-button chat-more" aria-label="ตัวเลือกเพิ่มเติม"><Icon name="dots" /></button>
            </div>
            <div className="selected-verse-chip">
              <span className="verse-chip-icon">۞</span>
              <span>อัลฟาติฮะฮ์ · อายะฮ์ {currentAyah.number}</span>
              <span className="chip-reference">{reference}</span>
            </div>
          </div>
          <div className="agent-select-wrap">
            <label htmlFor="agent-select">รูปแบบการค้นคว้า</label>
            <div className="agent-select">
              <span className="agent-avatar">س</span>
              <select id="agent-select" value={agent} onChange={(event) => setAgent(event.target.value)}>
                {agents.map((name) => <option key={name}>{name}</option>)}
              </select>
              <span className="select-chevron"><Icon name="chevron" size={14} /></span>
            </div>
            <span className="agent-note">โปรไฟล์ AI เพื่อการศึกษา ไม่ใช่ตัวแทนของอุละมาอ์</span>
          </div>
          <div className="chat-tabs" role="tablist" aria-label="มุมมองการศึกษา">
            <button role="tab" aria-selected={activeTab === "overview"} className={activeTab === "overview" ? "chat-tab active" : "chat-tab"} onClick={() => setActiveTab("overview")}>ภาพรวม</button>
            <button role="tab" aria-selected={activeTab === "sources"} className={activeTab === "sources" ? "chat-tab active" : "chat-tab"} onClick={() => setActiveTab("sources")}>แหล่งอ้างอิง <span className="tab-count">0</span></button>
          </div>
          <div className="chat-body">
            {activeTab === "overview" ? (
              hasAsked ? (
                <div className="unavailable-card" role="status">
                  <div className="unavailable-icon"><Icon name="help" size={20} /></div>
                  <span className="evidence-label">ยังไม่มีคำตอบ</span>
                  <h3>บริการตัฟซีรยังไม่เชื่อมต่อ</h3>
                  <p>ระบบยังไม่ได้ส่งคำถามไปยัง AI จึงไม่มีคำอธิบายหรือแหล่งอ้างอิงให้แสดง</p>
                  <div className="unavailable-query"><span>คำถามของคุณ</span><p>{query}</p></div>
                  <button className="text-button" onClick={() => { setHasAsked(false); setQuery(""); }}>ล้างคำถาม</button>
                </div>
              ) : (
                <div className="chat-welcome">
                  <div className="welcome-illustration">
                    <div className="welcome-orbit orbit-one" />
                    <div className="welcome-orbit orbit-two" />
                    <div className="welcome-book"><Icon name="book" size={29} /></div>
                    <span className="welcome-star star-one">✳</span>
                    <span className="welcome-star star-two">✦</span>
                  </div>
                  <span className="welcome-eyebrow">อ่านอย่างเข้าใจ</span>
                  <h3>เริ่มต้นค้นคว้า<br />อายะฮ์ที่เลือก</h3>
                  <p>ถามคำถามเกี่ยวกับความหมายหรือบริบท เราจะแสดงสถานะหลักฐานและที่มาอย่างชัดเจน</p>
                  <div className="suggestion-label">คำถามแนะนำ</div>
                  <button className="suggestion" onClick={() => setQuery("ช่วยอธิบายความหมายของอายะฮ์นี้")}>
                    <span>ช่วยอธิบายความหมายของอายะฮ์นี้</span><Icon name="chevron" size={15} />
                  </button>
                  <button className="suggestion" onClick={() => setQuery("มีแหล่งตัฟซีรใดอธิบายอายะฮ์นี้บ้าง")}>
                    <span>มีแหล่งตัฟซีรใดอธิบายอายะฮ์นี้บ้าง</span><Icon name="chevron" size={15} />
                  </button>
                </div>
              )
            ) : (
              <div className="sources-empty">
                <div className="sources-icon"><Icon name="book" size={22} /></div>
                <h3>ยังไม่มีแหล่งอ้างอิง</h3>
                <p>จะแสดงข้อความต้นฉบับ ชื่อหนังสือ เล่ม และหน้า เมื่อมีแหล่งข้อมูลที่ตรวจสอบแล้ว</p>
                <span className="source-status"><span /> ไม่มีแหล่งข้อมูลที่ยืนยันแล้ว</span>
              </div>
            )}
          </div>
          <div className="research-integrity">
            <div className="integrity-icon"><Icon name="help" size={15} /></div>
            <p><strong>ความโปร่งใสสำคัญ</strong> คำอธิบาย AI และข้อความจากแหล่งต้นฉบับจะแยกสถานะให้ชัดเจน</p>
            <button aria-label="อ่านหลักการอ้างอิง" onClick={() => setActiveTab("sources")}><Icon name="chevron" size={14} /></button>
          </div>
          <form className="chat-composer" onSubmit={askQuestion}>
            <label className="sr-only" htmlFor="question">พิมพ์คำถามเกี่ยวกับอายะฮ์</label>
            <textarea
              id="question"
              placeholder="ถามเกี่ยวกับอายะฮ์นี้..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              rows={2}
            />
            <div className="composer-bottom">
              <span><Icon name="spark" size={14} /> AI ยังไม่เชื่อมต่อ</span>
              <button type="submit" className="send-button" aria-label="ส่งคำถาม" disabled={!query.trim()}><Icon name="send" size={16} /></button>
            </div>
            <div className="composer-disclaimer">คำตอบในอนาคตจะอ้างอิงเฉพาะแหล่งข้อมูลที่ตรวจสอบได้</div>
          </form>
        </aside>
      </div>
      {notice && <div className="toast" role="status">{notice}</div>}
    </main>
  );
}
