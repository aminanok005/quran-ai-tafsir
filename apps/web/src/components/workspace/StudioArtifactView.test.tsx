import { fireEvent, render, screen, cleanup } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  apiClient,
  LegacyStudioArtifactData,
  TargetStudioArtifactData,
} from '../../lib/api/client';
import { StudioPanel, StudyContext } from './WorkspacePanels';
import { StudioArtifactView } from './StudioArtifactView';

const sources = [
  { id: 'quran', label: 'Quran 1:1', url: 'https://quran.com/1/1' },
];

const audioData: Extract<TargetStudioArtifactData, { kind: 'audio' }> = {
  kind: 'audio',
  artifact: {
    title: 'Audio lesson',
    summary: 'A short overview.',
    content: {
      segments: [
        { host: 'Host A', text: 'คำอธิบายช่วงที่หนึ่ง' },
        { host: 'Host B', text: 'คำอธิบายช่วงที่สอง' },
        { host: 'Host A', text: 'คำอธิบายช่วงที่สาม' },
        { host: 'Host B', text: 'คำอธิบายช่วงที่สี่' },
      ],
    },
  },
  sources,
  evidence_status: 'AI-SYNTHESIS',
};

const quizData: Extract<TargetStudioArtifactData, { kind: 'quiz' }> = {
  kind: 'quiz',
  artifact: {
    title: 'Five question quiz',
    summary: 'Check understanding.',
    content: {
      questions: Array.from({ length: 5 }, (_, index) => ({
        question: `Question ${index + 1}`,
        options: ['First choice', 'Second choice', 'Third choice'],
        answer_index: 1 as const,
        explanation: `Explanation ${index + 1}`,
      })),
    },
  },
  sources,
  evidence_status: 'AI-SYNTHESIS',
};

function infographicData(
  layoutHint: 'stacked' | 'two-column' | 'sequence',
): Extract<TargetStudioArtifactData, { kind: 'infographic' }> {
  return {
    kind: 'infographic',
    artifact: {
      title: 'Infographic',
      summary: 'Visual summary.',
      content: {
        takeaway: 'A central takeaway.',
        cards: [
          { heading: 'Card one', points: ['First point.', 'Second point.'] },
          { heading: 'Card two', points: ['First point.', 'Second point.'] },
          { heading: 'Card three', points: ['First point.', 'Second point.'] },
        ],
        layout_hint: layoutHint,
      },
    },
    sources,
    evidence_status: 'AI-SYNTHESIS',
  };
}

const context: StudyContext = {
  surah_number: 1,
  ayah_number: 1,
  surah_name: 'Al-Fatihah',
  arabic_text: 'Ayah',
  translation: 'Translation',
  tafsir_text: '',
  tafsir_approved: false,
  tafsir_source: '',
  tafsir_book_id: null,
};

class MockSpeechSynthesisUtterance {
  voice: SpeechSynthesisVoice | null = null;
  lang = '';

  constructor(public text: string) {}
}

function installSpeechMock(voices: SpeechSynthesisVoice[]) {
  const speech = {
    cancel: jest.fn(),
    getVoices: jest.fn(() => voices),
    pause: jest.fn(),
    resume: jest.fn(),
    speak: jest.fn(),
  };
  Object.defineProperty(window, 'speechSynthesis', {
    configurable: true,
    value: speech,
  });
  Object.defineProperty(window, 'SpeechSynthesisUtterance', {
    configurable: true,
    value: MockSpeechSynthesisUtterance,
  });
  return speech;
}

let createObjectUrlDescriptor: PropertyDescriptor | undefined;
let revokeObjectUrlDescriptor: PropertyDescriptor | undefined;

function mountStudioPanel(
  onSaveArtifact = jest.fn(async () => {}),
  onSaveTargetArtifact = jest.fn(async () => {}),
  selectedSources = ['quran'],
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <StudioPanel
        context={context}
        selectedSources={selectedSources}
        onSaveArtifact={onSaveArtifact}
        onSaveTargetArtifact={onSaveTargetArtifact}
      />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
}

