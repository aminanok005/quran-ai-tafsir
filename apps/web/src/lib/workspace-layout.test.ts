import {
  getWorkspaceShortcutAction,
  readWorkspaceLayout,
  serializeWorkspaceLayout,
  WorkspaceLayoutState,
  WORKSPACE_LAYOUT_STORAGE_KEY,
} from './workspace-layout';

describe('workspace layout helpers', () => {
  it('uses the existing storage key and three-panel defaults', () => {
    expect(WORKSPACE_LAYOUT_STORAGE_KEY).toBe('quran-workspace-layout');
    expect(readWorkspaceLayout({ getItem: () => null })).toEqual({
      sourcesOpen: true,
      studioOpen: true,
      panelLayout: { sources: 24, reader: 49, studio: 27 },
    });
  });

  it('restores visibility and valid panel sizes while preserving defaults for missing sizes', () => {
    const saved = JSON.stringify({
      sourcesOpen: false,
      studioOpen: true,
      panelLayout: { sources: 30, reader: 45 },
    });

    expect(readWorkspaceLayout({ getItem: () => saved })).toEqual({
      sourcesOpen: false,
      studioOpen: true,
      panelLayout: { sources: 30, reader: 45, studio: 27 },
    });
  });

  it('warns and falls back when persisted JSON is malformed', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});

    expect(readWorkspaceLayout({ getItem: () => '{invalid' })).toEqual({
      sourcesOpen: true,
      studioOpen: true,
      panelLayout: { sources: 24, reader: 49, studio: 27 },
    });
    expect(warn).toHaveBeenCalledWith(
      'Ignoring invalid saved workspace layout',
      expect.any(SyntaxError),
    );
    warn.mockRestore();
  });

  it('ignores non-positive, non-finite, and unknown layout sizes', () => {
    const saved = JSON.stringify({
      panelLayout: { sources: 0, reader: -10, studio: 35, extra: 80 },
    });

    expect(readWorkspaceLayout({ getItem: () => saved }).panelLayout).toEqual({
      sources: 24,
      reader: 49,
      studio: 35,
    });
  });

  it('serializes only the current workspace visibility and layout state', () => {
    const state: WorkspaceLayoutState = {
      sourcesOpen: false,
      studioOpen: false,
      panelLayout: { sources: 30, reader: 45, studio: 25 },
    };

    expect(JSON.parse(serializeWorkspaceLayout(state))).toEqual(state);
  });

  it('maps bracket shortcuts and ignores editable targets', () => {
    expect(getWorkspaceShortcutAction('[', document.body)).toBe('toggle-sources');
    expect(getWorkspaceShortcutAction(']', document.body)).toBe('toggle-studio');
    expect(getWorkspaceShortcutAction('x', document.body)).toBeNull();

    const input = document.createElement('input');
    const textarea = document.createElement('textarea');
    const select = document.createElement('select');
    const contentEditable = document.createElement('div');
    contentEditable.setAttribute('contenteditable', 'true');

    for (const target of [input, textarea, select, contentEditable]) {
      expect(getWorkspaceShortcutAction('[', target)).toBeNull();
      expect(getWorkspaceShortcutAction(']', target)).toBeNull();
    }
  });
});
