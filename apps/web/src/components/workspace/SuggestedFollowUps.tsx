'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import type { SuggestedFollowUp } from '../../lib/api/client';

type Props = {
  suggestions: SuggestedFollowUp[];
  status: 'loading' | 'success' | 'error';
  onAsk: (prompts: string[]) => void;
  onRefresh: () => void;
};

const categoryLabels: Record<SuggestedFollowUp['category'], string> = {
  deepen: 'เจาะลึก',
  compare: 'เปรียบเทียบ',
  context: 'บริบท',
  review: 'ทบทวน',
  source: 'ต้นฉบับ',
};

export function SuggestedFollowUps({ suggestions, status, onAsk, onRefresh }: Props) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  if (status === 'error' || (status === 'success' && suggestions.length === 0)) return null;

  if (status === 'loading') {
    return (
      <section aria-label="คำแนะนำคำถามต่อไป" className="space-y-3">
        <div>
          <h3 className="text-sm font-bold text-surface-900">ต่อไปคุณอาจสนใจ</h3>
          <p className="mt-1 text-xs text-surface-600">เลือกได้หลายข้อ แล้วกดถามต่อ</p>
        </div>
        <div
          aria-label="กำลังโหลดคำแนะนำ"
          className="grid grid-cols-2 gap-2"
          data-testid="suggestion-skeleton-grid"
          role="status"
        >
          {[0, 1, 2, 3].map((item) => (
            <div
              aria-hidden="true"
              className="min-h-28 animate-pulse rounded-xl border border-surface-200 bg-surface-50 p-3"
              key={item}
            >
              <div className="h-4 w-20 rounded bg-surface-200" />
              <div className="mt-3 h-3 w-full rounded bg-surface-200" />
              <div className="mt-2 h-3 w-2/3 rounded bg-surface-200" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  const selectedSuggestions = selectedIds.flatMap((id) => {
    const suggestion = suggestions.find((item) => item.id === id);
    return suggestion ? [suggestion] : [];
  });
  const toggleSuggestion = (id: string) => {
    setSelectedIds((current) => current.includes(id)
      ? current.filter((value) => value !== id)
      : [...current, id]);
  };
  const askSelected = () => {
    if (selectedSuggestions.length === 0) return;
    const prompts = selectedSuggestions.map((item) => item.prompt);
    setSelectedIds([]);
    onAsk(prompts);
  };

  return (
    <section aria-label="คำแนะนำคำถามต่อไป" className="space-y-3">
      <div>
        <h3 className="text-sm font-bold text-surface-900">ต่อไปคุณอาจสนใจ</h3>
        <p className="mt-1 text-xs text-surface-600">เลือกได้หลายข้อ แล้วกดถามต่อ</p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {suggestions.slice(0, 4).map((suggestion) => {
          const selected = selectedIds.includes(suggestion.id);
          return (
            <button
              aria-pressed={selected}
              className={`relative min-w-0 rounded-xl border bg-white p-3 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-800 ${
                selected
                  ? 'border-primary-800 ring-1 ring-primary-800'
                  : 'border-surface-200 hover:border-primary-800'
              }`}
              key={suggestion.id}
              onClick={() => toggleSuggestion(suggestion.id)}
              type="button"
            >
              <span className="flex items-start justify-between gap-2">
                <span className="rounded-full bg-primary-50 px-2 py-1 text-[11px] font-semibold text-primary-800">
                  {categoryLabels[suggestion.category]}
                </span>
                {selected && <Check aria-hidden="true" className="h-4 w-4 shrink-0 text-primary-800" />}
              </span>
              {suggestion.category === 'review' && (
                <span className="mt-2 inline-flex rounded-full bg-accent-50 px-2 py-1 text-[10px] font-bold text-accent-800">
                  AI-SYNTHESIS
                </span>
              )}
              <span className="mt-2 block break-words text-sm font-semibold leading-5 text-surface-900">
                {suggestion.title}
              </span>
              <span className="mt-2 block text-xs text-surface-600">
                อิงจาก {suggestion.basisCount} แหล่ง
              </span>
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          className="min-h-11 rounded-xl bg-primary-800 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-800 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={selectedSuggestions.length === 0}
          onClick={askSelected}
          type="button"
        >
          ถามข้อที่เลือก ({selectedSuggestions.length})
        </button>
        <button
          className="min-h-11 rounded-xl px-3 py-2 text-sm font-semibold text-primary-800 hover:bg-primary-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-800 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={selectedSuggestions.length === 0}
          onClick={() => setSelectedIds([])}
          type="button"
        >
          ล้างตัวเลือก
        </button>
        <button
          className="min-h-11 rounded-xl px-3 py-2 text-sm font-semibold text-primary-800 hover:bg-primary-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-800"
          onClick={onRefresh}
          type="button"
        >
          คำแนะนำชุดอื่น
        </button>
      </div>
    </section>
  );
}