beforeEach(() => {
  window.localStorage.clear();
  createObjectUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
  revokeObjectUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL');
});

afterEach(() => {
  cleanup();
  jest.restoreAllMocks();
  Reflect.deleteProperty(window, 'speechSynthesis');
  if (createObjectUrlDescriptor) Object.defineProperty(URL, 'createObjectURL', createObjectUrlDescriptor);
  else Reflect.deleteProperty(URL, 'createObjectURL');
  if (revokeObjectUrlDescriptor) Object.defineProperty(URL, 'revokeObjectURL', revokeObjectUrlDescriptor);
  else Reflect.deleteProperty(URL, 'revokeObjectURL');
});

describe('StudioArtifactView', () => {
  it('renders audio segments in order and speaks with a Thai voice', () => {
    const thaiVoice: SpeechSynthesisVoice = {
      default: true,
      lang: 'th-TH',
      localService: true,
      name: 'Thai voice',
      voiceURI: 'thai-local',
    };
    const speech = installSpeechMock([thaiVoice]);
    render(<StudioArtifactView data={audioData} />);

    expect(screen.getAllByTestId('audio-segment').map((item) => item.textContent)).toEqual([
      expect.stringContaining('คำอธิบายช่วงที่หนึ่ง'),
      expect.stringContaining('คำอธิบายช่วงที่สอง'),
      expect.stringContaining('คำอธิบายช่วงที่สาม'),
      expect.stringContaining('คำอธิบายช่วงที่สี่'),
    ]);

    fireEvent.click(screen.getByRole('button', { name: 'Play audio' }));

    expect(speech.speak).toHaveBeenCalledTimes(4);
    const utterance = speech.speak.mock.calls[0][0] as MockSpeechSynthesisUtterance;
    expect(utterance.text).toBe('คำอธิบายช่วงที่หนึ่ง');
    expect(utterance.voice).toBe(thaiVoice);
    expect(utterance.lang).toBe('th-TH');

    fireEvent.click(screen.getByRole('button', { name: 'Stop audio' }));
    expect(speech.cancel).toHaveBeenCalled();
  });

  it('explains unsupported speech and an unavailable Thai voice', () => {
    render(<StudioArtifactView data={audioData} />);
    fireEvent.click(screen.getByRole('button', { name: 'Play audio' }));
    expect(screen.getByRole('status').textContent).toMatch(/not supported/i);

    cleanup();
    const speech = installSpeechMock([]);
    render(<StudioArtifactView data={audioData} />);
    fireEvent.click(screen.getByRole('button', { name: 'Play audio' }));
    expect(screen.getByRole('status').textContent).toMatch(/Thai voice/i);
    expect(speech.speak).not.toHaveBeenCalled();
  });

  it('shows quiz correctness and explanation without persisting progress', () => {
    render(<StudioArtifactView data={quizData} />);

    expect(screen.getAllByRole('heading', { level: 3, name: /^\d+\. Question \d+$/ })).toHaveLength(5);
    expect(screen.getAllByRole('button', { name: /Question \d+ option \d+/ })).toHaveLength(15);
    fireEvent.click(screen.getByRole('button', { name: 'Question 1 option 2' }));

    expect(screen.getByRole('status').textContent).toBe('Correct');
    expect(screen.getByText('Explanation 1')).toBeTruthy();
    expect(screen.getByTestId('quiz-progress').textContent).toContain('Score: 1');
    expect(screen.getByTestId('quiz-progress').textContent).toContain('5');
    expect(window.localStorage.length).toBe(0);
  });

  it.each(['stacked', 'two-column', 'sequence'] as const)(
    'renders infographic cards with the %s layout hint',
    (layoutHint) => {
      render(<StudioArtifactView data={infographicData(layoutHint)} />);

      expect(screen.getByTestId('infographic').getAttribute('data-layout')).toBe(layoutHint);
      expect(screen.getByText('A central takeaway.')).toBeTruthy();
      expect(screen.getByRole('heading', { name: /Card one/ })).toBeTruthy();
      expect(screen.getByRole('heading', { name: /Card two/ })).toBeTruthy();
      expect(screen.getByRole('heading', { name: /Card three/ })).toBeTruthy();
    },
  );

  it('renders citation links with only the server-provided labels and URLs', () => {
    render(<StudioArtifactView data={audioData} />);

    const citation = screen.getByRole('link', { name: 'Quran 1:1' });
    expect(citation.getAttribute('href')).toBe('https://quran.com/1/1');
    expect(citation.getAttribute('rel')).toBe('noopener noreferrer');
  });

  it('keeps legacy slide artifacts on their existing renderer', async () => {
    const legacyArtifact: LegacyStudioArtifactData = {
      kind: 'slides',
      title: 'Legacy slide deck',
      summary: 'Legacy summary.',
      sections: [],
      slides: [{ title: 'Legacy slide title', bullets: ['One point'], notes: '' }],
      scenes: [],
      questions: [],
      flashcards: [],
      rows: [],
      sources,
      evidence_status: 'AI-SYNTHESIS',
    };
    const createArtifact = jest
      .spyOn(apiClient, 'createStudioArtifact')
      .mockResolvedValue({ success: true, data: legacyArtifact });
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <StudioPanel context={context} selectedSources={['quran']} onSaveArtifact={async () => {}} onSaveTargetArtifact={async () => {}} />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getByRole('button', { name: /Slides/ }));
    fireEvent.click(screen.getByRole('button', { name: /สร้าง Slides/ }));

    expect(await screen.findByText('Legacy slide title')).toBeTruthy();
    expect(createArtifact).toHaveBeenCalledTimes(1);
    queryClient.clear();
  });

  it('only generates after one explicit click, not on mount, kind selection, or source changes', async () => {
    const createArtifact = jest
      .spyOn(apiClient, 'createStudioArtifact')
      .mockResolvedValue({ success: true, data: audioData });
    const panel = mountStudioPanel();

    fireEvent.click(screen.getByRole('button', { name: /Audio Overview/ }));
    panel.rerender(
      <QueryClientProvider client={panel.queryClient}>
        <StudioPanel
          context={context}
          selectedSources={['quran', 'tafsir']}
          onSaveArtifact={jest.fn(async () => {})}
          onSaveTargetArtifact={jest.fn(async () => {})}
        />
      </QueryClientProvider>,
    );
    expect(createArtifact).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /สร้าง Audio Overview/ }));
    expect(await screen.findByRole('heading', { name: 'Audio lesson' })).toBeTruthy();
    expect(createArtifact).toHaveBeenCalledTimes(1);
  });

  it.each([
    'LLM_API_KEY is not configured',
    'Provider authorization failed',
    'Provider is unavailable',
    'AI returned an invalid Studio artifact',
    'Selected source is not approved',
    'Tafsir is missing from the cache',
  ])('shows the API error detail for generation failures: %s', async (message) => {
    jest.spyOn(apiClient, 'createStudioArtifact').mockRejectedValue(new Error(message));
    mountStudioPanel();

    fireEvent.click(screen.getByRole('button', { name: /สร้าง Report/ }));

    expect((await screen.findByRole('alert')).textContent).toContain(message);
  });

  it('rejects invalid generated target output visibly', async () => {
    const invalidAudio: Extract<TargetStudioArtifactData, { kind: 'audio' }> = {
      ...audioData,
      artifact: {
        ...audioData.artifact,
        content: { segments: [] },
      },
    };
    jest.spyOn(apiClient, 'createStudioArtifact').mockResolvedValue({
      success: true,
      data: invalidAudio,
    });
    mountStudioPanel();
    fireEvent.click(screen.getByRole('button', { name: /Audio Overview/ }));
    fireEvent.click(screen.getByRole('button', { name: /สร้าง Audio Overview/ }));

    expect((await screen.findByRole('alert')).textContent).toMatch(/invalid Studio artifact/i);
    expect(screen.queryByRole('heading', { name: 'Audio lesson' })).toBeNull();
  });

  it('preserves the last valid preview and disables export and save for invalid edits', async () => {
    jest.spyOn(apiClient, 'createStudioArtifact').mockResolvedValue({
      success: true,
      data: audioData,
    });
    mountStudioPanel();
    fireEvent.click(screen.getByRole('button', { name: /Audio Overview/ }));
    fireEvent.click(screen.getByRole('button', { name: /สร้าง Audio Overview/ }));
    expect(await screen.findByRole('heading', { name: 'Audio lesson' })).toBeTruthy();

    fireEvent.click(screen.getByText('แก้ไข artifact (JSON)'));
    fireEvent.change(screen.getByRole('textbox', { name: 'แก้ไข artifact JSON' }), {
      target: { value: '{ invalid json' },
    });

    expect(screen.getByRole('heading', { name: 'Audio lesson' })).toBeTruthy();
    expect(screen.getByRole('alert').textContent).toMatch(/JSON/i);
    expect(screen.getByRole('button', { name: /ส่งออก JSON/ }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByRole('button', { name: /Save to Note/ }).hasAttribute('disabled')).toBe(true);
  });

  it('exports the full target envelope with edited fields and unchanged source metadata', async () => {
    let downloadedBlob: Blob | undefined;
    let downloadedName = '';
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: (blob: Blob) => {
        downloadedBlob = blob;
        return 'blob:studio-artifact';
      },
    });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: jest.fn() });
    jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      downloadedName = this.download;
    });
    jest.spyOn(apiClient, 'createStudioArtifact').mockResolvedValue({
      success: true,
      data: audioData,
    });
    mountStudioPanel();
    fireEvent.click(screen.getByRole('button', { name: /Audio Overview/ }));
    fireEvent.click(screen.getByRole('button', { name: /สร้าง Audio Overview/ }));
    await screen.findByRole('heading', { name: 'Audio lesson' });
    fireEvent.click(screen.getByText('แก้ไข artifact (JSON)'));
    fireEvent.change(screen.getByRole('textbox', { name: 'แก้ไข artifact JSON' }), {
      target: {
        value: JSON.stringify({
          title: 'Edited audio',
          summary: 'Edited summary.',
          content: audioData.artifact.content,
        }),
      },
    });

    fireEvent.click(screen.getByRole('button', { name: /ส่งออก JSON/ }));
    expect(downloadedBlob).toBeTruthy();
    expect(downloadedName).toMatch(/audio-1-1\.json/);
    const exportedText = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(reader.error);
      reader.readAsText(downloadedBlob as Blob);
    });
    expect(JSON.parse(exportedText)).toEqual({
      ...audioData,
      artifact: {
        ...audioData.artifact,
        title: 'Edited audio',
        summary: 'Edited summary.',
      },
    });

  });

  it('passes the complete edited target envelope and ayah context to Note saving', async () => {
    const saveArtifact = jest.fn(async () => {});
    jest.spyOn(apiClient, 'createStudioArtifact').mockResolvedValue({
      success: true,
      data: audioData,
    });
    mountStudioPanel(jest.fn(async () => {}), saveArtifact);
    fireEvent.click(screen.getByRole('button', { name: /Audio Overview/ }));
    fireEvent.click(screen.getByRole('button', { name: /สร้าง Audio Overview/ }));
    await screen.findByRole('heading', { name: 'Audio lesson' });
    fireEvent.click(screen.getByText('แก้ไข artifact (JSON)'));
    fireEvent.change(screen.getByRole('textbox', { name: 'แก้ไข artifact JSON' }), {
      target: {
        value: JSON.stringify({
          title: 'Edited audio',
          summary: 'Edited summary.',
          content: audioData.artifact.content,
        }),
      },
    });

    fireEvent.click(screen.getByRole('button', { name: /Save to Note/ }));
    expect(await screen.findByText('บันทึกลง Personal Notes แล้ว')).toBeTruthy();
    expect(saveArtifact).toHaveBeenCalledWith({
      ...audioData,
      artifact: {
        ...audioData.artifact,
        title: 'Edited audio',
        summary: 'Edited summary.',
      },
    }, context);
  });
});
