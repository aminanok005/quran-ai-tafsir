export type ReaderAudioMode =
  "recitation" | "translation" | "recitation-then-translation";
export type ReaderAudioLanguage = "th" | "en" | "id";
export type ReaderTranslationVoiceEngine = "ai" | "device";
export type ReaderAudioSpeed = 0.85 | 1 | 1.15;
export type ReaderAudioPlaybackState = "idle" | "single" | "auto";

export interface ReaderAudioVoice {
  lang: string;
  name?: string;
  voiceURI?: string;
}

export interface ReaderSpeechUtterance {
  text: string;
  lang: string;
  voice: ReaderAudioVoice;
  rate: number;
  onend: (() => void) | null;
  onerror: (() => void) | null;
}

interface ReaderAudioElement {
  src: string;
  currentTime: number;
  playbackRate: number;
  error: { code: number; message?: string | null } | null;
  onended: ((event: Event) => void) | null;
  onerror: ((event: Event) => void) | null;
  play(): Promise<void>;
  pause(): void;
}

interface ReaderSpeechSynthesis {
  getVoices(): ReaderAudioVoice[];
  speak(utterance: ReaderSpeechUtterance): void;
  cancel(): void;
  addEventListener(type: "voiceschanged", listener: () => void): void;
  removeEventListener(type: "voiceschanged", listener: () => void): void;
}

export interface ReaderAudioSequenceOptions {
  surah: number;
  ayah: number;
  ayahNumbers: number[];
  audioByAyah: Record<number, string>;
  mode: ReaderAudioMode;
  language: ReaderAudioLanguage;
  translationVoiceEngine?: ReaderTranslationVoiceEngine;
  speed?: ReaderAudioSpeed;
}

type GeneratedTranslationCacheStatus = "hit" | "miss" | "unknown";

interface ReaderAudioPlaybackDependencies {
  audio: ReaderAudioElement;
  speech: ReaderSpeechSynthesis | null;
  createUtterance(text: string, voice: ReaderAudioVoice): ReaderSpeechUtterance;
  loadTranslations(
    surah: number,
    language: ReaderAudioLanguage,
    signal: AbortSignal,
  ): Promise<Record<number, string>>;
  loadGeneratedTranslationAudio(
    surah: number,
    ayah: number,
    language: ReaderAudioLanguage,
    speed: ReaderAudioSpeed,
    signal: AbortSignal,
  ): Promise<{ url: string; cacheStatus: GeneratedTranslationCacheStatus }>;
  revokeGeneratedAudioUrl(url: string): void;
  onAyahChange(ayah: number): void;
  onStatus(status: string): void;
  onStateChange(state: ReaderAudioPlaybackState): void;
}

class PlaybackCancelled extends Error {}

function languageVoice(
  voices: ReaderAudioVoice[],
  language: ReaderAudioLanguage,
): ReaderAudioVoice | undefined {
  return voices.find(
    (voice) => voice.lang.split("-")[0].toLowerCase() === language,
  );
}

