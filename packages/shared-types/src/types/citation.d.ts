// Evidence and citation validation types

export interface SourcePermission {
  sourceId: string;
  bookId: string;
  license: string;
  allowedUses: string[]; // ['display', 'quotation', 'indexing', 'embedding', 'AI processing']
  restrictions?: string[];
  expiresAt?: string;
  reviewerId?: string;
  reviewDate?: string;
  status: 'pending' | 'approved' | 'rejected' | 'suspended';
}

export interface CitationValidationResult {
  citation: CitationValidation;
  isValid: boolean;
  issues: ValidationIssue[];
  confidence: number;
  recommendations?: string[];
}

export interface CitationValidation {
  sourceId: string;
  bookId: string;
  author: string;
  passageId?: string;
  ayahId?: string;
  excerpt: string;
  grading?: EvidenceGrade;
  verified: boolean;
}

export interface ValidationIssue {
  type: 'MISSING_SOURCE' | 'EXPIRED_LICENSE' | 'COPYRIGHT_VIOLATION' | 'UNVERIFIED_HADITH' | 'FABRICATED_CONTENT' | 'ATTRIBUTION_ERROR';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  location?: string;
  suggestedFix?: string;
}

export interface EvidenceGrade {
  level: 'sahih' | 'hasan' | 'daif' | 'maudu';
  chain?: string[];
  notes?: string;
  grader?: string;
}

export interface SourceQualityReport {
  sourceId: string;
  integrityScore: number;
  completenessScore: number;
  accuracyScore: number;
  issues: ValidationIssue[];
  lastVerified: string;
  reviewer?: string;
}

export interface SourceVerification {
  sourceId: string;
  verifiedBy: string;
  verificationDate: string;
  status: 'verified' | 'rejected' | 'pending_review';
  notes?: string;
  requiredActions?: string[];
}

export interface TafsirMetadata {
  sourceId: string;
  author: string;
  title: string;
  language: string;
  permissions: SourcePermission;
  verification: SourceVerification;
  qualityReport?: SourceQualityReport;
  ayahMappings: AyahMapping[];
}

export interface AyahMapping {
  ayahId: string;
  surah: number;
  ayah: number;
  location: string; // book, volume, page, chapter
  confidence: number;
  verified: boolean;
}

export interface CitationStats {
  totalSources: number;
  verifiedSources: number;
  unverifiedSources: number;
  discreditedSources: number;
  aiSynthesisCount: number;
  scholarlyDifferenceCount: number;
  lastUpdated: string;
}