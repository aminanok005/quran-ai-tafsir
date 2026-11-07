import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from './page';
import { apiClient, StudyNote } from '../src/lib/api/client';

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

function installLocalQuranFetch() {
  const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
    const path = String(input);
    localQuranPaths.push(path);
    const body = path === '/api/quran/surahs/'
      ? [{ number: 1, name_th: 'Al-Fatihah', verses_count: 7 }]
      : path.includes('/ayahs/')
        ? [{ number: 1, numberInSurah: 1, text_uthmani: 'Arabic verse', page_number: 1 }]
        : path.includes('edition=th.thai')
          ? [{ number: 1, numberInSurah: 1, text: 'Thai translation' }]
          : path.includes('edition=ar.alafasy')
            ? [{ number: 1, numberInSurah: 1, audio: 'https://audio.example/1.mp3' }]
            : [];
    return {
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => body,
    } as Response;
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
  jest.spyOn(apiClient, 'getTafsirPassage').mockResolvedValue({
    data: { translation_allowed: false, thai_translation: 'คำแปลตัฟซีร' },
  });
});

afterEach(() => {
  cleanup();
  jest.restoreAllMocks();
  window.localStorage.clear();
  if (originalFetchDescriptor) Object.defineProperty(globalThis, 'fetch', originalFetchDescriptor);
  else Reflect.deleteProperty(globalThis, 'fetch');
});

describe('workspace page integration', () => {
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
});
