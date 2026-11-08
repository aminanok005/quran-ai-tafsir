import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from './page';
import { apiClient, AgentAnalysisResponse, StudyNote, SuggestedFollowUp } from '../src/lib/api/client';

const mockQuranOnlyArtifact = {
  kind: 'audio' as const,
  artifact: {
    title: 'Saved audio',
    summary: 'A generated overview.',
    content: {
      segments: [
        { host: 'Host A' as const, text: 'คำอธิบายช่วงที่หนึ่ง' },
        { host: 'Host B' as const, text: 'คำอธิบายช่วงที่สอง' },
        { host: 'Host A' as const, text: 'คำอธิบายช่วงที่สาม' },
        { host: 'Host B' as const, text: 'คำอธิบายช่วงที่สี่' },
      ],
    },
  },
  sources: [{ id: 'quran', label: 'Quran 1:1', url: 'https://quran.com/1/1' }],
  evidence_status: 'AI-SYNTHESIS' as const,
};

const mockTafsirArtifact = {
  ...mockQuranOnlyArtifact,
  sources: [
    ...mockQuranOnlyArtifact.sources,
    {
      id: 'tafsir-91',
      label: 'Tafsir Ibn Kathir',
      url: 'https://quran.com/tafsirs/91',
    },
  ],
};
const originalCreateObjectURLDescriptor = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
const originalRevokeObjectURLDescriptor = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL');
const originalSpeechSynthesisDescriptor = Object.getOwnPropertyDescriptor(window, 'speechSynthesis');
const originalSpeechUtteranceDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'SpeechSynthesisUtterance');

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  useSearchParams: () => new URLSearchParams('view=reader'),
}));

jest.mock('../src/components/ui/fonts', () => ({
  amiriQuran: { className: 'mock-amiri', style: { fontFamily: 'serif' } },
  notoSansThai: { className: 'mock-thai' },
}));

jest.mock('react-resizable-panels', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  return {
    PanelGroup: ({
      children,
      onLayout,
    }: {
      children: React.ReactNode;
      onLayout: (sizes: number[]) => void;
    }) => React.createElement(
      'div',
      { 'data-testid': 'panel-group' },
      React.createElement('button', {
        type: 'button',
        onClick: () => onLayout([30, 45, 25]),
      }, 'Set test panel sizes'),
      children,
    ),
    Panel: ({
      children,
      id,
      defaultSize,
    }: {
      children: React.ReactNode;
      id: string;
      defaultSize: number;
    }) => React.createElement(
      'div',
      { 'data-panel': id, 'data-default-size': String(defaultSize) },
      children,
    ),
    PanelResizeHandle: () => null,
  };
});

jest.mock('../src/components/workspace/WorkspacePanels', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  return {
    SourcesPanel: () => React.createElement(
      'section',
      { 'data-testid': 'sources-panel' },
      'Sources workspace',
    ),
    StudioPanel: ({
      context,
      onSaveTargetArtifact,
    }: {
      context: unknown;
      onSaveTargetArtifact: (artifact: typeof mockQuranOnlyArtifact, context: unknown) => Promise<void>;
    }) => React.createElement(
      'section',
      { 'data-testid': 'studio-panel' },
      React.createElement('button', {
        type: 'button',
        onClick: () => void onSaveTargetArtifact(mockTafsirArtifact, context),
      }, 'Save Quran and Tafsir note'),
      React.createElement('button', {
        type: 'button',
        onClick: () => void onSaveTargetArtifact(mockQuranOnlyArtifact, context),
      }, 'Save Quran only note'),
    ),
  };
});

const originalFetchDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'fetch');
let localQuranPaths: string[] = [];

function localQuranResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Service Unavailable',
    json: async () => body,
  } as Response;
}

function defaultLocalQuranBody(path: string): unknown {
  return path === '/api/quran/surahs/'
    ? [{ number: 1, name_th: 'Al-Fatihah', verses_count: 7 }]
    : path.includes('/ayahs/')
      ? [{ number: 1, numberInSurah: 1, text_uthmani: 'Arabic verse', page_number: 1 }]
      : path.includes('edition=th.thai')
        ? [{ number: 1, numberInSurah: 1, text: 'Thai translation' }]
        : path.includes('edition=en.sahih')
          ? [{ number: 1, numberInSurah: 1, text: 'English translation' }]
          : path.includes('edition=id.indonesian')
            ? [{ number: 1, numberInSurah: 1, text: 'Terjemahan Indonesia' }]
        : path.includes('edition=ar.alafasy')
          ? [{ number: 1, numberInSurah: 1, audio: 'https://audio.example/1.mp3' }]
          : [];
}

