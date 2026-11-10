import type {
  AudioHost,
  AudioStudioArtifact,
  InfographicLayoutHint,
  InfographicStudioArtifact,
  QuizStudioArtifact,
  StudioArtifactEnvelope,
  TargetStudioArtifactKind,
} from './api/client';

export type StudioArtifactValidationResult =
  | { valid: true; artifact: StudioArtifactEnvelope }
  | { valid: false; error: string };

type ContentValidation<T> =
  | { valid: true; content: T }
  | { valid: false; error: string };

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(
  value: UnknownRecord,
  requiredKeys: readonly string[],
  optionalKeys: readonly string[] = [],
): boolean {
  const allowedKeys = [...requiredKeys, ...optionalKeys];
  return (
    requiredKeys.every((key) => Object.prototype.hasOwnProperty.call(value, key))
    && Object.keys(value).every((key) => allowedKeys.includes(key))
  );
}

function normalizedText(value: unknown, minLength: number, maxLength: number): string | null {
  if (typeof value !== 'string') return null;
  const normalized = value.trim();
  const length = Array.from(normalized).length;
  return length >= minLength && length <= maxLength ? normalized : null;
}

function invalid(error: string): StudioArtifactValidationResult {
  return { valid: false, error };
}

function invalidContent<T>(error: string): ContentValidation<T> {
  return { valid: false, error };
}

function validateAudioContent(content: unknown): ContentValidation<AudioStudioArtifact['content']> {
  if (!isRecord(content) || !hasOnlyKeys(content, ['segments']) || !Array.isArray(content.segments)) {
    return invalidContent('Audio content must contain only a segments array');
  }
  if (content.segments.length < 4 || content.segments.length > 8) {
    return invalidContent('Audio requires 4-8 host segments');
  }

  const segments: AudioStudioArtifact['content']['segments'] = [];
  for (let index = 0; index < content.segments.length; index += 1) {
    const rawSegment = content.segments[index];
    if (!isRecord(rawSegment) || !hasOnlyKeys(rawSegment, ['host', 'text'])) {
      return invalidContent('Each audio segment must contain only host and text');
    }

    const hostValue = typeof rawSegment.host === 'string' ? rawSegment.host.trim() : '';
    const expectedHost = index % 2 === 0 ? 'Host A' : 'Host B';
    if (hostValue !== expectedHost) {
      return invalidContent('Audio hosts must alternate, starting with Host A');
    }
    const text = normalizedText(rawSegment.text, 1, 1200);
    if (text === null || !/[\u0E00-\u0E7F]/.test(text)) {
      return invalidContent('Audio segment text must contain 1-1,200 characters of Thai script');
    }

    const host: AudioHost = hostValue === 'Host A' ? 'Host A' : 'Host B';
    segments.push({ host, text });
  }

  return { valid: true, content: { segments } };
}

function validateQuizContent(content: unknown): ContentValidation<QuizStudioArtifact['content']> {
  if (!isRecord(content) || !hasOnlyKeys(content, ['questions']) || !Array.isArray(content.questions)) {
    return invalidContent('Quiz content must contain only a questions array');
  }
  if (content.questions.length !== 5) {
    return invalidContent('Quiz requires exactly five questions');
  }

  const questions: QuizStudioArtifact['content']['questions'] = [];
  for (const rawQuestion of content.questions) {
    if (
      !isRecord(rawQuestion)
      || !hasOnlyKeys(rawQuestion, ['question', 'options', 'answer_index', 'explanation'], ['source_passage_id'])
      || !Array.isArray(rawQuestion.options)
      || rawQuestion.options.length !== 3
    ) {
      return invalidContent('Each quiz question requires a prompt, three options, an answer, and an explanation');
    }

    const question = normalizedText(rawQuestion.question, 1, 500);
    const explanation = normalizedText(rawQuestion.explanation, 1, 1000);
    if (question === null || explanation === null) {
      return invalidContent('Quiz prompts must be 1-500 characters and explanations 1-1,000 characters');
    }

    const sourcePassageId = rawQuestion.source_passage_id === undefined
      ? undefined
      : normalizedText(rawQuestion.source_passage_id, 1, 200);
    if (sourcePassageId === null) {
      return invalidContent('Quiz source references must be 1-200 characters');
    }

    const optionValues: string[] = [];
    for (const option of rawQuestion.options) {
      const normalizedOption = normalizedText(option, 1, 200);
      if (normalizedOption === null) {
        return invalidContent('Quiz options must contain 1-200 non-whitespace characters');
      }
      optionValues.push(normalizedOption);
    }
    if (
      typeof rawQuestion.answer_index !== 'number'
      || !Number.isInteger(rawQuestion.answer_index)
      || rawQuestion.answer_index < 0
      || rawQuestion.answer_index > 2
    ) {
      return invalidContent('Quiz answer_index must be an integer from 0 to 2');
    }

    const options: [string, string, string] = [optionValues[0], optionValues[1], optionValues[2]];
    const answerIndex: 0 | 1 | 2 =
      rawQuestion.answer_index === 0 ? 0 : rawQuestion.answer_index === 1 ? 1 : 2;
    questions.push({
      question,
      options,
      answer_index: answerIndex,
      explanation,
      ...(sourcePassageId !== undefined ? { source_passage_id: sourcePassageId } : {}),
    });
  }

  return { valid: true, content: { questions } };
}

