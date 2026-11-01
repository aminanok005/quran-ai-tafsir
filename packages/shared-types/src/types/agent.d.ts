// Agent orchestration and execution types

export type AgentType =
  | 'ibn-kathir'
  | 'al-tabari'
  | 'al-qurtubi'
  | 'ibn-ashur'
  | 'al-saadi'
  | 'al-zuhayli';

export interface AgentConfig {
  agentId: string;
  agentType: AgentType;
  scholar: string;
  scholarAr?: string;
  methodology: AgentMethodology;
  sourceCollection: string;
  retrievalConfig: RetrievalConfig;
  outputSchema: OutputSchema;
  qualityGates: QualityGate[];
  maxContextLength: number;
  temperature: number;
  topP: number;
  defaultMaxTokens: number;
}

export interface AgentMethodology {
  type: 'ma'thur' | 'ra'y' | 'linguistic' | 'legal' | 'contemporary';
  description: string;
  prioritySources: string[];
  exclusionCriteria?: string[];
}

export interface RetrievalConfig {
  sourceTypes: ('quran' | 'hadith' | 'tafsir')[];
  minConfidence: number;
  maxResults: number;
  filterByVerified: boolean;
  includeUnverifiedWithFlags: boolean;
}

export interface OutputSchema {
  explanation: string;
  arabicOriginal?: string;
  thaiTranslation: string;
  analysis: string;
  citations: string[];
  confidence: number;
  scholarlyPosition?: string;
  disagreementWith?: string[];
}

export interface QualityGate {
  type: 'citation_accuracy' | 'content_authenticity' | 'thai_translation' | 'scholarly_attribution';
  threshold: number;
  action: 'allow' | 'reject' | 'request_revision';
}

export interface AgentExecution {
  executionId: string;
  agentId: string;
  ayahId: string;
  context: AgentContext;
  sources: RetrievedSource[];
  output: AgentOutput;
  citations: Citation[];
  metadata: ExecutionMetadata;
}

export interface AgentContext {
  ayahId: string;
  surah: number;
  ayah: number;
  arabicText: string;
  userContext?: string;
  previousExplanations?: AgentOutput[];
}

export interface RetrievedSource {
  sourceId: string;
  title: string;
  author: string;
  relevance: number;
  confidence: number;
  excerpt: string;
  fullText?: string;
}

export interface AgentOutput {
  explanation: string;
  citations: CitationReference[];
  confidence: number;
  scholarlyPosition?: string;
  methodologyNotes?: string;
  limitations?: string[];
}

export interface CitationReference {
  sourceId: string;
  passageId?: string;
  reference: string;
  excerpt: string;
  grade?: EvidenceGrade;
}

export interface ExecutionMetadata {
  startTime: string;
  endTime: string;
  duration: number;
  llmProvider: string;
  model: string;
  tokenUsage: TokenUsage;
  cost: number;
  qualityScore: number;
}

export interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
}

export interface EvidenceGrade {
  level: 'sahih' | 'hasan' | 'daif' | 'maudu';
  chain?: string[];
}

export interface AgentStatus {
  agentId: string;
  status: 'idle' | 'processing' | 'completed' | 'failed' | 'quality_check';
  currentExecutions: number;
  queueSize: number;
  errorCount: number;
  lastExecution?: string;
}

export interface AgentOrchestrationRequest {
  ayahId: string;
  agentTypes: AgentType[];
  context?: Partial<AgentContext>;
  options?: Partial<AgentConfig>;
}

export interface AgentOrchestrationResult {
  executionId: string;
  agentOutputs: AgentOutput[];
  comparison?: ScholarlyComparison;
  metadata: OrchestrationMetadata;
}

export interface OrchestrationMetadata {
  agentsExecuted: string[];
  totalSourcesRetrieved: number;
  totalCitations: number;
  processingTime: number;
  cacheHits: number;
}

export interface AgentHealthCheck {
  agentId: string;
  healthy: boolean;
  lastHealthCheck: string;
  issues: HealthIssue[];
}

export interface HealthIssue {
  sourceUnavailable: string[];
  citationValidationFailed: number;
  qualityGateFailed: string[];
  lastError?: string;
  errorCount: number;
}