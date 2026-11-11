import {
  createReaderAudioPlayback,
  ReaderAudioMode,
  ReaderAudioPlaybackState,
  ReaderAudioVoice,
  ReaderSpeechUtterance,
} from "./reader-audio-playback";

class FakeAudio {
  src = "";
  currentTime = 0;
  playbackRate = 1;
  error: { code: number; message?: string | null } | null = null;
  onended: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  play = jest.fn(async () => {});
  pause = jest.fn();

  finish() {
    this.onended?.(new Event("ended"));
  }
}

class FakeSpeech {
  voices: ReaderAudioVoice[] = [];
  listeners = new Set<() => void>();
  utterances: ReaderSpeechUtterance[] = [];
  speak = jest.fn((utterance: ReaderSpeechUtterance) =>
    this.utterances.push(utterance),
  );
  cancel = jest.fn();

  getVoices() {
    return this.voices;
  }

  addEventListener(_type: "voiceschanged", listener: () => void) {
    this.listeners.add(listener);
  }

  removeEventListener(_type: "voiceschanged", listener: () => void) {
    this.listeners.delete(listener);
  }

  emitVoicesChanged() {
    this.listeners.forEach((listener) => listener());
  }
}

function setup(speech: FakeSpeech | null = new FakeSpeech()) {
  const audio = new FakeAudio();
  const onAyahChange = jest.fn();
  const onStatus = jest.fn();
  const onStateChange = jest.fn((_state: ReaderAudioPlaybackState) => {});
  const loadTranslations = jest.fn(
    async (_surah: number, _language: string, _signal: AbortSignal): Promise<Record<number, string>> => ({
      1: "Translation one",
      2: "Translation two",
    }),
  );
  const loadGeneratedTranslationAudio = jest.fn(
    async (
      _surah: number,
      _ayah: number,
      _language: "th" | "en" | "id",
      _speed: 0.85 | 1 | 1.15,
      _signal: AbortSignal,
    ) => ({
      url: "blob:translation",
      cacheStatus: "unknown" as "hit" | "miss" | "unknown",
    }),
  );
  const revokeGeneratedAudioUrl = jest.fn();
  const controller = createReaderAudioPlayback({
    audio,
    speech,
    createUtterance: (text, voice) => ({
      text,
      lang: voice.lang,
      voice,
      rate: 1,
      onend: null,
      onerror: null,
    }),
    loadTranslations,
    loadGeneratedTranslationAudio,
    revokeGeneratedAudioUrl,
    onAyahChange,
    onStatus,
    onStateChange,
  });
  return {
    audio,
    speech,
    controller,
    onAyahChange,
    onStatus,
    onStateChange,
    loadTranslations,
    loadGeneratedTranslationAudio,
    revokeGeneratedAudioUrl,
  };
}

function options(mode: ReaderAudioMode = "recitation") {
  return {
    surah: 1,
    ayah: 1,
    ayahNumbers: [1, 2],
    audioByAyah: { 1: "/audio/1.mp3", 2: "/audio/2.mp3" },
    mode,
    language: "en" as const,
  };
}

