// Tafsir agent data structures and source attribution types

export interface TafsirSource {
  id: string;
  bookId: string;
  author: string;
  authorAr?: string;
  title: string;
  edition?: string;
  publisher?: string;
  volume?: number;
  page?: number;
  chapter?: number;
  sourceUrl?: string;
  language: 'ar' | 'en' | 'ur';
  copyright?: string;
  verified: boolean;
  license?: string;
}

export interface Tafsir Passage {
  id: string;
  sourceId: string;
  ayahId: string;
  surah: number;
  ayah: number;
  arabicText: string;
  verse commentary: string;
  footnotes?: string[];
  hadithReferences?: HadithReference[];
  grading?: EvidenceGrade;
}

export interface HadithReference {
  collection: string;
  hadithId: string;
  text: string;
  grading?: EvidenceGrade;
}

export interface EvidenceGrade {
  level: 'sahih' | 'hasan' | 'daif' | 'maudu';
  chain?: string[];
  notes?: string;
}

export interface TafsirExplanation {
  sourceId: string;
  scholar: string;
  methodology: 'ma'thur' | 'ra'y' | 'linguistic' | 'legal' | 'contemporary';
  arabicOriginal?: string;
  thaiTranslation: string;
  analysis: string;
  keyPoints: string[];
  crossReferences: CrossReference[];
  evidenceLevel: EvidenceLevel;
}

export interface EvidenceLevel {
  label: 'VERIFIED' | 'SOURCE-ATTRIBUTED' | 'SCHOLARLY DIFFERENCE' | 'UNVERIFIED' | 'AI SYNTHESIS';
  confidence: number;
  sourceChain: string[];
  verificationNotes?: string;
}

export interface CrossReference {
  type: 'quran' | 'hadith' | 'tafsir';
  reference: string;
  text: string;
  relevance: number;
}

export interface ScholarlyComparison {
  ayahId: string;
  sources: TafsirSource[];
  explanations: TafsirExplanation[];
  agreements: string[];
  disagreements: Disagreement[];
}

export interface Disagreement {
  scholar1: string;
  scholar2: string;
  issue: string;
  evidence1: string[];
  evidence2: string[];
  resolution?: string;
}

export interface Citation {
  id: string;
  sourceId: string;
  passageId: string;
  ayahId: string;
  reference: string;
  originalText: string;
  excerpt: string;
  grading?: EvidenceGrade;
  verified: boolean;
}