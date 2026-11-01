// Quran Foundation API response types and Quran data structures

export interface QuranMetadata {
  surahs: Surah[];
  surah: Surah;
  ayahs: Ayah[];
  ayah: Ayah;
}

export interface Surah {
  number: number;
  name: string;
  nameSimple: string;
  nameComplex: string;
  versesCount: number;
  pages: number[];
  revelation: {
    order: number;
    meccan: boolean;
  };
  recitation?: {
    audio: string[];
    surahId: string;
  };
}

export interface Ayah {
  id: string;
  surah: number;
  ayah: number;
  text: string; // Arabic Uthmani text
  textSimple: string;
  textComplex: string;
  translation?: {
    id: number;
    text: string;
    language: string;
    name: string;
  };
  words?: Word[];
  audio?: string;
}

export interface Word {
  id: string;
  ayahId: string;
  text: string;
  translation: string;
  transliteration: string;
}

export interface Translation {
  id: number;
  language: string;
  name: string;
  text: string;
  author?: string;
  source?: string;
}

export interface QuranSearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  page: number;
  perPage: number;
}

export interface SearchResult {
  ayahId: string;
  surah: number;
  ayah: number;
  text: string;
  score: number;
  matchType: 'exact' | 'word' | 'semantic';
}