"use client";

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011';

export type StudyNote = {
  id: string;
  title: string;
  content: string;
  surah_number: number | null;
  ayah_number: number | null;
  source_label: string;
  created_at: string;
  updated_at: string;
};

export type TranslationAudioCapabilities = {
  available: boolean;
  supported_languages: ('th' | 'en' | 'id')[];
  enabled_editions: string[];
};

export type TranslationAudioCacheStatus = 'hit' | 'miss' | 'unknown';

export type TranslationAudio = {
  blob: Blob;
  cacheStatus: TranslationAudioCacheStatus;
};

export type StudioArtifactRequest = {
  kind: StudioArtifactKind;
  surah_number: number;
  ayah_number: number;
  surah_name: string;
  arabic_text: string;
  translation: string;
  tafsir_book_id: string | null;
  selected_sources: string[];
};

export type TargetStudioArtifactKind = 'audio' | 'quiz' | 'infographic';
export type StudioArtifactKind =
  | TargetStudioArtifactKind
  | 'report'
  | 'slides'
  | 'video'
  | 'flashcards'
  | 'comparison';

export type StudioArtifactSource = {
  id: string;
  label: string;
  url: string;
};

export type AudioHost = 'Host A' | 'Host B';
export type AudioStudioArtifact = {
  title: string;
  summary: string;
  content: {
    segments: Array<{ host: AudioHost; text: string }>;
  };
};

export type QuizStudioArtifact = {
  title: string;
  summary: string;
  content: {
    questions: Array<{
      question: string;
      options: [string, string, string];
      answer_index: 0 | 1 | 2;
      explanation: string;
      source_passage_id?: string;
    }>;
  };
};

export type InfographicLayoutHint = 'stacked' | 'two-column' | 'sequence';
export type InfographicStudioArtifact = {
  title: string;
  summary: string;
  content: {
    takeaway: string;
    cards: Array<{ heading: string; points: string[] }>;
    layout_hint?: InfographicLayoutHint;
  };
};

export type StudioArtifactEnvelope =
  | AudioStudioArtifact
  | QuizStudioArtifact
  | InfographicStudioArtifact;

export type TargetStudioArtifactData =
  | {
      kind: 'audio';
      artifact: AudioStudioArtifact;
      sources: StudioArtifactSource[];
      evidence_status: 'AI-SYNTHESIS';
    }
  | {
      kind: 'quiz';
      artifact: QuizStudioArtifact;
      sources: StudioArtifactSource[];
      evidence_status: 'AI-SYNTHESIS';
    }
  | {
      kind: 'infographic';
      artifact: InfographicStudioArtifact;
      sources: StudioArtifactSource[];
      evidence_status: 'AI-SYNTHESIS';
    };

export type LegacyStudioArtifactKind = Exclude<
  StudioArtifactKind,
  TargetStudioArtifactKind
>;
export type LegacyStudioArtifactData = {
  kind: LegacyStudioArtifactKind;
  title: string;
  summary: string;
  sections: unknown[];
  slides: unknown[];
  scenes: unknown[];
  questions: unknown[];
  flashcards: unknown[];
  rows: unknown[];
  sources: StudioArtifactSource[];
  evidence_status: string;
};

export type StudioArtifactResponse = {
  success: boolean;
  data: TargetStudioArtifactData | LegacyStudioArtifactData;
};

export type AgentCitation = {
  passage_id: string;
  evidence_status: string;
  reference: {
    book?: string;
    scholar?: string;
    volume?: number | string | null;
    page?: number | string | null;
    edition?: string | null;
    url?: string | null;
  };
};

export type AgentOutput = {
  status?: string;
  error?: string;
  explanation?: string | Record<string, unknown>;
  evidence_level?: string;
  citations?: AgentCitation[];
};

export type AgentAnalysisValidation = {
  overall_valid: boolean;
  agent_validations: Record<string, {
    valid: boolean;
    errors: string[];
    warnings: string[];
    evidence_level: string;
  }>;
};

