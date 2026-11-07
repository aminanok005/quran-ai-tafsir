import { validateStudioArtifactEdit } from './studio-artifact-validation';

const audioContent = (count = 4) => ({
  segments: Array.from({ length: count }, (_, index) => ({
    host: index % 2 === 0 ? 'Host A' : 'Host B',
    text: `คำอธิบาย ${index + 1}`,
  })),
});

const quizContent = () => ({
  questions: Array.from({ length: 5 }, (_, index) => ({
    question: `Question ${index + 1}?`,
    options: ['First', 'Second', 'Third'],
    answer_index: 1,
    explanation: 'Supported by the source.',
  })),
});

const infographicContent = () => ({
  takeaway: 'A source-supported takeaway.',
  cards: Array.from({ length: 3 }, (_, index) => ({
    heading: `Card ${index + 1}`,
    points: ['First point.', 'Second point.'],
  })),
});

function artifactFor(kind: 'audio'): {
  title: string;
  summary: string;
  content: ReturnType<typeof audioContent>;
};
function artifactFor(kind: 'quiz'): {
  title: string;
  summary: string;
  content: ReturnType<typeof quizContent>;
};
function artifactFor(kind: 'infographic'): {
  title: string;
  summary: string;
  content: ReturnType<typeof infographicContent>;
};
function artifactFor(kind: 'audio' | 'quiz' | 'infographic') {
  return {
    title: 'Title',
    summary: '',
    content: kind === 'audio'
      ? audioContent()
      : kind === 'quiz'
        ? quizContent()
        : infographicContent(),
  };
}

function addField(target: object, key: string, value: unknown) {
  Object.assign(target, { [key]: value });
}

function expectInvalid(kind: 'audio' | 'quiz' | 'infographic', artifact: unknown) {
  const result = validateStudioArtifactEdit(kind, JSON.stringify(artifact));
  expect(result.valid).toBe(false);
  if (!result.valid) expect(result.error.length).toBeGreaterThan(0);
}