function installLocalQuranFetch(
  respond: (path: string) => Response | Promise<Response> = (path) =>
    localQuranResponse(defaultLocalQuranBody(path)),
) {
  const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
    const path = String(input);
    localQuranPaths.push(path);
    return respond(path);
  });
  Object.defineProperty(globalThis, 'fetch', {
    configurable: true,
    writable: true,
    value: fetchMock,
  });
  return fetchMock;
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <Home />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
}

beforeEach(() => {
  window.localStorage.clear();
  localQuranPaths = [];
  installLocalQuranFetch();
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    value: jest.fn(() => 'blob:translation-audio'),
  });
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    value: jest.fn(),
  });
  jest.spyOn(apiClient, 'getTranslationAudioCapabilities').mockResolvedValue({
    available: false,
    supported_languages: [],
    enabled_editions: [],
  });
  jest.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  jest.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
  jest.spyOn(apiClient, 'getTafsirPassage').mockResolvedValue({
    data: { translation_allowed: false, thai_translation: 'คำแปลตัฟซีร' },
  });
});

afterEach(() => {
  cleanup();
  jest.restoreAllMocks();
  if (originalCreateObjectURLDescriptor) {
    Object.defineProperty(URL, 'createObjectURL', originalCreateObjectURLDescriptor);
  } else {
    Reflect.deleteProperty(URL, 'createObjectURL');
  }
  if (originalRevokeObjectURLDescriptor) {
    Object.defineProperty(URL, 'revokeObjectURL', originalRevokeObjectURLDescriptor);
  } else {
    Reflect.deleteProperty(URL, 'revokeObjectURL');
  }
  if (originalSpeechSynthesisDescriptor) {
    Object.defineProperty(window, 'speechSynthesis', originalSpeechSynthesisDescriptor);
  } else {
    Reflect.deleteProperty(window, 'speechSynthesis');
  }
  if (originalSpeechUtteranceDescriptor) {
    Object.defineProperty(globalThis, 'SpeechSynthesisUtterance', originalSpeechUtteranceDescriptor);
  } else {
    Reflect.deleteProperty(globalThis, 'SpeechSynthesisUtterance');
  }
  window.localStorage.clear();
  if (originalFetchDescriptor) Object.defineProperty(globalThis, 'fetch', originalFetchDescriptor);
  else Reflect.deleteProperty(globalThis, 'fetch');
});