export type AgentAnalysisResponse = {
  success: boolean;
  data: {
    ayah_id: string;
    agents_executed: string[];
    agent_outputs: Record<string, AgentOutput>;
    sections?: Array<{
      question: string;
      ayah_id: string;
      agents_executed: string[];
      agent_outputs: Record<string, AgentOutput>;
      validation?: AgentAnalysisValidation;
    }>;
    session_id?: string | null;
    message_id?: string | null;
    followups_available?: boolean;
    evidence_summary: {
      total_sources: number;
      verified_sources: number;
      unverified_sources: number;
      ai_synthesis: number;
    };
    validation?: AgentAnalysisValidation;
  };
};

export type SuggestedFollowUp = {
  id: string;
  category: 'deepen' | 'compare' | 'context' | 'review' | 'source';
  title: string;
  prompt: string;
  basisCount: number;
  evidence: 'SOURCE_ATTRIBUTED' | 'AI_SYNTHESIS';
};

export type ChatSuggestionsResponse = {
  suggestions: SuggestedFollowUp[];
};

// API Client - Client-side fetch wrapper
export class ApiClient {
  private baseUrl: string;
  private cache: Map<string, Promise<any>> = new Map();

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async getTranslationAudioResponseError(response: Response): Promise<Error> {
    const body = await response.text();
    if (body.trim()) {
      try {
        const errorBody: unknown = JSON.parse(body);
        const detail = typeof errorBody === 'object' && errorBody !== null
          ? 'detail' in errorBody && typeof errorBody.detail === 'string'
            ? errorBody.detail
            : 'error' in errorBody && typeof errorBody.error === 'string'
              ? errorBody.error
              : 'message' in errorBody && typeof errorBody.message === 'string'
                ? errorBody.message
                : undefined
          : undefined;
        if (detail) return new Error(detail);
      } catch {
        // Non-JSON error bodies fall back to the HTTP status.
      }
    }

    return new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorBody: unknown = await response.json();
      const detail = typeof errorBody === 'object' && errorBody !== null
        ? 'detail' in errorBody && typeof errorBody.detail === 'string'
          ? errorBody.detail
          : 'error' in errorBody && typeof errorBody.error === 'string'
            ? errorBody.error
            : 'message' in errorBody && typeof errorBody.message === 'string'
              ? errorBody.message
              : undefined
        : undefined;
      throw new Error(
        typeof detail === 'string'
          ? detail
          : `API Error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async getTranslationAudioCapabilities(
    signal?: AbortSignal,
  ): Promise<TranslationAudioCapabilities> {
    const response = await fetch(`${this.baseUrl}/api/v1/quran/translation-audio/capabilities`, {
      signal,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) {
      throw await this.getTranslationAudioResponseError(response);
    }

    const payload: unknown = await response.json();
    if (
      typeof payload !== 'object'
      || payload === null
      || !('available' in payload)
      || typeof payload.available !== 'boolean'
      || !('supported_languages' in payload)
      || !Array.isArray(payload.supported_languages)
      || !payload.supported_languages.every((language) => (
        language === 'th' || language === 'en' || language === 'id'
      ))
      || !('enabled_editions' in payload)
      || !Array.isArray(payload.enabled_editions)
      || !payload.enabled_editions.every((edition) => typeof edition === 'string')
    ) {
      throw new Error('Invalid translation audio capabilities response');
    }

    return {
      available: payload.available,
      supported_languages: payload.supported_languages,
      enabled_editions: payload.enabled_editions,
    };
  }

  async getTranslationAudio(
    surah: number,
    ayah: number,
    edition: string,
    speed: number,
    signal?: AbortSignal,
  ): Promise<TranslationAudio> {
    const query = new URLSearchParams({
      edition,
      speed: String(speed),
    });
    const endpoint = `/api/v1/quran/translation-audio/${encodeURIComponent(String(surah))}/${encodeURIComponent(String(ayah))}?${query}`;
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      signal,
      credentials: 'include',
    });

    if (!response.ok) {
      throw await this.getTranslationAudioResponseError(response);
    }

    const contentType = response.headers.get('Content-Type')?.split(';', 1)[0].trim().toLowerCase();
    if (contentType !== 'audio/mpeg') {
      throw new Error(`Invalid translation audio content type: ${contentType ?? 'missing'}; expected audio/mpeg`);
    }

    const cacheHeader = response.headers.get('X-Audio-Cache')?.trim().toLowerCase();
    const cacheStatus: TranslationAudioCacheStatus = cacheHeader === 'hit' || cacheHeader === 'miss'
      ? cacheHeader
      : 'unknown';

    return { blob: await response.blob(), cacheStatus };
  }

  async post<T = any>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getNotes(): Promise<{ success: boolean; data: StudyNote[] }> {
    return this.request('/workspace/notes');
  }

  async createNote(note: Omit<StudyNote, 'id' | 'created_at' | 'updated_at'>): Promise<{ success: boolean; data: StudyNote }> {
    return this.request('/workspace/notes', {
      method: 'POST',
      body: JSON.stringify(note),
    });
  }

  async updateNote(noteId: string, update: { title?: string; content?: string }): Promise<{ success: boolean; data: StudyNote }> {
    return this.request(`/workspace/notes/${encodeURIComponent(noteId)}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  }

  async deleteNote(noteId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/workspace/notes/${encodeURIComponent(noteId)}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!response.ok) {
      const errorBody: unknown = await response.json();
      const detail = typeof errorBody === 'object' && errorBody !== null && 'error' in errorBody
        && typeof errorBody.error === 'string' ? errorBody.error : 'ลบโน้ตไม่สำเร็จ';
      throw new Error(detail);
    }
  }