describe('validateStudioArtifactEdit', () => {
  it('accepts inclusive boundaries for all structured artifact kinds', () => {
    const audio = artifactFor('audio');
    audio.title = 'T'.repeat(160);
    audio.summary = 'S'.repeat(500);
    audio.content = audioContent(8);
    audio.content.segments[0].text = 'ค'.repeat(1200);
    expect(validateStudioArtifactEdit('audio', JSON.stringify(audio)).valid).toBe(true);

    const quiz = artifactFor('quiz');
    quiz.title = 'T';
    quiz.summary = '';
    quiz.content.questions[0].question = 'Q'.repeat(500);
    quiz.content.questions[0].options[0] = 'O'.repeat(200);
    quiz.content.questions[0].answer_index = 2;
    quiz.content.questions[0].explanation = 'E'.repeat(1000);
    expect(validateStudioArtifactEdit('quiz', JSON.stringify(quiz)).valid).toBe(true);

    const infographic = artifactFor('infographic');
    infographic.content.takeaway = 'T'.repeat(500);
    infographic.content.cards = Array.from({ length: 6 }, (_, index) => ({
      heading: 'H'.repeat(100),
      points: Array.from({ length: 5 }, () => 'P'.repeat(280)),
    }));
    addField(infographic.content, 'layout_hint', 'two-column');
    expect(validateStudioArtifactEdit('infographic', JSON.stringify(infographic)).valid).toBe(true);
  });

  it('rejects malformed JSON and unknown fields at every object depth', () => {
    expect(validateStudioArtifactEdit('audio', '{not json').valid).toBe(false);

    const extraTopLevel = artifactFor('audio');
    addField(extraTopLevel, 'provider_metadata', 'forbidden');
    expectInvalid('audio', extraTopLevel);

    const extraContent = artifactFor('audio');
    addField(extraContent.content, 'unexpected', true);
    expectInvalid('audio', extraContent);

    const extraSegment = artifactFor('audio');
    addField(extraSegment.content.segments[0], 'extra', true);
    expectInvalid('audio', extraSegment);

    const extraQuestion = artifactFor('quiz');
    addField(extraQuestion.content.questions[0], 'extra', true);
    expectInvalid('quiz', extraQuestion);

    const extraCard = artifactFor('infographic');
    addField(extraCard.content.cards[0], 'extra', true);
    expectInvalid('infographic', extraCard);
  });

  it('rejects audio count, length, language, and host violations', () => {
    expectInvalid('audio', { ...artifactFor('audio'), content: audioContent(3) });
    expectInvalid('audio', { ...artifactFor('audio'), content: audioContent(9) });
    expectInvalid('audio', { ...artifactFor('audio'), title: ' ' });
    expectInvalid('audio', { ...artifactFor('audio'), title: '' });
    expectInvalid('audio', { ...artifactFor('audio'), title: 'T'.repeat(161) });
    expectInvalid('audio', { ...artifactFor('audio'), summary: 'S'.repeat(501) });

    const shortText = artifactFor('audio');
    shortText.content.segments[0].text = '';
    expectInvalid('audio', shortText);
    const longText = artifactFor('audio');
    longText.content.segments[0].text = 'ค'.repeat(1201);
    expectInvalid('audio', longText);
    const nonThaiText = artifactFor('audio');
    nonThaiText.content.segments[0].text = 'English only';
    expectInvalid('audio', nonThaiText);
    const wrongFirstHost = artifactFor('audio');
    wrongFirstHost.content.segments[0].host = 'Host B';
    expectInvalid('audio', wrongFirstHost);
    const repeatedHost = artifactFor('audio');
    repeatedHost.content.segments[1].host = 'Host A';
    expectInvalid('audio', repeatedHost);
  });

  it('rejects quiz field lengths, counts, and non-integer answer indices', () => {
    expectInvalid('quiz', { ...artifactFor('quiz'), title: 'T'.repeat(161) });
    expectInvalid('quiz', { ...artifactFor('quiz'), summary: 'S'.repeat(501) });
    expectInvalid('quiz', { ...artifactFor('quiz'), content: { questions: quizContent().questions.slice(0, 4) } });
    expectInvalid('quiz', {
      ...artifactFor('quiz'),
      content: { questions: [...quizContent().questions, quizContent().questions[0]] },
    });

    const shortQuestion = artifactFor('quiz');
    shortQuestion.content.questions[0].question = '';
    expectInvalid('quiz', shortQuestion);
    const longQuestion = artifactFor('quiz');
    longQuestion.content.questions[0].question = 'Q'.repeat(501);
    expectInvalid('quiz', longQuestion);
    const shortOptions = artifactFor('quiz');
    shortOptions.content.questions[0].options.pop();
    expectInvalid('quiz', shortOptions);
    const longOptions = artifactFor('quiz');
    longOptions.content.questions[0].options.push('Fourth');
    expectInvalid('quiz', longOptions);
    const shortOptionText = artifactFor('quiz');
    shortOptionText.content.questions[0].options[0] = '';
    expectInvalid('quiz', shortOptionText);
    const longOptionText = artifactFor('quiz');
    longOptionText.content.questions[0].options[0] = 'O'.repeat(201);
    expectInvalid('quiz', longOptionText);
    for (const answerIndex of [-1, 3, 1.5, true]) {
      const invalidAnswer = artifactFor('quiz');
      addField(invalidAnswer.content.questions[0], 'answer_index', answerIndex);
      expectInvalid('quiz', invalidAnswer);
    }
    const shortExplanation = artifactFor('quiz');
    shortExplanation.content.questions[0].explanation = '';
    expectInvalid('quiz', shortExplanation);
    const longExplanation = artifactFor('quiz');
    longExplanation.content.questions[0].explanation = 'E'.repeat(1001);
    expectInvalid('quiz', longExplanation);
  });

  it('rejects infographic bounds and invalid layout hints', () => {
    expectInvalid('infographic', { ...artifactFor('infographic'), title: 'T'.repeat(161) });
    expectInvalid('infographic', { ...artifactFor('infographic'), summary: 'S'.repeat(501) });
    expectInvalid('infographic', { ...artifactFor('infographic'), content: { ...infographicContent(), takeaway: '' } });
    expectInvalid('infographic', { ...artifactFor('infographic'), content: { ...infographicContent(), takeaway: 'T'.repeat(501) } });
    expectInvalid('infographic', {
      ...artifactFor('infographic'),
      content: { ...infographicContent(), cards: infographicContent().cards.slice(0, 2) },
    });
    expectInvalid('infographic', {
      ...artifactFor('infographic'),
      content: {
        ...infographicContent(),
        cards: [
          ...infographicContent().cards,
          ...infographicContent().cards,
          ...infographicContent().cards,
        ],
      },
    });

    const shortHeading = artifactFor('infographic');
    shortHeading.content.cards[0].heading = '';
    expectInvalid('infographic', shortHeading);
    const longHeading = artifactFor('infographic');
    longHeading.content.cards[0].heading = 'H'.repeat(101);
    expectInvalid('infographic', longHeading);
    const shortPoints = artifactFor('infographic');
    shortPoints.content.cards[0].points.pop();
    expectInvalid('infographic', shortPoints);
    const longPoints = artifactFor('infographic');
    longPoints.content.cards[0].points = Array.from({ length: 6 }, () => 'Point');
    expectInvalid('infographic', longPoints);
    const emptyPoint = artifactFor('infographic');
    emptyPoint.content.cards[0].points[0] = '';
    expectInvalid('infographic', emptyPoint);
    const overlongPoint = artifactFor('infographic');
    overlongPoint.content.cards[0].points[0] = 'P'.repeat(281);
    expectInvalid('infographic', overlongPoint);

    const omittedLayoutHint = artifactFor('infographic');
    expect(validateStudioArtifactEdit('infographic', JSON.stringify(omittedLayoutHint)).valid).toBe(true);
    const invalidLayoutHint = artifactFor('infographic');
    addField(invalidLayoutHint.content, 'layout_hint', 'freeform');
    expectInvalid('infographic', invalidLayoutHint);
    const nullLayoutHint = artifactFor('infographic');
    addField(nullLayoutHint.content, 'layout_hint', null);
    expectInvalid('infographic', nullLayoutHint);
  });

  it('returns a fresh validated value without changing frozen source metadata', () => {
    const original = artifactFor('audio');
    Object.freeze(original);
    Object.freeze(original.content);
    Object.freeze(original.content.segments);
    original.content.segments.forEach(Object.freeze);
    const before = JSON.stringify(original);
    const result = validateStudioArtifactEdit('audio', before);

    expect(result.valid).toBe(true);
    expect(JSON.stringify(original)).toBe(before);
    if (result.valid) expect(result.artifact).not.toBe(original);
  });
});
