'use client';

import { useState } from 'react';
import type { LearningBlock } from '../../lib/strapi';

function QuizBlock({ block }: { block: Extract<LearningBlock, { kind: 'quiz' }> }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const selectedOption = block.options.find((option) => option.id === selected);

  return (
    <section className="rounded-2xl border border-[#dce4e1] bg-white p-5">
      <p className="text-xs font-bold text-violet-800">แบบฝึกหัดเพื่อการเรียนรู้จากหลักสูตร</p>
      <h3 className="mt-2 text-base font-semibold leading-7 text-slate-900">{block.question}</h3>
      <fieldset className="mt-4 space-y-2">
        <legend className="sr-only">ตัวเลือกคำตอบ</legend>
        {block.options.map((option) => (
          <label key={option.id} className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 text-sm hover:bg-slate-50">
            <input
              type="radio"
              name={`quiz-${block.id}`}
              checked={selected === option.id}
              disabled={submitted}
              onChange={() => setSelected(option.id)}
              className="mt-1 accent-[#0E5E4F]"
            />
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>
      {!submitted ? (
        <button
          type="button"
          disabled={selected === null || block.options.length === 0}
          onClick={() => setSubmitted(true)}
          className="mt-4 rounded-full bg-[#0E5E4F] px-4 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          ตรวจคำตอบ
        </button>
      ) : (
        <div className={`mt-4 rounded-xl p-3 text-sm ${selectedOption?.correct ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'}`} role="status">
          <p className="font-semibold">{selectedOption?.correct ? 'ตอบถูกต้อง' : 'คำตอบนี้ยังไม่ถูกต้อง'}</p>
          {selectedOption?.feedback && <p className="mt-1">{selectedOption.feedback}</p>}
          {block.explanation && <p className="mt-2">{block.explanation}</p>}
        </div>
      )}
    </section>
  );
}

export function CourseBlocks({ blocks }: { blocks: LearningBlock[] }) {
  if (blocks.length === 0) {
    return <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">บทนี้ยังไม่มีเนื้อหา</p>;
  }

  return (
    <div className="space-y-4">
      {blocks.map((block, index) => {
        if (block.kind === 'quiz') return <QuizBlock key={`${block.id}-${index}`} block={block} />;
        if (block.kind === 'vocabulary') {
          return (
            <section key={`${block.id}-${index}`} className="rounded-2xl border border-[#dce4e1] bg-white p-5">
              <h3 className="font-semibold text-slate-900">{block.title || 'คำศัพท์'}</h3>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {block.pairs.map((pair) => (
                  <div key={pair.id} className="rounded-xl bg-[#F5F7F6] p-3">
                    <p dir="rtl" className="text-right text-lg font-semibold text-[#073B32]">{pair.arabicWord}</p>
                    {pair.rootWord && <p className="mt-1 text-xs text-slate-500">รากศัพท์: {pair.rootWord}</p>}
                    <p className="mt-1 text-sm text-slate-700">{pair.meaningTh}</p>
                  </div>
                ))}
              </div>
            </section>
          );
        }
        if (block.kind === 'theory') {
          return (
            <section key={`${block.id}-${index}`} className="rounded-2xl border border-[#dce4e1] bg-white p-5">
              {block.title && <h3 className="font-semibold text-slate-900">{block.title}</h3>}
              {block.arabicText && <p dir="rtl" className="mt-4 text-right text-2xl leading-[2.4] text-[#073B32]">{block.arabicText}</p>}
              {block.translationTh && <p className="mt-3 text-sm leading-7 text-slate-700">{block.translationTh}</p>}
              {block.explanation && <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-600">{block.explanation}</p>}
              {block.citationReference && <p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">อ้างอิง: {block.citationReference}</p>}
            </section>
          );
        }
        return (
          <p key={`${block.id}-${index}`} className="rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
            ยังไม่รองรับบล็อกเนื้อหาประเภท {block.component}
          </p>
        );
      })}
    </div>
  );
}
