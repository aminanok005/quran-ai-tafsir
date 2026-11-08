import { useEffect, useId, useRef, useState } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { Play, Settings2, Square, X } from 'lucide-react';
import type {
  ReaderAudioLanguage,
  ReaderAudioMode,
  ReaderAudioPlaybackState,
  ReaderAudioSpeed,
  ReaderTranslationVoiceEngine,
} from '../../lib/quran/reader-audio-playback';

interface ReaderAudioControlsProps {
  mode: ReaderAudioMode;
  language: ReaderAudioLanguage;
  playbackState: ReaderAudioPlaybackState;
  status: string;
  settingsOpen: boolean;
  translationVoiceEngine: ReaderTranslationVoiceEngine;
  speed: ReaderAudioSpeed;
  aiVoiceAvailable: boolean;
  aiVoiceUnavailableReason: string;
  children?: ReactNode;
  listenDisabled?: boolean;
  autoDisabled?: boolean;
  onSettingsOpenChange(open: boolean): void;
  onModeChange(mode: ReaderAudioMode): void;
  onLanguageChange(language: ReaderAudioLanguage): void;
  onTranslationVoiceEngineChange(engine: ReaderTranslationVoiceEngine): void;
  onSpeedChange(speed: ReaderAudioSpeed): void;
  onListen(): void;
  onAuto(): void;
  onStop(): void;
}

const languageLabels: Record<ReaderAudioLanguage, string> = {
  th: 'ภาษาไทย',
  en: 'ภาษาอังกฤษ',
  id: 'ภาษาอินโดนีเซีย',
};

