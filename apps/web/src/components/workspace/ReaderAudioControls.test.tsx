import { fireEvent, render, screen, within } from '@testing-library/react';
import { useState } from 'react';
import { ReaderAudioControls } from './ReaderAudioControls';

describe('ReaderAudioControls', () => {
  const props = {
    mode: 'recitation' as const,
    language: 'th' as const,
    playbackState: 'idle' as const,
    status: 'หยุดการเล่นแล้ว',
    settingsOpen: false,
    translationVoiceEngine: 'device' as const,
    speed: 1 as const,
    aiVoiceAvailable: false,
    aiVoiceUnavailableReason: 'AI audio is not configured; device voice is selected.',
    onSettingsOpenChange: jest.fn(),
    onModeChange: jest.fn(),
    onLanguageChange: jest.fn(),
    onTranslationVoiceEngineChange: jest.fn(),
    onSpeedChange: jest.fn(),
    onListen: jest.fn(),
    onAuto: jest.fn(),
    onStop: jest.fn(),
  };

  beforeEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  it('renders localized playback actions and status', () => {
    const { container } = render(<ReaderAudioControls {...props} />);

    const listenButton = screen.getByRole('button', { name: 'ฟังเสียง' });
    expect(listenButton.getAttribute('aria-pressed')).toBe('false');
    const continuousSwitch = screen.getByRole('switch', { name: /เล่นต่อเนื่อง/ });
    expect(continuousSwitch.getAttribute('aria-checked')).toBe('false');
    expect(screen.getByText('เล่นอายะฮ์ถัดไปอัตโนมัติ').id).toBe(continuousSwitch.getAttribute('aria-describedby'));
    expect(screen.getByText('เล่นอายะฮ์ถัดไปอัตโนมัติ')).toBeTruthy();
    expect(screen.getByRole('status').getAttribute('aria-live')).toBe('polite');
    expect(screen.getByRole('status').textContent).toBe('หยุดการเล่นแล้ว');
    expect(screen.queryByRole('combobox', { name: 'ภาษาเสียงแปล' })).toBeNull();
    expect(screen.getByRole('group', { name: 'การทำงานของอายะฮ์' })).toBeTruthy();
    expect(container.firstChild instanceof HTMLElement).toBe(true);
  });

  it('places audio actions alongside localized note and AI actions', () => {
    render(
      <ReaderAudioControls {...props}>
        <button type="button" data-reader-action="save" className="reader-action-button reader-action-secondary">บันทึกลงโน้ต</button>
        <button type="button" data-reader-action="ask" className="reader-action-button reader-action-secondary">ถาม AI</button>
      </ReaderAudioControls>,
    );

    const toolbar = within(screen.getByRole('group', { name: 'การทำงานของอายะฮ์' }));
    expect(toolbar.getByRole('button', { name: 'บันทึกลงโน้ต' })).toBeTruthy();
    expect(toolbar.getByRole('button', { name: 'ถาม AI' })).toBeTruthy();
    expect(toolbar.getByRole('button', { name: 'ฟังเสียง' }).classList.contains('reader-action-button')).toBe(true);
    expect(toolbar.getByRole('button', { name: 'บันทึกลงโน้ต' }).classList.contains('reader-action-button')).toBe(true);
    expect(toolbar.getByRole('button', { name: 'ถาม AI' }).classList.contains('reader-action-button')).toBe(true);
  });

  it('keeps playback options collapsed until the settings summary is opened', () => {
    const view = render(<ReaderAudioControls {...props} />);

    expect(screen.queryByRole('combobox', { name: 'รูปแบบการเล่นเสียง' })).toBeNull();
    expect(screen.queryByRole('dialog', { name: 'ตั้งค่าเสียง' })).toBeNull();
    const settingsButton = screen.getByRole('button', { name: /ตั้งค่าเสียง/i });
    expect(settingsButton.getAttribute('aria-expanded')).toBe('false');
    expect(settingsButton.textContent).toContain('ภาษาไทย');
    expect(settingsButton.textContent).toContain('อัลอะฟาซี');

    fireEvent.click(settingsButton);

    expect(props.onSettingsOpenChange).toHaveBeenCalledWith(true);
    view.rerender(
      <ReaderAudioControls {...props} settingsOpen />,
    );
    expect(settingsButton.getAttribute('aria-expanded')).toBe('true');
    expect(screen.getByRole('dialog', { name: 'ตั้งค่าเสียง' })).toBeTruthy();
  });

  it('renders the narrow settings sheet outside the ayah container', () => {
    const measureElement = jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect');
    measureElement.mockImplementation(function getBoundingClientRect(this: HTMLElement) {
      const width = this.classList.contains('reader-ayah-card') ? 480 : 0;
      const height = this.classList.contains('reader-ayah-card') ? 200 : 0;
      return {
        x: 0,
        y: 0,
        width,
        height,
        top: 0,
        right: width,
        bottom: height,
        left: 0,
        toJSON: () => ({}),
      };
    });

    render(
      <div className="reader-ayah-card">
        <ReaderAudioControls {...props} settingsOpen />
      </div>,
    );

    const dialog = screen.getByRole('dialog', { name: 'ตั้งค่าเสียง' });
    const closeButton = within(dialog).getByRole('button', { name: 'ปิดการตั้งค่าเสียง' });
    const lastControl = within(dialog).getByRole('combobox', { name: 'ความเร็วเสียง' });
    expect(dialog.closest('.reader-ayah-card')).toBeNull();
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.parentElement?.classList.contains('reader-audio-settings-portal')).toBe(true);
    expect(document.activeElement).toBe(closeButton);

    lastControl.focus();
    fireEvent.keyDown(lastControl, { key: 'Tab' });
    expect(document.activeElement).toBe(closeButton);
    closeButton.focus();
    fireEvent.keyDown(closeButton, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(lastControl);
    measureElement.mockRestore();
  });

  it.each([
    [480, true],
    [720, false],
    [850, false],
  ])('uses the viewport-safe settings sheet only below 720px (card %ipx)', (cardWidth, isSheet) => {
    jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function getBoundingClientRect(this: HTMLElement) {
      const width = this.classList.contains('reader-ayah-card') ? cardWidth : 0;
      const height = this.classList.contains('reader-ayah-card') ? 200 : 0;
      return {
        x: 0,
        y: 0,
        width,
        height,
        top: 0,
        right: width,
        bottom: height,
        left: 0,
        toJSON: () => ({}),
      };
    });

    render(
      <div className="reader-ayah-card">
        <ReaderAudioControls {...props} settingsOpen />
      </div>,
    );

    const dialog = screen.getByRole('dialog', { name: 'ตั้งค่าเสียง' });
    expect(dialog.parentElement?.classList.contains('reader-audio-settings-portal')).toBe(isSheet);
    expect(dialog.getAttribute('aria-modal') === 'true').toBe(isSheet);
  });

  it('shows translation language and selects the requested options', () => {
    render(<ReaderAudioControls {...props} settingsOpen mode="recitation-then-translation" language="id" />);

    expect((screen.getByRole('combobox', { name: 'รูปแบบการเล่นเสียง' }) as HTMLSelectElement).value).toBe('recitation-then-translation');
    expect((screen.getByRole('combobox', { name: 'ภาษาเสียงแปล' }) as HTMLSelectElement).value).toBe('id');
    fireEvent.change(screen.getByRole('combobox', { name: 'รูปแบบการเล่นเสียง' }), { target: { value: 'translation' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'ภาษาเสียงแปล' }), { target: { value: 'en' } });
    expect(props.onModeChange).toHaveBeenCalledWith('translation');
    expect(props.onLanguageChange).toHaveBeenCalledWith('en');
  });

  it('lets users select an available voice engine and speed, and explains unavailable AI voice', () => {
    const view = render(<ReaderAudioControls {...props} settingsOpen mode="translation" />);

    const engine = screen.getByRole('combobox', { name: 'เสียงแปล' }) as HTMLSelectElement;
    expect(engine.value).toBe('device');
    expect(screen.getByText(props.aiVoiceUnavailableReason)).toBeTruthy();
    expect((screen.getByRole('option', { name: /เสียง AI/i }) as HTMLOptionElement).disabled).toBe(true);

    view.rerender(
      <ReaderAudioControls
        {...props}
        settingsOpen
        mode="translation"
        aiVoiceAvailable
        aiVoiceUnavailableReason=""
      />,
    );
    fireEvent.change(screen.getByRole('combobox', { name: 'เสียงแปล' }), {
      target: { value: 'ai' },
    });
    fireEvent.change(screen.getByRole('combobox', { name: 'ความเร็วเสียง' }), {
      target: { value: '1.15' },
    });

    expect(props.onTranslationVoiceEngineChange).toHaveBeenCalledWith('ai');
    expect(props.onSpeedChange).toHaveBeenCalledWith(1.15);
  });

  it('keeps the compact audio summary to the reader, language, and speed', () => {
    render(<ReaderAudioControls {...props} mode="translation" />);

    const settingsButton = screen.getByRole('button', { name: /ตั้งค่าเสียง/i });
    expect(settingsButton.textContent).toContain('อัลอะฟาซี');
    expect(settingsButton.textContent).toContain('ภาษาไทย');
    expect(settingsButton.textContent).toContain('1x');
  });

  it('switches the playback action to Stop and announces pressed state while playing', () => {
    render(<ReaderAudioControls {...props} playbackState="single" />);
    const stopButton = screen.getByRole('button', { name: 'หยุด' });
    expect(stopButton.getAttribute('aria-pressed')).toBe('true');
    fireEvent.click(stopButton);
    expect(props.onStop).toHaveBeenCalled();
  });

  it('toggles continuous playback using an accessible switch', () => {
    render(<ReaderAudioControls {...props} playbackState="auto" />);
    const continuousSwitch = screen.getByRole('switch', { name: /เล่นต่อเนื่อง/ });
    expect(continuousSwitch.getAttribute('aria-checked')).toBe('true');
    fireEvent.click(continuousSwitch);
    expect(props.onStop).toHaveBeenCalled();
  });

  it('closes the settings dialog on Escape and returns focus to the trigger', () => {
    const measureElement = jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect');
    measureElement.mockImplementation(function getBoundingClientRect(this: HTMLElement) {
      const width = this.classList.contains('reader-ayah-card') ? 480 : 0;
      const height = this.classList.contains('reader-ayah-card') ? 200 : 0;
      return {
        x: 0,
        y: 0,
        width,
        height,
        top: 0,
        right: width,
        bottom: height,
        left: 0,
        toJSON: () => ({}),
      };
    });

    function StatefulControls() {
      const [settingsOpen, setSettingsOpen] = useState(false);
      return (
        <div className="reader-ayah-card">
          <ReaderAudioControls
            {...props}
            settingsOpen={settingsOpen}
            onSettingsOpenChange={setSettingsOpen}
          />
        </div>
      );
    }

    render(<StatefulControls />);
    const trigger = screen.getByRole('button', { name: /ตั้งค่าเสียง/i });
    fireEvent.click(trigger);
    const dialog = screen.getByRole('dialog', { name: 'ตั้งค่าเสียง' });
    fireEvent.keyDown(within(dialog).getByRole('combobox', { name: 'ผู้อ่าน' }), { key: 'Escape' });

    expect(screen.queryByRole('dialog', { name: 'ตั้งค่าเสียง' })).toBeNull();
    expect(document.activeElement).toBe(trigger);
    measureElement.mockRestore();
  });
});