  async createStudioArtifact(request: StudioArtifactRequest): Promise<StudioArtifactResponse> {
    return this.request<StudioArtifactResponse>('/workspace/artifacts', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTafsirPassage(surah: number, ayah: number, agentType: string) {
    return this.request<unknown>(
      `/tafsir/passages/${surah}/${ayah}?agent_type=${encodeURIComponent(agentType)}`
    );
  }

  async translateApiTafsirPassage(surah: number, ayah: number, agentType: string) {
    const query = `agent_type=${encodeURIComponent(agentType)}`;
    return this.request<unknown>(`/tafsir/passages/api/${surah}/${ayah}/translate?${query}`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async getAgentExplanation(
    surah: number,
    ayah: number,
    agentType: string,
    question = '',
    options?: { sessionId: string; subquestions?: string[] },
  ): Promise<AgentAnalysisResponse> {
    const query = new URLSearchParams({
      ayah_id: `${surah}:${ayah}`,
    });
    if (options) query.set('session_id', options.sessionId);
    return this.request<AgentAnalysisResponse>(`/tafsir/agents/explain?${query}`, {
      method: 'POST',
      body: JSON.stringify({
        agent_types: [agentType],
        context: {
          question,
          language: 'th',
          ...(options?.subquestions ? { subquestions: options.subquestions } : {}),
        },
      }),
    });
  }

  async getChatSuggestions(
    sessionId: string,
    messageId: string,
  ): Promise<ChatSuggestionsResponse> {
    return this.request<ChatSuggestionsResponse>('/chat/suggestions', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message_id: messageId }),
    });
  }

  async compareAgents(surah: number, ayah: number): Promise<unknown> {
    const query = new URLSearchParams({ ayah_id: `${surah}:${ayah}` });
    return this.request(`/tafsir/agents/compare?${query}`, { method: 'POST' });
  }

  async generateFlashcards(surah: number, ayahRange: number[], cardCount: number) {
    const endpoint = `/study/generate-flashcards?surah=${surah}&min=${ayahRange[0]}&max=${ayahRange[1]}&count=${cardCount}`;
    try {
      return await this.request<any>(endpoint);
    } catch (error) {
      console.error('Failed to generate flashcards:', error);
      return [];
    }
  }

  async generateQuiz(surah: number, questionCount: number, difficulty: string) {
    const endpoint = `/study/generate-quiz?surah=${surah}&count=${questionCount}&difficulty=${difficulty}`;
    try {
      return await this.request<any>(endpoint);
    } catch (error) {
      console.error('Failed to generate quiz:', error);
      return null;
    }
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
