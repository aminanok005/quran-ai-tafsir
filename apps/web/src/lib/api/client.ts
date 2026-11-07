"use client";

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011';

// API Client - Client-side fetch wrapper
export class ApiClient {
  private baseUrl: string;
  private cache: Map<string, Promise<any>> = new Map();

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
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

  async post<T = any>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTafsirPassage(surah: number, ayah: number, agentType: string) {
    return this.request<unknown>(
      `/tafsir/passages/${surah}/${ayah}?agent_type=${encodeURIComponent(agentType)}`
    );
  }

  async translateTafsirPassage(passageId: string) {
    return this.request<unknown>(`/tafsir/passages/${encodeURIComponent(passageId)}/translate`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async translateDevelopmentTafsirPassage(surah: number, ayah: number, agentType: string) {
    const query = `agent_type=${encodeURIComponent(agentType)}`;
    return this.request<unknown>(`/tafsir/passages/dev/${surah}/${ayah}/translate?${query}`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async getAgentExplanation(surah: number, ayah: number, agentType: string) {
    const endpoint = `/tafsir/agents/explain?surah=${surah}&ayah=${ayah}&agent_type=${agentType}&language=th`;
    try {
      return await this.request<any>(endpoint);
    } catch (error) {
      console.error('Failed to get agent explanation:', error);
      return null;
    }
  }

  async compareAgents(surah: number, ayah: number) {
    const endpoint = `/tafsir/compare?surah=${surah}&ayah=${ayah}`;
    try {
      return await this.request<any>(endpoint);
    } catch (error) {
      console.error('Failed to compare agents:', error);
      return null;
    }
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