function validateInfographicContent(
  content: unknown,
): ContentValidation<InfographicStudioArtifact['content']> {
  if (
    !isRecord(content)
    || !hasOnlyKeys(content, ['takeaway', 'cards'], ['layout_hint'])
    || !Array.isArray(content.cards)
  ) {
    return invalidContent('Infographic content must contain a takeaway, cards, and optional layout_hint');
  }
  const takeaway = normalizedText(content.takeaway, 1, 500);
  if (takeaway === null) {
    return invalidContent('Infographic takeaway must contain 1-500 non-whitespace characters');
  }
  if (content.cards.length < 3 || content.cards.length > 6) {
    return invalidContent('Infographic requires 3-6 cards');
  }

  const cards: InfographicStudioArtifact['content']['cards'] = [];
  for (const rawCard of content.cards) {
    if (
      !isRecord(rawCard)
      || !hasOnlyKeys(rawCard, ['heading', 'points'])
      || !Array.isArray(rawCard.points)
    ) {
      return invalidContent('Each infographic card must contain only a heading and points array');
    }
    const heading = normalizedText(rawCard.heading, 1, 100);
    if (heading === null) {
      return invalidContent('Infographic headings must contain 1-100 non-whitespace characters');
    }
    if (rawCard.points.length < 2 || rawCard.points.length > 5) {
      return invalidContent('Each infographic card requires 2-5 points');
    }
    const points: string[] = [];
    for (const point of rawCard.points) {
      const normalizedPoint = normalizedText(point, 1, 280);
      if (normalizedPoint === null) {
        return invalidContent('Infographic points must contain 1-280 non-whitespace characters');
      }
      points.push(normalizedPoint);
    }
    cards.push({ heading, points });
  }

  let layoutHint: InfographicLayoutHint | undefined;
  if (Object.prototype.hasOwnProperty.call(content, 'layout_hint')) {
    if (
      content.layout_hint !== 'stacked'
      && content.layout_hint !== 'two-column'
      && content.layout_hint !== 'sequence'
    ) {
      return invalidContent('Infographic layout_hint must be stacked, two-column, or sequence');
    }
    layoutHint = content.layout_hint;
  }

  return {
    valid: true,
    content: layoutHint === undefined
      ? { takeaway, cards }
      : { takeaway, cards, layout_hint: layoutHint },
  };
}

export function validateStudioArtifactEdit(
  kind: TargetStudioArtifactKind,
  editorText: string,
): StudioArtifactValidationResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(editorText);
  } catch (error) {
    if (error instanceof SyntaxError) return invalid('Artifact JSON is malformed');
    throw error;
  }

  if (!isRecord(parsed) || !hasOnlyKeys(parsed, ['title', 'summary', 'content'])) {
    return invalid('Artifact must contain only title, summary, and content');
  }
  const title = normalizedText(parsed.title, 1, 160);
  const summary = normalizedText(parsed.summary, 0, 500);
  if (title === null || summary === null) {
    return invalid('Artifact title must be 1-160 characters and summary 0-500 characters');
  }

  if (kind === 'audio') {
    const result = validateAudioContent(parsed.content);
    return result.valid
      ? { valid: true, artifact: { title, summary, content: result.content } }
      : invalid(result.error);
  }
  if (kind === 'quiz') {
    const result = validateQuizContent(parsed.content);
    return result.valid
      ? { valid: true, artifact: { title, summary, content: result.content } }
      : invalid(result.error);
  }
  const result = validateInfographicContent(parsed.content);
  return result.valid
    ? { valid: true, artifact: { title, summary, content: result.content } }
    : invalid(result.error);
}
