export type WorkspacePanelSizes = {
  sources: number;
  reader: number;
  studio: number;
};

export type WorkspaceLayoutState = {
  sourcesOpen: boolean;
  studioOpen: boolean;
  panelLayout: WorkspacePanelSizes;
};

export type WorkspaceShortcutAction = 'toggle-sources' | 'toggle-studio';

export const WORKSPACE_LAYOUT_STORAGE_KEY = 'quran-workspace-layout';

export const DEFAULT_WORKSPACE_LAYOUT: WorkspaceLayoutState = {
  sourcesOpen: true,
  studioOpen: true,
  panelLayout: { sources: 24, reader: 49, studio: 27 },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function defaultLayout(): WorkspaceLayoutState {
  return {
    ...DEFAULT_WORKSPACE_LAYOUT,
    panelLayout: { ...DEFAULT_WORKSPACE_LAYOUT.panelLayout },
  };
}

export function readWorkspaceLayout(
  storage: Pick<Storage, 'getItem'> = window.localStorage,
): WorkspaceLayoutState {
  const saved = storage.getItem(WORKSPACE_LAYOUT_STORAGE_KEY);
  if (!saved) return defaultLayout();

  try {
    const parsed: unknown = JSON.parse(saved);
    if (!isRecord(parsed)) return defaultLayout();

    const layout = defaultLayout();
    if (typeof parsed.sourcesOpen === 'boolean') layout.sourcesOpen = parsed.sourcesOpen;
    if (typeof parsed.studioOpen === 'boolean') layout.studioOpen = parsed.studioOpen;
    if (isRecord(parsed.panelLayout)) {
      for (const key of ['sources', 'reader', 'studio'] as const) {
        const size = parsed.panelLayout[key];
        if (typeof size === 'number' && Number.isFinite(size) && size > 0) {
          layout.panelLayout[key] = size;
        }
      }
    }
    return layout;
  } catch (failure) {
    console.warn('Ignoring invalid saved workspace layout', failure);
    return defaultLayout();
  }
}

export function serializeWorkspaceLayout(state: WorkspaceLayoutState): string {
  return JSON.stringify({
    sourcesOpen: state.sourcesOpen,
    studioOpen: state.studioOpen,
    panelLayout: state.panelLayout,
  });
}

export function getWorkspaceShortcutAction(
  key: string,
  target: EventTarget | null,
): WorkspaceShortcutAction | null {
  if (
    typeof HTMLElement !== 'undefined'
    && target instanceof HTMLElement
    && (
      target.isContentEditable
      || target.getAttribute('contenteditable') === 'true'
      || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
    )
  ) {
    return null;
  }
  if (key === '[') return 'toggle-sources';
  if (key === ']') return 'toggle-studio';
  return null;
}