export function createReaderAudioPlayback(
  dependencies: ReaderAudioPlaybackDependencies,
) {
  let generation = 0;
  let activeRequest: AbortController | null = null;
  let activeGeneratedAudioUrl: string | null = null;
  const { audio, speech } = dependencies;

  function releaseActiveGeneratedAudioUrl(): void {
    if (activeGeneratedAudioUrl === null) return;
    const url = activeGeneratedAudioUrl;
    activeGeneratedAudioUrl = null;
    dependencies.revokeGeneratedAudioUrl(url);
  }

  function isCurrent(requestGeneration: number): boolean {
    return generation === requestGeneration;
  }

  function stopCurrent(updateState: boolean): number {
    generation += 1;
    activeRequest?.abort();
    activeRequest = null;
    releaseActiveGeneratedAudioUrl();
    audio.onended = null;
    audio.onerror = null;
    audio.pause();
    audio.currentTime = 0;
    speech?.cancel();
    if (updateState) dependencies.onStateChange("idle");
    return generation;
  }

  function waitForVoice(
    language: ReaderAudioLanguage,
    requestGeneration: number,
    signal: AbortSignal,
    timeoutMs: number,
  ): Promise<ReaderAudioVoice> {
    if (!speech)
      return Promise.reject(new Error("เบราว์เซอร์นี้ไม่รองรับเสียงพูด"));
    const currentVoice = languageVoice(speech.getVoices(), language);
    if (currentVoice) return Promise.resolve(currentVoice);

    return new Promise((resolve, reject) => {
      let timeout: ReturnType<typeof setTimeout>;
      const cleanup = () => {
        clearTimeout(timeout);
        speech.removeEventListener("voiceschanged", handleVoicesChanged);
        signal.removeEventListener("abort", handleAbort);
      };
      const handleVoicesChanged = () => {
        if (!isCurrent(requestGeneration)) return;
        const voice = languageVoice(speech.getVoices(), language);
        if (!voice) return;
        cleanup();
        resolve(voice);
      };
      const handleAbort = () => {
        cleanup();
        reject(new PlaybackCancelled());
      };

      speech.addEventListener("voiceschanged", handleVoicesChanged);
      signal.addEventListener("abort", handleAbort, { once: true });
      timeout = setTimeout(() => {
        cleanup();
        reject(new Error(`ไม่พบเสียงพูดภาษา ${language} ในเบราว์เซอร์`));
      }, timeoutMs);
      if (signal.aborted) handleAbort();
    });
  }

  function playRecitation(
    url: string,
    signal: AbortSignal,
    requestGeneration: number,
  ): Promise<void> {
    if (!url) return Promise.reject(new Error("ไม่มีเสียงอ่านสำหรับอายะฮ์นี้"));
    audio.src = url;
    audio.currentTime = 0;

    return new Promise((resolve, reject) => {
      const cleanup = () => {
        audio.onended = null;
        audio.onerror = null;
        signal.removeEventListener("abort", handleAbort);
      };
      const handleAbort = () => {
        cleanup();
        reject(new PlaybackCancelled());
      };
      audio.onended = () => {
        if (!isCurrent(requestGeneration)) return;
        cleanup();
        resolve();
      };
      audio.onerror = () => {
        if (!isCurrent(requestGeneration)) return;
        cleanup();
        const message = audio.error?.message;
        reject(
          new Error(
            (typeof message === "string" && message.trim()) ||
              "เล่นเสียงอ่านไม่สำเร็จ",
          ),
        );
      };
      signal.addEventListener("abort", handleAbort, { once: true });
      if (signal.aborted) {
        handleAbort();
        return;
      }

      void audio.play().catch((error: unknown) => {
        if (!isCurrent(requestGeneration)) return;
        cleanup();
        reject(
          error instanceof Error ? error : new Error("เล่นเสียงอ่านไม่สำเร็จ"),
        );
      });
    });
  }

  async function playGeneratedTranslation(
    options: ReaderAudioSequenceOptions,
    ayah: number,
    signal: AbortSignal,
    requestGeneration: number,
  ): Promise<void> {
    const speed = options.speed ?? 1;
    dependencies.onStatus(
      `กำลังขอ/สร้างเสียงคำแปลภาษา ${options.language} สำหรับอายะฮ์ ${ayah}`,
    );
    let generated: {
      url: string;
      cacheStatus: GeneratedTranslationCacheStatus;
    };
    try {
      generated = await dependencies.loadGeneratedTranslationAudio(
        options.surah,
        ayah,
        options.language,
        speed,
        signal,
      );
    } catch (error) {
      if (
        error instanceof PlaybackCancelled ||
        signal.aborted ||
        !isCurrent(requestGeneration)
      ) {
        throw new PlaybackCancelled();
      }
      const context =
        error instanceof Error ? error.message : "สร้างเสียงคำแปลไม่สำเร็จ";
      throw new Error(
        `${context} กรุณาลองอีกครั้ง หรือเลือกเสียงพูดจากอุปกรณ์ด้วยตนเอง`,
      );
    }
    if (!isCurrent(requestGeneration) || signal.aborted) {
      dependencies.revokeGeneratedAudioUrl(generated.url);
      throw new PlaybackCancelled();
    }

    activeGeneratedAudioUrl = generated.url;
    if (generated.cacheStatus === "hit") {
      dependencies.onStatus(`พบเสียงคำแปลในแคชสำหรับอายะฮ์ ${ayah}`);
    } else if (generated.cacheStatus === "miss") {
      dependencies.onStatus(
        `ไม่พบเสียงคำแปลในแคช สร้างเสียงใหม่แล้วสำหรับอายะฮ์ ${ayah}`,
      );
    }
    audio.playbackRate = 1;
    dependencies.onStatus(`กำลังเล่นเสียงคำแปลสำหรับอายะฮ์ ${ayah}`);
    try {
      await playRecitation(generated.url, signal, requestGeneration);
    } catch (error) {
      if (
        error instanceof PlaybackCancelled ||
        signal.aborted ||
        !isCurrent(requestGeneration)
      ) {
        throw new PlaybackCancelled();
      }
      const context =
        error instanceof Error ? error.message : "เล่นเสียงคำแปลไม่สำเร็จ";
      throw new Error(
        `${context} กรุณาลองอีกครั้ง หรือเลือกเสียงพูดจากอุปกรณ์ด้วยตนเอง`,
      );
    } finally {
      releaseActiveGeneratedAudioUrl();
    }
  }

  function speakTranslation(
    text: string,
    voice: ReaderAudioVoice,
    signal: AbortSignal,
    requestGeneration: number,
    speed: ReaderAudioSpeed,
  ): Promise<void> {
    if (!speech)
      return Promise.reject(new Error("เบราว์เซอร์นี้ไม่รองรับเสียงพูด"));
    if (!text.trim())
      return Promise.reject(new Error("ไม่มีคำแปลสำหรับอายะฮ์นี้"));
    const utterance = dependencies.createUtterance(text, voice);
    utterance.lang = voice.lang;
    utterance.rate = speed;

    return new Promise((resolve, reject) => {
      const cleanup = () => {
        utterance.onend = null;
        utterance.onerror = null;
        signal.removeEventListener("abort", handleAbort);
      };
      const handleAbort = () => {
        cleanup();
        reject(new PlaybackCancelled());
      };
      utterance.onend = () => {
        if (!isCurrent(requestGeneration)) return;
        cleanup();
        resolve();
      };
      utterance.onerror = () => {
        if (!isCurrent(requestGeneration)) return;
        cleanup();
        reject(new Error("อ่านคำแปลด้วยเสียงไม่สำเร็จ"));
      };
      signal.addEventListener("abort", handleAbort, { once: true });
      if (signal.aborted) {
        handleAbort();
        return;
      }
      speech.speak(utterance);
    });
  }

  async function run(
    options: ReaderAudioSequenceOptions,
    auto: boolean,
  ): Promise<void> {
    const requestGeneration = stopCurrent(false);
    const voiceDeadline = Date.now() + 3000;
    const request = new AbortController();
    activeRequest = request;
    dependencies.onStateChange(auto ? "auto" : "single");
    dependencies.onStatus(
      auto
        ? `เริ่มเล่นต่อเนื่องจากอายะฮ์ ${options.ayah}`
        : `กำลังเล่นอายะฮ์ ${options.ayah}`,
    );

    const ayahs = options.ayahNumbers.filter((ayah) => ayah >= options.ayah);
    if (!ayahs.includes(options.ayah)) ayahs.unshift(options.ayah);
    let completed = false;

    try {
      let translations: Record<number, string> | null = null;
      let voice: ReaderAudioVoice | undefined;
      const translationVoiceEngine = options.translationVoiceEngine ?? "device";
      const speed = options.speed ?? 1;

      for (
        let index = 0;
        index < (auto ? ayahs.length : Math.min(ayahs.length, 1));
        index += 1
      ) {
        if (!isCurrent(requestGeneration)) throw new PlaybackCancelled();
        const ayah = ayahs[index];
        dependencies.onStatus(`กำลังเล่นอายะฮ์ ${ayah}`);
        if (options.mode !== "translation") {
          audio.playbackRate = speed;
          await playRecitation(
            options.audioByAyah[ayah] ?? "",
            request.signal,
            requestGeneration,
          );
        }
        if (options.mode !== "recitation") {
          if (translationVoiceEngine === "ai") {
            await playGeneratedTranslation(
              options,
              ayah,
              request.signal,
              requestGeneration,
            );
          } else {
            dependencies.onStatus(
              `กำลังใช้เสียงพูดจากอุปกรณ์สำหรับคำแปลภาษา ${options.language}`,
            );
            if (!translations) {
              dependencies.onStatus(
                `กำลังโหลดคำแปลภาษา ${options.language} สำหรับอายะฮ์ ${ayah}`,
              );
              translations = await dependencies.loadTranslations(
                options.surah,
                options.language,
                request.signal,
              );
              if (!isCurrent(requestGeneration)) throw new PlaybackCancelled();
            }
            const text = translations[ayah];
            if (!text?.trim()) {
              throw new Error(
                `ไม่มีคำแปลภาษา ${options.language} สำหรับอายะฮ์ ${ayah}`,
              );
            }
            if (!voice)
              voice = await waitForVoice(
                options.language,
                requestGeneration,
                request.signal,
                Math.max(0, voiceDeadline - Date.now()),
              );
            if (!voice) throw new Error("ไม่พบเสียงพูดที่ตรงกับภาษาที่เลือก");
            dependencies.onStatus(
              `กำลังอ่านคำแปลภาษา ${options.language} สำหรับอายะฮ์ ${ayah}`,
            );
            await speakTranslation(
              text,
              voice,
              request.signal,
              requestGeneration,
              speed,
            );
          }
        }
        if (!isCurrent(requestGeneration)) throw new PlaybackCancelled();
        if (auto && index + 1 < ayahs.length) {
          const nextAyah = ayahs[index + 1];
          dependencies.onAyahChange(nextAyah);
        }
      }
      completed = true;
      if (auto) dependencies.onStatus("อ่านต่อเนื่องครบซูเราะฮ์แล้ว");
      else dependencies.onStatus(`เล่นอายะฮ์ ${options.ayah} เสร็จแล้ว`);
    } catch (error) {
      if (error instanceof PlaybackCancelled || !isCurrent(requestGeneration))
        return;
      dependencies.onStatus(
        error instanceof Error ? error.message : "เล่นเสียงไม่สำเร็จ",
      );
    } finally {
      if (isCurrent(requestGeneration)) {
        activeRequest = null;
        audio.onended = null;
        audio.onerror = null;
        audio.pause();
        audio.currentTime = 0;
        releaseActiveGeneratedAudioUrl();
        dependencies.onStateChange("idle");
        if (!completed) speech?.cancel();
      }
    }
  }

  return {
    startSingle: (options: ReaderAudioSequenceOptions) => run(options, false),
    startAuto: (options: ReaderAudioSequenceOptions) => run(options, true),
    stop: () => {
      stopCurrent(true);
      dependencies.onStatus("หยุดการเล่นแล้ว");
    },
    dispose: () => {
      stopCurrent(false);
    },
  };
}