export function ReaderAudioControls({
  mode,
  language,
  playbackState,
  status,
  settingsOpen,
  translationVoiceEngine,
  speed,
  aiVoiceAvailable,
  aiVoiceUnavailableReason,
  children,
  listenDisabled = false,
  autoDisabled = false,
  onSettingsOpenChange,
  onModeChange,
  onLanguageChange,
  onTranslationVoiceEngineChange,
  onSpeedChange,
  onListen,
  onAuto,
  onStop,
}: ReaderAudioControlsProps) {
  const isPlaying = playbackState !== 'idle';
  const isAutoPlaying = playbackState === 'auto';
  const isTranslationMode = mode !== 'recitation';
  const settingsId = useId();
  const settingsTitleId = useId();
  const continuousDescriptionId = useId();
  const [settingsCardWidth, setSettingsCardWidth] = useState<number | null>(null);
  const controlsRef = useRef<HTMLDivElement>(null);
  const settingsDialogRef = useRef<HTMLDivElement>(null);
  const settingsTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!settingsOpen) {
      setSettingsCardWidth(null);
      return;
    }

    const card = controlsRef.current?.closest('.reader-ayah-card');
    if (!card) {
      setSettingsCardWidth(720);
      return;
    }

    const updateCardWidth = () => {
      const width = card.getBoundingClientRect().width;
      setSettingsCardWidth(width || (typeof ResizeObserver === 'undefined' ? 720 : null));
    };
    updateCardWidth();

    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(updateCardWidth);
    observer.observe(card);
    return () => observer.disconnect();
  }, [settingsOpen]);

  useEffect(() => {
    if (!settingsOpen || settingsCardWidth === null || settingsCardWidth >= 720) return;
    const dialog = settingsDialogRef.current;
    if (!dialog || dialog.contains(document.activeElement)) return;
    dialog.querySelector<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    )?.focus();
  }, [settingsOpen, settingsCardWidth]);

  const closeSettings = () => {
    onSettingsOpenChange(false);
    settingsTriggerRef.current?.focus();
  };

  const closeSettingsOnEscape = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Escape') return;
    event.preventDefault();
    event.stopPropagation();
    closeSettings();
  };

  const trapSettingsTab = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Tab' || settingsCardWidth === null || settingsCardWidth >= 720) return;

    const focusableElements = event.currentTarget.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    );
    const first = focusableElements[0];
    const last = focusableElements[focusableElements.length - 1];
    if (!first || !last) {
      event.preventDefault();
      return;
    }

    if (event.shiftKey && (document.activeElement === first || !event.currentTarget.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !event.currentTarget.contains(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  };

  const settingsPanel = settingsOpen && settingsCardWidth !== null ? (
    <div
      ref={settingsDialogRef}
      id={settingsId}
      role="dialog"
      aria-modal={settingsCardWidth < 720 ? true : undefined}
      aria-labelledby={settingsTitleId}
      onKeyDown={trapSettingsTab}
      className="reader-audio-settings-panel"
    >
      <div className="reader-audio-settings-header">
        <h2 id={settingsTitleId} className="text-base font-semibold text-surface-900">ตั้งค่าเสียง</h2>
        <button
          type="button"
          aria-label="ปิดการตั้งค่าเสียง"
          onClick={closeSettings}
          className="reader-audio-settings-close"
        >
          <X aria-hidden="true" size={20} />
        </button>
      </div>
      <div className="reader-audio-settings-fields">
        <label className="reader-audio-setting-field">
          ผู้อ่าน
          <select aria-label="ผู้อ่าน" value="ar.alafasy" disabled>
            <option value="ar.alafasy">อัลอะฟาซี</option>
          </select>
        </label>
        <label className="reader-audio-setting-field">
          รูปแบบการเล่นเสียง
          <select
            aria-label="รูปแบบการเล่นเสียง"
            value={mode}
            onChange={(event) => {
              const selectedMode = event.target.value;
              if (
                selectedMode === 'recitation'
                || selectedMode === 'translation'
                || selectedMode === 'recitation-then-translation'
              ) {
                onModeChange(selectedMode);
              }
            }}
          >
            <option value="recitation">เสียงอ่าน</option>
            <option value="translation">เสียงคำแปล</option>
            <option value="recitation-then-translation">เสียงอ่านและคำแปล</option>
          </select>
        </label>
        {isTranslationMode && (
          <>
            <label className="reader-audio-setting-field">
              ภาษาเสียงแปล
              <select
                aria-label="ภาษาเสียงแปล"
                value={language}
                onChange={(event) => {
                  const selectedLanguage = event.target.value;
                  if (selectedLanguage === 'th' || selectedLanguage === 'en' || selectedLanguage === 'id') {
                    onLanguageChange(selectedLanguage);
                  }
                }}
              >
                <option value="th">ภาษาไทย</option>
                <option value="en">ภาษาอังกฤษ</option>
                <option value="id">ภาษาอินโดนีเซีย</option>
              </select>
            </label>
            <label className="reader-audio-setting-field">
              เสียงแปล
              <select
                aria-label="เสียงแปล"
                value={translationVoiceEngine}
                onChange={(event) => {
                  if (event.target.value === 'device') {
                    onTranslationVoiceEngineChange('device');
                  } else if (event.target.value === 'ai' && aiVoiceAvailable) {
                    onTranslationVoiceEngineChange('ai');
                  }
                }}
              >
                <option value="device">เสียงจากอุปกรณ์</option>
                <option value="ai" disabled={!aiVoiceAvailable}>
                  เสียง AI{aiVoiceAvailable ? '' : ' (ยังไม่พร้อมใช้งาน)'}
                </option>
              </select>
            </label>
            <p className="reader-audio-settings-note">
              {aiVoiceAvailable
                ? 'เสียง AI จะส่งคำแปลฉบับเต็มไปยังผู้ให้บริการเสียงที่ตั้งค่าไว้'
                : aiVoiceUnavailableReason}
            </p>
          </>
        )}
        <label className="reader-audio-setting-field">
          ความเร็วเสียง
          <select
            aria-label="ความเร็วเสียง"
            value={String(speed)}
            onChange={(event) => {
              const selectedSpeed = Number(event.target.value);
              if (selectedSpeed === 0.85 || selectedSpeed === 1 || selectedSpeed === 1.15) {
                onSpeedChange(selectedSpeed);
              }
            }}
          >
            <option value="0.85">0.85x</option>
            <option value="1">1x</option>
            <option value="1.15">1.15x</option>
          </select>
        </label>
      </div>
    </div>
  ) : null;

  const narrowSettingsPortal = settingsCardWidth !== null
    && settingsCardWidth < 720
    && typeof document !== 'undefined'
    ? createPortal(
      <div className="reader-audio-settings-portal">
        <button
          type="button"
          aria-label="ปิดการตั้งค่าเสียง"
          onClick={closeSettings}
          className="reader-audio-settings-backdrop"
        />
        {settingsPanel}
      </div>,
      document.body,
    )
    : null;

  return (
    <div ref={controlsRef} className="reader-audio-controls" onKeyDown={closeSettingsOnEscape}>
      <div role="group" aria-label="การทำงานของอายะฮ์" className="reader-action-grid">
        <div data-reader-action="listen" className="reader-action-listen">
          <button
            type="button"
            aria-pressed={isPlaying}
            disabled={listenDisabled && !isPlaying}
            onClick={isPlaying ? onStop : onListen}
            className="reader-action-button reader-action-primary"
          >
            {isPlaying
              ? <Square aria-hidden="true" size={18} fill="currentColor" />
              : <Play aria-hidden="true" size={18} fill="currentColor" />}
            <span>{isPlaying ? 'หยุด' : 'ฟังเสียง'}</span>
          </button>
        </div>
        {children}
        <div data-reader-action="continuous" className="reader-continuous-control">
          <button
            type="button"
            role="switch"
            aria-label="เล่นต่อเนื่อง"
            aria-checked={isAutoPlaying}
            aria-describedby={continuousDescriptionId}
            disabled={autoDisabled && !isAutoPlaying}
            onClick={isAutoPlaying ? onStop : onAuto}
            className="reader-continuous-switch"
          >
            <span aria-hidden="true" className="reader-continuous-track">
              <span className="reader-continuous-thumb" />
            </span>
            <span className="reader-continuous-label">เล่นต่อเนื่อง</span>
          </button>
          <span id={continuousDescriptionId} className="reader-continuous-description">เล่นอายะฮ์ถัดไปอัตโนมัติ</span>
        </div>
      </div>

      <div className="reader-audio-status-row">
        <span
          role="status"
          aria-live="polite"
          aria-atomic="true"
          title={status}
          className="reader-audio-status-text"
        >
          {status}
        </span>
        <div className="reader-audio-settings-anchor">
          <button
            ref={settingsTriggerRef}
            type="button"
            aria-label="ตั้งค่าเสียง"
            aria-expanded={settingsOpen}
            aria-haspopup="dialog"
            aria-controls={settingsId}
            onClick={() => onSettingsOpenChange(!settingsOpen)}
            className="reader-audio-settings-trigger"
          >
            <Settings2 aria-hidden="true" size={16} />
            <span className="reader-audio-settings-summary">
              ตั้งค่าเสียง · อัลอะฟาซี · {languageLabels[language]} · {speed}x
            </span>
          </button>
          {settingsCardWidth !== null && settingsCardWidth >= 720 && settingsPanel}
        </div>
      </div>
      {narrowSettingsPortal}
    </div>
  );
}