describe('workspace page integration', () => {
  it('keeps each answer suggestions and separately cited batch responses in dialogue history', async () => {
    const makeOutput = (explanation: string, url: string) => ({
      explanation,
      evidence_level: 'SOURCE-ATTRIBUTED',
      citations: [{
        passage_id: url,
        evidence_status: 'SOURCE-ATTRIBUTED',
        reference: { book: 'Approved source', scholar: 'Scholar', url },
      }],
    });
    const makeAnswer = (
      messageId: string,
      agentOutputs: Record<string, ReturnType<typeof makeOutput>>,
      sections?: NonNullable<AgentAnalysisResponse['data']['sections']>,
    ): AgentAnalysisResponse => ({
      success: true,
      data: {
        ayah_id: '1:1',
        agents_executed: ['ibn_kathir'],
        agent_outputs: agentOutputs,
        evidence_summary: {
          total_sources: 1,
          verified_sources: 1,
          unverified_sources: 0,
          ai_synthesis: 0,
        },
        session_id: 'session-one',
        message_id: messageId,
        followups_available: true,
        ...(sections ? { sections } : {}),
      },
    });
    const suggestions: SuggestedFollowUp[] = [
      {
        id: 'follow-up-one',
        category: 'deepen',
        title: 'How does the first view approach this topic?',
        prompt: 'Explain the first selected approach.',
        basisCount: 1,
        evidence: 'SOURCE_ATTRIBUTED',
      },
      {
        id: 'follow-up-two',
        category: 'compare',
        title: 'How do the two views differ?',
        prompt: 'Compare the two selected approaches.',
        basisCount: 2,
        evidence: 'SOURCE_ATTRIBUTED',
      },
    ];
    const getExplanation = jest.spyOn(apiClient, 'getAgentExplanation')
      .mockResolvedValueOnce(makeAnswer('message-one', {
        ibn_kathir: makeOutput('Initial answer', 'https://source.example/initial'),
      }))
      .mockResolvedValueOnce(makeAnswer('message-two', {}, [
        {
          question: 'Explain the first selected approach.',
          ayah_id: '1:1',
          agents_executed: ['ibn_kathir'],
          agent_outputs: {
            ibn_kathir: makeOutput('First answer', 'https://source.example/first'),
          },
        },
        {
          question: 'Compare the two selected approaches.',
          ayah_id: '1:1',
          agents_executed: ['ibn_kathir'],
          agent_outputs: {
            ibn_kathir: makeOutput('Second answer', 'https://source.example/second'),
          },
        },
      ]));
    const getSuggestions = jest.spyOn(apiClient, 'getChatSuggestions')
      .mockResolvedValueOnce({ suggestions })
      .mockResolvedValueOnce({ suggestions: [] });
    const page = renderPage();
    await screen.findAllByText('Thai translation');
    fireEvent.click(screen.getAllByRole('button', { name: 'ถาม AI' })[0]);

    fireEvent.change(screen.getAllByLabelText('คำถามเกี่ยวกับอายะฮ์')[0], {
      target: { value: 'Initial question' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'ถาม' })[0]);
    expect(await screen.findAllByText('Initial answer')).toHaveLength(2);
    expect(await screen.findAllByRole('button', { name: /How does the first view/ })).toHaveLength(2);
    expect(getExplanation).toHaveBeenNthCalledWith(
      1,
      1,
      1,
      'ibn_kathir',
      'Initial question',
      { sessionId: expect.any(String) },
    );
    expect(getSuggestions).toHaveBeenNthCalledWith(1, 'session-one', 'message-one');

    fireEvent.click(screen.getAllByRole('button', { name: /How does the first view/ })[0]);
    fireEvent.click(screen.getAllByRole('button', { name: /How do the two views differ/ })[0]);
    fireEvent.click(screen.getAllByRole('button', { name: 'ถามข้อที่เลือก (2)' })[0]);

    expect(await screen.findAllByText('ข้อ 1: Explain the first selected approach.')).toHaveLength(2);
    expect(screen.getAllByText('ข้อ 2: Compare the two selected approaches.')).toHaveLength(2);
    expect(screen.getAllByRole('link', { name: /Scholar · Approved source/ }).slice(0, 3).map((link) => link.getAttribute('href')))
      .toEqual(['https://source.example/initial', 'https://source.example/first', 'https://source.example/second']);
    expect(getExplanation).toHaveBeenNthCalledWith(
      2,
      1,
      1,
      'ibn_kathir',
      '1. Explain the first selected approach.\n2. Compare the two selected approaches.',
      {
        sessionId: 'session-one',
        subquestions: [
          'Explain the first selected approach.',
          'Compare the two selected approaches.',
        ],
      },
    );
    expect(getSuggestions).toHaveBeenNthCalledWith(2, 'session-one', 'message-two');
    expect(screen.getAllByText('Initial answer')).toHaveLength(2);
    page.queryClient.clear();
  });

  it('announces Quran loading until the ayah request resolves', async () => {
    let resolveAyahRequest: ((response: Response) => void) | undefined;
    const pendingAyahRequest = new Promise<Response>((resolve) => {
      resolveAyahRequest = resolve;
    });
    installLocalQuranFetch((path) =>
      path.includes('/ayahs/')
        ? pendingAyahRequest
        : localQuranResponse(defaultLocalQuranBody(path)),
    );

    const page = renderPage();
    expect(await screen.findAllByRole('status', { name: 'กำลังโหลดอายะฮ์' })).toHaveLength(2);
    expect(screen.queryByText('ไม่พบข้อมูลอายะฮ์นี้')).toBeNull();

    if (!resolveAyahRequest) throw new Error('Ayah request resolver was not initialized');
    await act(async () => {
      resolveAyahRequest?.(localQuranResponse(defaultLocalQuranBody('/ayahs/')));
    });
    expect(await screen.findAllByText('Arabic verse')).toHaveLength(2);
    page.queryClient.clear();
  });

  it.each([
    ['missing verse collection', {}],
    ['null verse collection', { ayahs: null }],
    ['malformed verse collection', { ayahs: {} }],
    ['non-record verse item', [null]],
  ])('shows a Quran data error for %s instead of an empty state', async (_label, body) => {
    installLocalQuranFetch((path) =>
      path.includes('/ayahs/')
        ? localQuranResponse(body)
        : localQuranResponse(defaultLocalQuranBody(path)),
    );

    const page = renderPage();
    expect(await screen.findAllByRole('alert')).toHaveLength(2);
    expect(screen.queryByText('ไม่พบข้อมูลอายะฮ์นี้')).toBeNull();
    page.queryClient.clear();
  });

  it.each([
    ['empty array', []],
    ['empty supported envelope', { ayahs: [] }],
  ])('shows an empty state for a successful %s', async (_label, body) => {
    installLocalQuranFetch((path) =>
      path.includes('/ayahs/')
        ? localQuranResponse(body)
        : localQuranResponse(defaultLocalQuranBody(path)),
    );

    const page = renderPage();
    expect(await screen.findAllByText('ไม่พบข้อมูลอายะฮ์นี้')).toHaveLength(2);
    expect(screen.queryByRole('alert')).toBeNull();
    page.queryClient.clear();
  });

  it('shows an error instead of an empty state when the Quran dataset is unavailable', async () => {
    installLocalQuranFetch((path) =>
      path.includes('/ayahs/')
        ? localQuranResponse({ detail: 'ไม่พบข้อมูลซูเราะฮ์นี้ใน QPC dataset' }, 404)
        : localQuranResponse(defaultLocalQuranBody(path)),
    );

    const page = renderPage();
    expect(await screen.findAllByRole('alert')).toHaveLength(2);
    expect(screen.queryByText('ไม่พบข้อมูลอายะฮ์นี้')).toBeNull();
    page.queryClient.clear();
  });

  it('retries a failed Quran request and shows the selected ayah after success', async () => {
    let ayahRequestCount = 0;
    installLocalQuranFetch((path) => {
      if (!path.includes('/ayahs/')) {
        return localQuranResponse(defaultLocalQuranBody(path));
      }
      ayahRequestCount += 1;
      return ayahRequestCount === 1
        ? localQuranResponse({ detail: 'Quran service temporarily unavailable' }, 503)
        : localQuranResponse(defaultLocalQuranBody(path));
    });

    const page = renderPage();
    expect(await screen.findAllByRole('alert')).toHaveLength(2);
    fireEvent.click(screen.getAllByRole('button', { name: 'ลองโหลดอีกครั้ง' })[0]);

    expect(await screen.findAllByText('Arabic verse')).toHaveLength(2);
    expect(ayahRequestCount).toBe(2);
    page.queryClient.clear();
  });

  it('persists and restores resized panel layout and visibility', async () => {
    const firstRender = renderPage();
    await screen.findAllByText('Thai translation');
    fireEvent.click(screen.getByRole('button', { name: 'Set test panel sizes' }));
    fireEvent.click(screen.getByRole('button', { name: 'ย่อแผง Sources' }));

    await waitFor(() => {
      expect(JSON.parse(window.localStorage.getItem('quran-workspace-layout') ?? '{}')).toEqual({
        sourcesOpen: false,
        studioOpen: true,
        panelLayout: { sources: 30, reader: 45, studio: 25 },
      });
    });
    firstRender.unmount();
    firstRender.queryClient.clear();

    const secondRender = renderPage();
    expect(await screen.findByRole('button', { name: 'เปิดแผง Sources' })).toBeTruthy();
    expect(document.querySelector('[data-panel="sources"]')).toBeNull();
    expect(Number(document.querySelector('[data-panel="reader"]')?.getAttribute('data-default-size')))
      .toBeCloseTo((45 / 70) * 100);
    expect(Number(document.querySelector('[data-panel="studio"]')?.getAttribute('data-default-size')))
      .toBeCloseTo((25 / 70) * 100);
    secondRender.queryClient.clear();
  });

  it('toggles Sources and Studio with shortcuts but ignores shortcuts from inputs', async () => {
    const page = renderPage();
    await screen.findAllByText('Thai translation');
    expect(screen.getByTestId('sources-panel')).toBeTruthy();
    expect(screen.getByTestId('studio-panel')).toBeTruthy();

    const input = screen.getByPlaceholderText('ค้นหาอายะฮ์ เช่น 2:255 หรือคำสำคัญ');
    fireEvent.keyDown(input, { key: '[' });
    expect(screen.getByTestId('sources-panel')).toBeTruthy();

    fireEvent.keyDown(window, { key: '[' });
    expect(screen.queryByTestId('sources-panel')).toBeNull();
    fireEvent.keyDown(window, { key: ']' });
    expect(screen.queryByTestId('studio-panel')).toBeNull();

    fireEvent.keyDown(window, { key: '[' });
    fireEvent.keyDown(window, { key: ']' });
    expect(screen.getByTestId('sources-panel')).toBeTruthy();
    expect(screen.getByTestId('studio-panel')).toBeTruthy();
    page.queryClient.clear();
  });

  it('selects all mobile tabs and saves the exact target Note payload from server citations', async () => {
    const createNote = jest.spyOn(apiClient, 'createNote').mockImplementation(async (note) => ({
      success: true,
      data: {
        ...note,
        id: 'note-1',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      } satisfies StudyNote,
    }));
    const page = renderPage();
    await screen.findAllByText('Thai translation');
    const mobileContent = screen.getByTestId('mobile-view-content');
    const mobileTabs = within(screen.getByTestId('workspace-mobile-tabs'));

    fireEvent.click(mobileTabs.getByRole('button', { name: 'อ่าน' }));
    expect(mobileTabs.getByRole('button', { name: 'อ่าน' }).getAttribute('aria-current')).toBe('page');
    expect(within(mobileContent).getAllByText('Thai translation').length).toBeGreaterThan(0);

    fireEvent.click(mobileTabs.getByRole('button', { name: 'Sources' }));
    expect(mobileTabs.getByRole('button', { name: 'Sources' }).getAttribute('aria-current')).toBe('page');
    expect(within(mobileContent).getByTestId('sources-panel')).toBeTruthy();

    fireEvent.click(mobileTabs.getByRole('button', { name: 'ตัฟซีร' }));
    expect(mobileTabs.getByRole('button', { name: 'ตัฟซีร' }).getAttribute('aria-current')).toBe('page');
    expect(within(mobileContent).getAllByText(/ตัฟซีร/).length).toBeGreaterThan(0);

    fireEvent.click(mobileTabs.getByRole('button', { name: 'Studio' }));
    expect(mobileTabs.getByRole('button', { name: 'Studio' }).getAttribute('aria-current')).toBe('page');
    expect(within(mobileContent).getByTestId('studio-panel')).toBeTruthy();
    fireEvent.click(within(mobileContent).getByRole('button', { name: 'Save Quran and Tafsir note' }));
    await waitFor(() => expect(createNote).toHaveBeenCalledTimes(1));
    expect(createNote).toHaveBeenLastCalledWith({
      title: 'Saved audio',
      content: JSON.stringify(mockTafsirArtifact),
      surah_number: 1,
      ayah_number: 1,
      source_label: 'Quran Al-Fatihah 1:1; Tafsir Ibn Kathir',
    });

    fireEvent.click(within(mobileContent).getByRole('button', { name: 'Save Quran only note' }));
    await waitFor(() => expect(createNote).toHaveBeenCalledTimes(2));
    expect(createNote).toHaveBeenLastCalledWith({
      title: 'Saved audio',
      content: JSON.stringify(mockQuranOnlyArtifact),
      surah_number: 1,
      ayah_number: 1,
      source_label: 'Quran Al-Fatihah 1:1',
    });
    expect(localQuranPaths.every((path) => path.startsWith('/api/quran/'))).toBe(true);
    page.queryClient.clear();
  });

  it('keeps the selected Quran ayah identifiable in the loaded Reader', async () => {
    const page = renderPage();
    await screen.findAllByText('Arabic verse');

    expect(document.querySelectorAll('[aria-current="location"]')).toHaveLength(2);
    page.queryClient.clear();
  });

  it('shares audio controls across responsive Readers and requests only the chosen spoken translation', async () => {
    const page = renderPage();
    await screen.findAllByText('Thai translation');

    expect(screen.queryAllByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })).toHaveLength(0);
    expect(document.querySelectorAll('audio')).toHaveLength(1);
    expect(document.querySelectorAll('audio[controls]')).toHaveLength(0);
    expect(screen.queryByText('เสียงอ่าน · อัลอะฟาซี')).toBeNull();
    expect(screen.getAllByRole('button', { name: 'ฟังเสียง' })).toHaveLength(2);

    const actionGroups = screen.getAllByRole('group', { name: 'การทำงานของอายะฮ์' });
    expect(actionGroups).toHaveLength(2);
    for (const actionGroup of actionGroups) {
      const actions = within(actionGroup);
      expect(actions.getByRole('button', { name: 'ถาม AI' })).toBeTruthy();
      expect(actions.getByRole('button', { name: 'บันทึกลงโน้ต' })).toBeTruthy();
      expect(actions.getByRole('button', { name: 'ฟังเสียง' }).classList.contains('reader-action-primary')).toBe(true);
      expect(actions.getByRole('switch', { name: 'เล่นต่อเนื่อง' })).toBeTruthy();
    }

    fireEvent.click(screen.getAllByRole('button', { name: 'ตั้งค่าเสียง' })[0]);
    expect(screen.getAllByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })).toHaveLength(2);
    expect(actionGroups.every((group) => group.closest('.reader-ayah-card')?.classList.contains('reader-ayah-card-settings-open'))).toBe(true);
    fireEvent.change(screen.getAllByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })[0], {
      target: { value: 'translation' },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'ภาษาเสียงแปล' })[0], {
      target: { value: 'en' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'ฟังเสียง' })[0]);

    await waitFor(() => {
      expect(localQuranPaths).toContain('/api/quran/surahs/1/?edition=en.sahih');
    });
    expect(screen.getAllByRole('combobox', { name: 'ภาษาเสียงแปล' }).every(
      (select) => (select as HTMLSelectElement).value === 'en',
    )).toBe(true);
    expect(screen.getAllByText('Thai translation')).toHaveLength(2);
    expect(document.querySelectorAll('audio')).toHaveLength(1);
    page.queryClient.clear();
  });

  it.each([
    ['th', 'th.thai'],
    ['en', 'en.sahih'],
    ['id', 'id.indonesian'],
  ])('requests AI audio for selected language %s and edition %s', async (language, edition) => {
    const audioBlob = new Blob(['audio']);
    jest.spyOn(apiClient, 'getTranslationAudioCapabilities').mockResolvedValue({
      available: true,
      supported_languages: ['th', 'en', 'id'],
      enabled_editions: ['th.thai', 'en.sahih', 'id.indonesian'],
    });
    const getTranslationAudio = jest.spyOn(apiClient, 'getTranslationAudio').mockResolvedValue({
      blob: audioBlob,
      cacheStatus: 'miss',
    });
    const page = renderPage();
    await screen.findAllByText('Thai translation');
    await waitFor(() => expect(apiClient.getTranslationAudioCapabilities).toHaveBeenCalled());

    fireEvent.click(screen.getAllByRole('button', { name: 'ตั้งค่าเสียง' })[0]);
    fireEvent.change(screen.getAllByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })[0], {
      target: { value: 'translation' },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'ภาษาเสียงแปล' })[0], {
      target: { value: language },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'เสียงแปล' })[0], {
      target: { value: 'ai' },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'ความเร็วเสียง' })[0], {
      target: { value: '1.15' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'ฟังเสียง' })[0]);

    await waitFor(() => expect(getTranslationAudio).toHaveBeenCalledWith(
      1,
      1,
      edition,
      1.15,
      expect.any(AbortSignal),
    ));
    expect(URL.createObjectURL).toHaveBeenCalledWith(audioBlob);
    page.unmount();
    page.queryClient.clear();
  });

  it('applies the selected speed to the native device speech utterance', async () => {
    const spokenUtterances: SpeechSynthesisUtterance[] = [];
    const availableVoice = { lang: 'en-US', name: 'English' };
    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: {
        getVoices: () => [availableVoice],
        speak: (utterance: SpeechSynthesisUtterance) => spokenUtterances.push(utterance),
        cancel: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
      },
    });
    Object.defineProperty(globalThis, 'SpeechSynthesisUtterance', {
      configurable: true,
      value: class {
        text: string;
        lang = '';
        rate = 1;
        voice: SpeechSynthesisVoice | null = null;
        onend: (() => void) | null = null;
        onerror: (() => void) | null = null;

        constructor(text: string) {
          this.text = text;
        }
      },
    });
    const page = renderPage();
    await screen.findAllByText('Thai translation');
    fireEvent.click(screen.getAllByRole('button', { name: 'ตั้งค่าเสียง' })[0]);
    fireEvent.change(screen.getAllByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })[0], {
      target: { value: 'translation' },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'ภาษาเสียงแปล' })[0], {
      target: { value: 'en' },
    });
    fireEvent.change(screen.getAllByRole('combobox', { name: 'ความเร็วเสียง' })[0], {
      target: { value: '1.15' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'ฟังเสียง' })[0]);

    await waitFor(() => expect(spokenUtterances).toHaveLength(1));
    expect(spokenUtterances[0].rate).toBe(1.15);
    page.unmount();
    page.queryClient.clear();
  });

  it('Auto advances and scrolls the shared Reader to the next ayah after playback ends', async () => {
    installLocalQuranFetch((path) => {
      if (path.includes('/ayahs/')) {
        return localQuranResponse([
          { number: 1, numberInSurah: 1, text_uthmani: 'Arabic one', page_number: 1 },
          { number: 2, numberInSurah: 2, text_uthmani: 'Arabic two', page_number: 1 },
        ]);
      }
      if (path.includes('edition=ar.alafasy')) {
        return localQuranResponse([
          { number: 1, numberInSurah: 1, audio: 'https://audio.example/1.mp3' },
          { number: 2, numberInSurah: 2, audio: 'https://audio.example/2.mp3' },
        ]);
      }
      return localQuranResponse(defaultLocalQuranBody(path));
    });
    const page = renderPage();
    await screen.findAllByText('Arabic one');

    const audio = screen.getByTestId('reader-playback-audio') as HTMLAudioElement;
    const play = jest.spyOn(audio, 'play').mockResolvedValue();
    jest.spyOn(audio, 'pause').mockImplementation(() => {});
    const scrollTargets = document.querySelectorAll<HTMLElement>('[data-reader-ayah="2"]');
    const scroll = jest.fn();
    scrollTargets.forEach((target) => {
      target.scrollIntoView = scroll;
    });

    fireEvent.click(screen.getAllByRole('switch', { name: 'เล่นต่อเนื่อง' })[0]);
    await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
    expect(audio.src).toBe('https://audio.example/1.mp3');

    await act(async () => {
      audio.dispatchEvent(new Event('ended'));
    });
    await waitFor(() => expect(play).toHaveBeenCalledTimes(2));
    expect(audio.src).toBe('https://audio.example/2.mp3');
    expect(scroll).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
    expect(new URLSearchParams(window.location.search).get('ayah')).toBe('2');

    await act(async () => {
      audio.dispatchEvent(new Event('ended'));
    });
    expect(screen.getAllByRole('status').some((status) => status.textContent?.includes('ครบซูเราะฮ์แล้ว'))).toBe(true);
    page.queryClient.clear();
  });

  it('manual ayah navigation cancels Auto and ignores the previous audio completion', async () => {
    installLocalQuranFetch((path) => {
      if (path.includes('/ayahs/')) {
        return localQuranResponse([
          { number: 1, numberInSurah: 1, text_uthmani: 'Arabic one', page_number: 1 },
          { number: 2, numberInSurah: 2, text_uthmani: 'Arabic two', page_number: 1 },
        ]);
      }
      if (path.includes('edition=ar.alafasy')) {
        return localQuranResponse([
          { number: 1, numberInSurah: 1, audio: 'https://audio.example/1.mp3' },
          { number: 2, numberInSurah: 2, audio: 'https://audio.example/2.mp3' },
        ]);
      }
      return localQuranResponse(defaultLocalQuranBody(path));
    });
    const page = renderPage();
    await screen.findAllByText('Arabic one');

    const audio = screen.getByTestId('reader-playback-audio') as HTMLAudioElement;
    const play = jest.spyOn(audio, 'play').mockResolvedValue();
    const pause = jest.spyOn(audio, 'pause').mockImplementation(() => {});
    fireEvent.click(screen.getAllByRole('switch', { name: 'เล่นต่อเนื่อง' })[0]);
    await waitFor(() => expect(play).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getAllByRole('button', { name: 'อายะฮ์ถัดไป' })[0]);
    expect(new URLSearchParams(window.location.search).get('ayah')).toBe('2');
    expect(pause).toHaveBeenCalled();
    await act(async () => {
      audio.dispatchEvent(new Event('ended'));
    });

    expect(play).toHaveBeenCalledTimes(1);
    expect(screen.getAllByRole('status').some((status) => status.textContent?.includes('หยุดการเล่นแล้ว'))).toBe(true);
    page.queryClient.clear();
  });
});