describe("Reader audio playback coordinator", () => {
  it("plays the selected recitation ayah and Auto advances only after audio ends", async () => {
    const { audio, controller, onAyahChange, onStateChange } = setup();
    const task = controller.startAuto(options());
    await Promise.resolve();

    expect(audio.src).toBe("/audio/1.mp3");
    expect(audio.play).toHaveBeenCalledTimes(1);
    audio.finish();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();

    expect(onAyahChange).toHaveBeenCalledWith(2);
    expect(audio.src).toBe("/audio/2.mp3");
    expect(audio.play).toHaveBeenCalledTimes(2);
    audio.finish();
    await task;
    expect(onStateChange).toHaveBeenLastCalledWith("idle");
  });

  it("waits for selected translation text and a matching speech voice", async () => {
    const { speech, controller, loadTranslations, onStatus } = setup();
    if (!speech) throw new Error("Expected speech adapter");
    speech.voices = [{ lang: "en-US" }];

    const task = controller.startSingle({
      ...options("translation"),
      language: "en",
    });
    await Promise.resolve();
    await Promise.resolve();

    expect(loadTranslations).toHaveBeenCalledWith(
      1,
      "en",
      expect.any(AbortSignal),
    );
    expect(speech.utterances).toHaveLength(1);
    expect(speech.utterances[0]).toMatchObject({
      text: "Translation one",
      lang: "en-US",
      voice: { lang: "en-US" },
    });
    speech.utterances[0].onend?.();
    await task;
    const statuses = onStatus.mock.calls.map(([status]) => status);
    const loadingStatus = statuses.findIndex((status) =>
      status.includes("กำลังโหลดคำแปลภาษา en"),
    );
    const speakingStatus = statuses.findIndex((status) =>
      status.includes("กำลังอ่านคำแปลภาษา en"),
    );
    expect(loadingStatus).toBeGreaterThanOrEqual(0);
    expect(speakingStatus).toBeGreaterThan(loadingStatus);
  });

  it("plays recitation before its spoken translation in combined mode", async () => {
    const { audio, speech, controller } = setup();
    if (!speech) throw new Error("Expected speech adapter");
    speech.voices = [{ lang: "en-US" }];

    const task = controller.startSingle({
      ...options("recitation-then-translation"),
      language: "en",
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(speech.utterances).toHaveLength(0);

    audio.finish();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(speech.utterances).toHaveLength(1);
    speech.utterances[0].onend?.();
    await task;
  });

  it("reports an unavailable speech adapter instead of silently substituting", async () => {
    const { controller, onStatus, onAyahChange } = setup(null);

    await controller.startAuto({ ...options("translation"), language: "th" });

    expect(onStatus).toHaveBeenCalledWith(expect.stringContaining("เสียงพูด"));
    expect(onAyahChange).not.toHaveBeenCalled();
  });

  it("waits for a matching voice and never uses an unrelated language", async () => {
    const { speech, controller } = setup();
    if (!speech) throw new Error("Expected speech adapter");
    const task = controller.startSingle({
      ...options("translation"),
      language: "th",
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(speech.utterances).toHaveLength(0);

    speech.voices = [{ lang: "th-TH" }];
    speech.emitVoicesChanged();
    await Promise.resolve();
    await Promise.resolve();
    expect(speech.utterances[0]).toMatchObject({
      lang: "th-TH",
      text: "Translation one",
    });
    speech.utterances[0].onend?.();
    await task;
  });

  it("stops with an actionable status when no matching voice appears before the deadline", async () => {
    jest.useFakeTimers();
    try {
      const { controller, onStatus } = setup();
      const task = controller.startSingle({
        ...options("translation"),
        language: "id",
      });
      await Promise.resolve();
      await Promise.resolve();
      await jest.advanceTimersByTimeAsync(3000);
      await task;

      expect(onStatus).toHaveBeenCalledWith(
        expect.stringContaining("ไม่พบเสียงพูดภาษา id"),
      );
    } finally {
      jest.useRealTimers();
    }
  });

  it.each([
    ["undefined", undefined],
    ["null", null],
    ["empty", ""],
    ["whitespace", "   "],
    ["non-string", 42],
  ])(
    "uses actionable generic status without throwing for a %s media error message",
    async (_description, message) => {
      const { audio, controller, onStatus } = setup();
      const task = controller.startSingle({
        ...options("translation"),
        translationVoiceEngine: "ai",
      });
      await Promise.resolve();
      await Promise.resolve();

      audio.error = { code: 4, message: message as string | null };
      expect(() => audio.onerror?.(new Event("error"))).not.toThrow();
      await task;

      expect(onStatus).toHaveBeenCalledWith(
        expect.stringMatching(/เล่นเสียง.*ไม่สำเร็จ/),
      );
      expect(onStatus).toHaveBeenCalledWith(
        expect.stringMatching(/retry|try again|ลองอีกครั้ง/i),
      );
      expect(onStatus).toHaveBeenCalledWith(
        expect.stringMatching(/device voice|เสียง.*อุปกรณ์/i),
      );
      expect(
        onStatus.mock.calls.some(([status]) => status.includes("TypeError")),
      ).toBe(false);
    },
  );

  it("counts the voice timeout from the initial request while translations load", async () => {
    jest.useFakeTimers();
    try {
      const { speech, controller, loadTranslations, onStatus } = setup();
      if (!speech) throw new Error("Expected speech adapter");
      loadTranslations.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve({ 1: "Translation one" }), 2500);
          }),
      );

      let settled = false;
      const task = controller
        .startSingle({
          ...options("translation"),
          language: "id",
        })
        .then(() => {
          settled = true;
        });

      await jest.advanceTimersByTimeAsync(2500);
      expect(settled).toBe(false);
      await jest.advanceTimersByTimeAsync(500);
      const completedByVoiceDeadline = settled;
      await jest.advanceTimersByTimeAsync(2500);
      await task;

      expect(completedByVoiceDeadline).toBe(true);
      expect(onStatus).toHaveBeenCalledWith(
        expect.stringContaining("ไม่พบเสียงพูดภาษา id"),
      );
      expect(jest.getTimerCount()).toBe(0);
      expect(speech.listeners.size).toBe(0);
    } finally {
      jest.useRealTimers();
    }
  });

  it("reports a missing translation and does not advance Auto", async () => {
    const { controller, loadTranslations, onStatus, onAyahChange } = setup();
    loadTranslations.mockResolvedValue({ 1: "", 2: "" });

    await controller.startAuto({ ...options("translation"), language: "en" });

    expect(onStatus).toHaveBeenCalledWith(
      expect.stringContaining("ไม่มีคำแปล"),
    );
    expect(onAyahChange).not.toHaveBeenCalled();
  });

  it("does not advance or speak after the current playback is stopped", async () => {
    const { audio, speech, controller, onAyahChange } = setup();
    if (!speech) throw new Error("Expected speech adapter");
    speech.voices = [{ lang: "en-US" }];

    const task = controller.startAuto({
      ...options("translation"),
      language: "en",
    });
    await Promise.resolve();
    await Promise.resolve();
    const staleEnd = speech.utterances[0].onend;
    controller.stop();
    staleEnd?.();
    await task;

    expect(onAyahChange).not.toHaveBeenCalled();
    expect(speech.cancel).toHaveBeenCalled();
    expect(audio.pause).toHaveBeenCalled();
  });

  it.each(["th", "en", "id"] as const)(
    "loads AI-generated %s audio using the selected language and speed without passing translation text",
    async (language) => {
      const {
        audio,
        speech,
        controller,
        onStatus,
        loadTranslations,
        loadGeneratedTranslationAudio,
        revokeGeneratedAudioUrl,
      } = setup();
      const task = controller.startSingle({
        ...options("translation"),
        language,
        translationVoiceEngine: "ai",
        speed: 1.15,
      });
      await Promise.resolve();
      await Promise.resolve();

      expect(loadGeneratedTranslationAudio).toHaveBeenCalledWith(
        1,
        1,
        language,
        1.15,
        expect.any(AbortSignal),
      );
      expect(onStatus).toHaveBeenCalledWith(
        expect.stringContaining("กำลังขอ/สร้าง"),
      );
      expect(loadTranslations).not.toHaveBeenCalled();
      expect(speech?.speak).not.toHaveBeenCalled();
      expect(audio.src).toBe("blob:translation");
      expect(audio.playbackRate).toBe(1);
      expect(onStatus).toHaveBeenCalledWith(
        expect.stringContaining("กำลังเล่นเสียงคำแปล"),
      );
      audio.finish();
      await task;
      expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
    },
  );

  it.each([
    ["th", "th-TH"],
    ["en", "en-US"],
    ["id", "id-ID"],
  ] as const)(
    "uses the selected rate for %s device speech",
    async (language, voiceLanguage) => {
      const { speech, controller } = setup();
      if (!speech) throw new Error("Expected speech adapter");
      speech.voices = [{ lang: voiceLanguage }];
      const task = controller.startSingle({
        ...options("translation"),
        language,
        translationVoiceEngine: "device",
        speed: 0.85,
      });
      await Promise.resolve();
      await Promise.resolve();

      expect(speech.utterances[0]).toMatchObject({ rate: 0.85 });
      speech.utterances[0].onend?.();
      await task;
    },
  );

  it("applies the selected playback rate to Alafasy before the combined translation", async () => {
    const { audio, speech, controller } = setup();
    if (!speech) throw new Error("Expected speech adapter");
    speech.voices = [{ lang: "en-US" }];
    const task = controller.startSingle({
      ...options("recitation-then-translation"),
      translationVoiceEngine: "device",
      speed: 1.15,
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(audio.playbackRate).toBe(1.15);
    audio.finish();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(speech.utterances).toHaveLength(1);
    speech.utterances[0].onend?.();
    await task;
  });

  it("applies the selected playback rate to Alafasy in recitation-only mode", async () => {
    const { audio, controller } = setup();
    const task = controller.startSingle({
      ...options("recitation"),
      speed: 1.15,
    });
    await Promise.resolve();

    expect(audio.playbackRate).toBe(1.15);
    audio.finish();
    await task;
  });

  it("does not advance Auto while generated translation audio is still playing", async () => {
    const { audio, controller, onAyahChange } = setup();
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(onAyahChange).not.toHaveBeenCalled();
    audio.finish();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    expect(onAyahChange).toHaveBeenCalledWith(2);
    expect(audio.src).toBe("blob:translation");
    audio.finish();
    await task;
  });

  it("revokes each URL once across repeated AI auto playback", async () => {
    const urls = Array.from(
      { length: 10 },
      (_, index) => `blob:translation-${index + 1}`,
    );
    const {
      audio,
      controller,
      onStatus,
      loadGeneratedTranslationAudio,
      revokeGeneratedAudioUrl,
    } = setup();
    loadGeneratedTranslationAudio.mockImplementation(
      async (_surah, ayah) => ({
        url: urls[ayah - 1],
        cacheStatus: "unknown",
      }),
    );
    const task = controller.startAuto({
      ...options("translation"),
      ayahNumbers: urls.map((_, index) => index + 1),
      translationVoiceEngine: "ai",
    });

    for (let index = 0; index < urls.length; index += 1) {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
      expect(audio.src).toBe(urls[index]);
      audio.finish();
    }
    await task;

    expect(audio.play).toHaveBeenCalledTimes(urls.length);
    expect(revokeGeneratedAudioUrl.mock.calls.map(([url]) => url)).toEqual(urls);
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledTimes(urls.length);
    expect(onStatus).toHaveBeenCalledWith("อ่านต่อเนื่องครบซูเราะฮ์แล้ว");
  });

  it("prefetches the next ayah's generated audio while the current one plays", async () => {
    const { audio, controller, loadGeneratedTranslationAudio, revokeGeneratedAudioUrl } = setup();
    loadGeneratedTranslationAudio.mockImplementation(async (_s, ayah) => ({
      url: `blob:t-${ayah}`,
      cacheStatus: "unknown",
    }));
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    for (let i = 0; i < 6; i += 1) await Promise.resolve();

    expect(audio.src).toBe("blob:t-1");
    expect(loadGeneratedTranslationAudio.mock.calls.map((c) => c[1])).toEqual([1, 2]);
    audio.finish();
    for (let i = 0; i < 6; i += 1) await Promise.resolve();
    expect(audio.src).toBe("blob:t-2");
    audio.finish();
    await task;
    expect(loadGeneratedTranslationAudio).toHaveBeenCalledTimes(2);
    expect(revokeGeneratedAudioUrl.mock.calls.map(([u]) => u)).toEqual(["blob:t-1", "blob:t-2"]);
  });

  it("revokes an unused prefetched URL when playback is stopped", async () => {
    const { audio, controller, loadGeneratedTranslationAudio, revokeGeneratedAudioUrl } = setup();
    loadGeneratedTranslationAudio.mockImplementation(async (_s, ayah) => ({
      url: `blob:t-${ayah}`,
      cacheStatus: "unknown",
    }));
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    for (let i = 0; i < 6; i += 1) await Promise.resolve();
    expect(audio.src).toBe("blob:t-1");
    controller.stop();
    await task;
    for (let i = 0; i < 4; i += 1) await Promise.resolve();

    expect(revokeGeneratedAudioUrl.mock.calls.map(([u]) => u).sort()).toEqual(["blob:t-1", "blob:t-2"]);
  });

  it("reports generated-audio play rejection without advancing or falling back to device speech", async () => {
    const {
      audio,
      speech,
      controller,
      onStatus,
      onAyahChange,
      revokeGeneratedAudioUrl,
    } = setup();
    audio.play.mockRejectedValueOnce(new Error("Playback blocked"));

    await controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });

    expect(audio.src).toBe("blob:translation");
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringContaining("Playback blocked"),
    );
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/retry|try again|ลองอีกครั้ง/i),
    );
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/device voice|เสียง.*อุปกรณ์/i),
    );
    expect(onAyahChange).not.toHaveBeenCalled();
    expect(speech?.speak).not.toHaveBeenCalled();
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
  });

  it("reports generated-audio media errors with retry guidance without advancing or falling back", async () => {
    const {
      audio,
      speech,
      controller,
      onStatus,
      onAyahChange,
      revokeGeneratedAudioUrl,
    } = setup();
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();

    audio.error = { code: 4, message: "Unsupported audio format" };
    audio.onerror?.(new Event("error"));
    await task;

    expect(
      onStatus.mock.calls.some(
        ([status]) =>
          status.includes("Unsupported audio format") &&
          /retry|try again|ลองอีกครั้ง/i.test(status) &&
          /device voice|เสียง.*อุปกรณ์/i.test(status),
      ),
    ).toBe(true);
    expect(onAyahChange).not.toHaveBeenCalled();
    expect(speech?.speak).not.toHaveBeenCalled();
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
  });

  it("reports AI generation cache status and never falls back to device speech on failure", async () => {
    const {
      audio,
      speech,
      controller,
      onStatus,
      onAyahChange,
      loadGeneratedTranslationAudio,
      revokeGeneratedAudioUrl,
    } = setup();
    loadGeneratedTranslationAudio.mockResolvedValueOnce({
      url: "blob:cached",
      cacheStatus: "hit",
    });
    loadGeneratedTranslationAudio.mockRejectedValueOnce(
      new Error("AI audio unavailable"),
    );

    const first = controller.startSingle({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(onStatus).toHaveBeenCalledWith(expect.stringMatching(/cache|แคช/i));
    audio.finish();
    await first;
    expect(audio.src).toBe("blob:cached");
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:cached");

    const second = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await second;
    expect(speech?.speak).not.toHaveBeenCalled();
    expect(onAyahChange).not.toHaveBeenCalled();
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringContaining("AI audio unavailable"),
    );
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/retry|try again|ลองอีกครั้ง/i),
    );
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/device voice|เสียง.*อุปกรณ์/i),
    );
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledTimes(1);
  });

  it("reports a cache miss and selected device voice status", async () => {
    const {
      audio,
      speech,
      controller,
      onStatus,
      loadGeneratedTranslationAudio,
    } = setup();
    loadGeneratedTranslationAudio.mockResolvedValueOnce({
      url: "blob:miss",
      cacheStatus: "miss",
    });
    const aiTask = controller.startSingle({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/ไม่พบ.*แคช|cache miss/i),
    );
    audio.finish();
    await aiTask;

    if (!speech) throw new Error("Expected speech adapter");
    speech.voices = [{ lang: "en-US" }];
    const deviceTask = controller.startSingle({
      ...options("translation"),
      translationVoiceEngine: "device",
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(onStatus).toHaveBeenCalledWith(
      expect.stringMatching(/เสียง.*อุปกรณ์|device voice/i),
    );
    speech.utterances.at(-1)?.onend?.();
    await deviceTask;
  });

  it("aborts generated-audio requests on stop and revokes URLs returned after cancellation", async () => {
    let resolveAudio:
      | ((result: {
          url: string;
          cacheStatus: "hit" | "miss" | "unknown";
        }) => void)
      | undefined;
    let requestSignal: AbortSignal | undefined;
    const {
      controller,
      loadGeneratedTranslationAudio,
      revokeGeneratedAudioUrl,
      onAyahChange,
    } = setup();
    loadGeneratedTranslationAudio.mockImplementationOnce(
      (_surah, _ayah, _language, _speed, signal) => {
        requestSignal = signal;
        return new Promise((resolve) => {
          resolveAudio = resolve;
        });
      },
    );
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();

    controller.stop();
    expect(requestSignal?.aborted).toBe(true);
    resolveAudio?.({ url: "blob:late", cacheStatus: "miss" });
    await task;
    await Promise.resolve();

    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:late");
    expect(onAyahChange).not.toHaveBeenCalled();
  });

  it("revokes generated URLs on playback error and ignores stale completion callbacks", async () => {
    const {
      audio,
      controller,
      revokeGeneratedAudioUrl,
      onAyahChange,
      loadGeneratedTranslationAudio,
    } = setup();
    const first = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();
    const staleEnd = audio.onended;
    controller.stop();
    staleEnd?.(new Event("ended"));
    await first;
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
    expect(onAyahChange).not.toHaveBeenCalled();

    loadGeneratedTranslationAudio.mockResolvedValueOnce({
      url: "blob:error",
      cacheStatus: "miss",
    });
    const second = controller.startSingle({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();
    audio.onerror?.(new Event("error"));
    await second;
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:error");
  });

  it("aborts replaced settings, revokes stale late URLs and the replacement URL exactly once", async () => {
    let resolveOld:
      | ((result: {
          url: string;
          cacheStatus: "hit" | "miss" | "unknown";
        }) => void)
      | undefined;
    let oldSignal: AbortSignal | undefined;
    const {
      audio,
      controller,
      loadGeneratedTranslationAudio,
      revokeGeneratedAudioUrl,
    } = setup();
    loadGeneratedTranslationAudio.mockImplementationOnce(
      (_surah, _ayah, _language, _speed, signal) => {
        oldSignal = signal;
        return new Promise((resolve) => {
          resolveOld = resolve;
        });
      },
    );
    const oldTask = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
      speed: 0.85,
    });
    await Promise.resolve();
    await Promise.resolve();

    const newTask = controller.startSingle({
      ...options("translation"),
      translationVoiceEngine: "ai",
      speed: 1.15,
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(oldSignal?.aborted).toBe(true);
    resolveOld?.({ url: "blob:stale", cacheStatus: "miss" });
    await oldTask;
    await Promise.resolve();
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:stale");

    audio.finish();
    await newTask;
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledTimes(2);
  });

  it("revokes an active generated URL on dispose and ignores its late audio callback", async () => {
    const { audio, controller, revokeGeneratedAudioUrl, onAyahChange } =
      setup();
    const task = controller.startAuto({
      ...options("translation"),
      translationVoiceEngine: "ai",
    });
    await Promise.resolve();
    await Promise.resolve();
    const staleEnd = audio.onended;
    controller.dispose();
    staleEnd?.(new Event("ended"));
    await task;

    expect(revokeGeneratedAudioUrl).toHaveBeenCalledWith("blob:translation");
    // active URL plus the prefetched next-ayah URL, each exactly once
    expect(revokeGeneratedAudioUrl).toHaveBeenCalledTimes(2);
    expect(onAyahChange).not.toHaveBeenCalled();
  });
});
