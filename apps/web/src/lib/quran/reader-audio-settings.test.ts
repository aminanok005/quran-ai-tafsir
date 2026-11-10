import {
  aiUnavailableReason,
  buildTtsSettings,
  isAiAvailable,
  mapEditionToLanguage,
  mapLanguageToEdition,
} from './reader-audio-settings';
import type { TranslationAudioCapabilities } from '../api/client';

function capabilities(overrides: Partial<TranslationAudioCapabilities> = {}): TranslationAudioCapabilities {
  return {
    available: true,
    supported_languages: ['th', 'en', 'id'],
    enabled_editions: ['th.thai', 'en.sahih', 'id.indonesian'],
    ...overrides,
  };
}

describe('mapLanguageToEdition', () => {
  it('maps th to th.thai', () => {
    expect(mapLanguageToEdition('th')).toEqual({
      edition: 'th.thai',
      language: 'th',
      label: 'ภาษาไทย',
    });
  });

  it('maps en to en.sahih', () => {
    expect(mapLanguageToEdition('en')).toEqual({
      edition: 'en.sahih',
      language: 'en',
      label: 'ภาษาอังกฤษ',
    });
  });

  it('maps id to id.indonesian', () => {
    expect(mapLanguageToEdition('id')).toEqual({
      edition: 'id.indonesian',
      language: 'id',
      label: 'ภาษาอินโดนีเซีย',
    });
  });
});

describe('mapEditionToLanguage', () => {
  it('maps th.thai to th', () => {
    expect(mapEditionToLanguage('th.thai')).toBe('th');
  });

  it('maps en.sahih to en', () => {
    expect(mapEditionToLanguage('en.sahih')).toBe('en');
  });

  it('maps id.indonesian to id', () => {
    expect(mapEditionToLanguage('id.indonesian')).toBe('id');
  });

  it('returns null for unknown edition', () => {
    expect(mapEditionToLanguage('ar.alafasy')).toBeNull();
    expect(mapEditionToLanguage('')).toBeNull();
    expect(mapEditionToLanguage('invalid-edition')).toBeNull();
  });
});

describe('isAiAvailable', () => {
  it('returns true when edition is allowlisted and language is supported', () => {
    expect(isAiAvailable(['th.thai', 'en.sahih'], 'th.thai', ['th', 'en'])).toBe(true);
  });

  it('returns true when all three editions are enabled', () => {
    expect(isAiAvailable(['th.thai', 'en.sahih', 'id.indonesian'], 'id.indonesian', ['th', 'en', 'id'])).toBe(true);
  });

  it('returns false when edition is not allowlisted', () => {
    expect(isAiAvailable(['th.thai'], 'en.sahih', ['th', 'en'])).toBe(false);
  });

  it('returns false when language is not supported', () => {
    expect(isAiAvailable(['th.thai'], 'th.thai', ['en'])).toBe(false);
  });

  it('returns false for unknown edition', () => {
    expect(isAiAvailable(['th.thai'], 'ar.alafasy', ['th', 'en'])).toBe(false);
  });

  it('returns false when no editions are enabled', () => {
    expect(isAiAvailable([], 'th.thai', ['th'])).toBe(false);
  });
});

describe('aiUnavailableReason', () => {
  it('returns empty string when AI is available', () => {
    expect(aiUnavailableReason(['th.thai'], 'th.thai', ['th'])).toBe('');
  });

  it('returns reason for unknown edition', () => {
    expect(aiUnavailableReason(['th.thai'], 'ar.alafasy', ['th'])).toContain(
      'AI voice is not enabled for ar.alafasy',
    );
  });

  it('returns reason for unsupported language', () => {
    expect(aiUnavailableReason(['th.thai'], 'th.thai', ['en'])).toContain(
      'AI voice is not supported for th.thai',
    );
  });

  it('returns reason for non-allowlisted edition', () => {
    expect(aiUnavailableReason(['th.thai'], 'en.sahih', ['th', 'en'])).toContain(
      'AI voice is not enabled for en.sahih',
    );
  });
});

describe('buildTtsSettings', () => {
  it('returns edition config and availability when all gates pass', () => {
    const result = buildTtsSettings(capabilities(), 'th.thai', 'th');
    expect(result.edition).toEqual({ edition: 'th.thai', language: 'th', label: 'ภาษาไทย' });
    expect(result.aiVoiceAvailable).toBe(true);
    expect(result.aiVoiceUnavailableReason).toBe('');
  });

  it('returns unavailable when capabilities is null', () => {
    const result = buildTtsSettings(null, 'th.thai', 'th');
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'Checking AI voice availability. Device voice remains available.',
    );
  });

  it('returns unavailable when TTS is not configured', () => {
    const result = buildTtsSettings(capabilities({ available: false }), 'th.thai', 'th');
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'AI voice is not configured. Device voice remains available.',
    );
  });

  it('returns unavailable when edition is not enabled', () => {
    const result = buildTtsSettings(capabilities({ enabled_editions: ['th.thai'] }), 'en.sahih', 'en');
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'AI voice is not enabled for en.sahih. Device voice remains available.',
    );
  });

  it('returns unavailable when language is not supported', () => {
    const result = buildTtsSettings(capabilities({ supported_languages: ['th'] }), 'th.thai', 'en');
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'AI voice is not supported for en. Device voice remains available.',
    );
  });

  it('handles capability error with custom message', () => {
    const result = buildTtsSettings(capabilities(), 'th.thai', 'th', 'Network error');
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'AI voice unavailable: Network error. Device voice remains selected.',
    );
  });

  it('falls back gracefully when selected edition is not in the map', () => {
    const result = buildTtsSettings(capabilities(), 'unknown-edition', 'th');
    expect(result.edition).toEqual({ edition: 'th.thai', language: 'th', label: 'ภาษาไทย' });
    expect(result.aiVoiceAvailable).toBe(false);
    expect(result.aiVoiceUnavailableReason).toBe(
      'AI voice is not enabled for unknown-edition. Device voice remains available.',
    );
  });
});
