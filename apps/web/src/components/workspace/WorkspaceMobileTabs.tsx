'use client';

export type WorkspaceMobileView = 'reader' | 'sources' | 'dialogue' | 'studio';

const tabs: Array<[WorkspaceMobileView, string]> = [
  ['reader', 'อ่าน'],
  ['sources', 'Sources'],
  ['dialogue', 'ตัฟซีร'],
  ['studio', 'Studio'],
];

export function WorkspaceMobileTabs({
  activeView,
  onSelect,
}: {
  activeView: WorkspaceMobileView;
  onSelect: (view: WorkspaceMobileView) => void;
}) {
  return (
    <div data-testid="workspace-mobile-tabs" className="flex shrink-0 items-center justify-center gap-1 border-b border-[#dce4e1] bg-white px-2 py-2">
      {tabs.map(([view, label]) => (
        <button
          key={view}
          type="button"
          aria-current={activeView === view ? 'page' : undefined}
          onClick={() => onSelect(view)}
          className={`rounded-lg px-3 py-2 text-xs font-semibold ${
            activeView === view ? 'bg-[#E6F4F1] text-[#0E5E4F]' : 'text-slate-500'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
