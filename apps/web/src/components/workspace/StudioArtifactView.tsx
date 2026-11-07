'use client';

import { useEffect, useState } from 'react';
import type {
  InfographicLayoutHint,
  TargetStudioArtifactData,
} from '../../lib/api/client';

function AudioArtifact({
  data,
}: {
  data: Extract<TargetStudioArtifactData, { kind: 'audio' }>;
}) {
  const [status, setStatus] = useState('');
  const segments = data.artifact.content.segments;

  useEffect(() => () => {
    if (typeof window !== 'undefined') {
      window.speechSynthesis?.cancel();
    }
  }, []);

  const play = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setStatus('Speech playback is not supported in this browser.');
      return;
    }

    const speech = window.speechSynthesis;
    const thaiVoice = speech.getVoices().find((voice) => voice.lang.toLowerCase().startsWith('th'));
    if (!thaiVoice) {
      setStatus('A Thai voice is not available in this browser.');
      return;
    }

    speech.cancel();
    segments.forEach((segment) => {
      const utterance = new SpeechSynthesisUtterance(segment.text);
      utterance.voice = thaiVoice;
      utterance.lang = thaiVoice.lang || 'th-TH';
      speech.speak(utterance);
    });
    setStatus('Audio queued with a Thai voice.');
  };

  const stop = () => {
    if (typeof window !== 'undefined') {
      window.speechSynthesis?.cancel();
    }
    setStatus('Playback stopped.');
  };

  return (
    <section aria-label="Audio overview" className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          aria-label="Play audio"
          onClick={play}
          className="rounded-lg bg-[#0E5E4F] px-3 py-2 text-xs font-semibold text-white hover:bg-[#073B32]"
        >
          Play
        </button>
        <button
          type="button"
          aria-label="Stop audio"
          onClick={stop}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
        >
          Stop
        </button>
      </div>
      {status && <p role="status" className="text-xs text-slate-500">{status}</p>}
      <ol className="space-y-3">
        {segments.map((segment, index) => (
          <li
            key={`${segment.host}-${index}`}
            data-testid="audio-segment"
            className="rounded-xl border border-slate-200 bg-white p-4"
          >
            <p className="text-[10px] font-semibold uppercase tracking-wide text-[#0E5E4F]">
              {segment.host}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-600">{segment.text}</p>
          </li>
        ))}
      </ol>
      <p className="text-[10px] leading-4 text-slate-400">
        Speech is generated locally by your browser; no audio is uploaded.
      </p>
    </section>
  );
}

function QuizArtifact({
  data,
}: {
  data: Extract<TargetStudioArtifactData, { kind: 'quiz' }>;
}) {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const questions = data.artifact.content.questions;
  const score = questions.reduce(
    (total, question, index) => total + (answers[index] === question.answer_index ? 1 : 0),
    0,
  );
  const answeredCount = Object.keys(answers).length;

  return (
    <section aria-label="Quiz" className="space-y-3">
      <p data-testid="quiz-progress" className="text-xs font-medium text-slate-500" aria-live="polite">
        Answered: {answeredCount} / {questions.length} · Score: {score} / {questions.length}
      </p>
      {questions.map((question, questionIndex) => {
        const selectedAnswer = answers[questionIndex];
        const isAnswered = selectedAnswer !== undefined;
        const isCorrect = selectedAnswer === question.answer_index;
        return (
          <section
            key={`${questionIndex}-${question.question}`}
            className="rounded-xl border border-slate-200 bg-white p-4"
          >
            <h3 className="text-sm font-semibold leading-6 text-[#073B32]">
              {questionIndex + 1}. {question.question}
            </h3>
            <div className="mt-3 space-y-2">
              {question.options.map((option, optionIndex) => {
                const selected = selectedAnswer === optionIndex;
                const correct = selected && optionIndex === question.answer_index;
                const wrong = selected && !correct;
                return (
                  <button
                    key={optionIndex}
                    type="button"
                    aria-label={`Question ${questionIndex + 1} option ${optionIndex + 1}`}
                    aria-pressed={selected}
                    onClick={() => setAnswers((current) => ({ ...current, [questionIndex]: optionIndex }))}
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                      correct
                        ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                        : wrong
                          ? 'border-rose-300 bg-rose-50 text-rose-800'
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <span className="mr-2 text-xs text-slate-400">
                      {String.fromCharCode(65 + optionIndex)}.
                    </span>
                    {option}
                  </button>
                );
              })}
            </div>
            {isAnswered && (
              <div className="mt-3 space-y-1">
                <p role="status" className={`text-xs font-semibold ${isCorrect ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {isCorrect ? 'Correct' : 'Not quite'}
                </p>
                <p className="text-xs leading-5 text-slate-500">{question.explanation}</p>
              </div>
            )}
          </section>
        );
      })}
    </section>
  );
}

function infographicLayoutClass(layout: InfographicLayoutHint): string {
  switch (layout) {
    case 'two-column':
      return 'grid grid-cols-1 gap-3 sm:grid-cols-2';
    case 'sequence':
      return 'grid grid-cols-1 gap-3 border-l-2 border-[#C7DED8] pl-4';
    case 'stacked':
      return 'grid grid-cols-1 gap-3';
  }
}

function InfographicArtifact({
  data,
}: {
  data: Extract<TargetStudioArtifactData, { kind: 'infographic' }>;
}) {
  const { takeaway, cards, layout_hint: layoutHint = 'stacked' } = data.artifact.content;

  return (
    <section
      data-testid="infographic"
      data-layout={layoutHint}
      aria-label="Infographic"
      className="space-y-3"
    >
      <p className="rounded-xl border border-[#C7DED8] bg-[#F5F9F7] p-4 text-sm font-semibold leading-6 text-[#073B32]">
        {takeaway}
      </p>
      <div className={infographicLayoutClass(layoutHint)}>
        {cards.map((card, index) => (
          <section key={`${index}-${card.heading}`} className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-semibold text-[#073B32]">
              {layoutHint === 'sequence' && (
                <span className="mr-2 text-xs font-bold text-[#0E5E4F]">{index + 1}.</span>
              )}
              {card.heading}
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
              {card.points.map((point, pointIndex) => <li key={pointIndex}>{point}</li>)}
            </ul>
          </section>
        ))}
      </div>
    </section>
  );
}

export function StudioArtifactView({ data }: { data: TargetStudioArtifactData }) {
  return (
    <article className="space-y-3">
      <header>
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#073B32]">{data.artifact.title}</h3>
            <p className="mt-1 text-[10px] leading-4 text-slate-500">{data.artifact.summary}</p>
          </div>
          <span className="shrink-0 rounded-full bg-violet-100 px-2 py-1 text-[8px] font-bold text-violet-700">
            {data.evidence_status}
          </span>
        </div>
        <nav aria-label="Citations" className="mt-2 flex flex-wrap gap-1.5">
          {data.sources.map((source) => (
            <a
              key={source.id}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full bg-[#E6F4F1] px-2 py-1 text-[9px] font-medium text-[#0E5E4F] hover:underline"
            >
              {source.label}
            </a>
          ))}
        </nav>
      </header>
      {data.kind === 'audio' && <AudioArtifact key={JSON.stringify(data.artifact)} data={data} />}
      {data.kind === 'quiz' && <QuizArtifact key={JSON.stringify(data.artifact)} data={data} />}
      {data.kind === 'infographic' && <InfographicArtifact data={data} />}
    </article>
  );
}
