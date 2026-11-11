'use client';

import type { ReaderAudioLanguage, ReaderTranslationVoiceEngine } from './reader-audio-playback';
import type { TranslationAudioCapabilities } from '../api/client';

export interface EditionConfig {
  edition: string;
  language: ReaderAudioLanguage;
  label: string;
}

const EDITION_MAP: Record<ReaderAudioLanguage, EditionConfig> = {
  th: { edition: 'th.thai', language: 'th', label: 'ภาษาไทย' },
  en: { edition: 'en.sahih', language: 'en', label: 'ภาษาอังกฤษ' },
  id: { edition: 'id.indonesian', language: 'id', label: 'ภาษาอินโดนีเซีย' },
};

/** Returns the fixed edition configuration for a supported language. */
export function mapLanguageToEdition(language: ReaderAudioLanguage): EditionConfig | null {
  return EDITION_MAP[language] ?? null;
}

/** Reverse-lookup the language from an edition identifier. */
export function mapEditionToLanguage(edition: string): ReaderAudioLanguage | null {
  for (const config of Object.values(EDITION_MAP)) {
    if (config.edition === edition) return config.language;
  }
  return null;
}

/**
 * True only when TTS is enabled, the selected edition is allowlisted,
 * and its language is supported.
 */
export function isAiAvailable(
  enabledEditions: string[],
  selectedEdition: string,
  supportedLanguages: ReaderAudioLanguage[],
): boolean {
  const language = mapEditionToLanguage(selectedEdition);
  if (!language) return false;
  if (!supportedLanguages.includes(language)) return false;
  if (!enabledEditions.includes(selectedEdition)) return false;
  return true;
}

/**
 * Human-readable reason when AI voice is unavailable for the selected edition.
 * Returns an empty string when AI is available.
 */
export function aiUnavailableReason(
  enabledEditions: string[],
  selectedEdition: string,
  supportedLanguages: ReaderAudioLanguage[],
): string {
  const language = mapEditionToLanguage(selectedEdition);
  if (!language) {
    return `AI voice is not enabled for ${selectedEdition}. Device voice remains available.`;
  }
  if (!supportedLanguages.includes(language)) {
    return `AI voice is not supported for ${selectedEdition}. Device voice remains available.`;
  }
  if (!enabledEditions.includes(selectedEdition)) {
    return `AI voice is not enabled for ${selectedEdition}. Device voice remains available.`;
  }
  return '';
}

export interface TtsBuildSettings {
  edition: EditionConfig | null;
  aiVoiceAvailable: boolean;
  aiVoiceUnavailableReason: string;
}

/**
 * Composes edition configuration and AI availability for the Reader.
 * Replaces the inline capability gating previously computed in page.tsx.
 */
export function buildTtsSettings(
  capabilities: TranslationAudioCapabilities | null,
  selectedEdition: string,
  playbackLanguage: ReaderAudioLanguage,
  capabilityError?: string,
): TtsBuildSettings {
  const edition = mapLanguageToEdition(playbackLanguage);

  if (capabilityError) {
    return {
      edition,
      aiVoiceAvailable: false,
      aiVoiceUnavailableReason: `AI voice unavailable: ${capabilityError}. Device voice remains selected.`,
    };
  }

  if (capabilities === null) {
    return {
      edition,
      aiVoiceAvailable: false,
      aiVoiceUnavailableReason: 'Checking AI voice availability. Device voice remains available.',
    };
  }

  if (!capabilities.available) {
    return {
      edition,
      aiVoiceAvailable: false,
      aiVoiceUnavailableReason: 'AI voice is not configured. Device voice remains available.',
    };
  }

  if (!capabilities.supported_languages.includes(playbackLanguage)) {
    return {
      edition,
      aiVoiceAvailable: false,
      aiVoiceUnavailableReason: `AI voice is not supported for ${playbackLanguage}. Device voice remains available.`,
    };
  }

  if (!capabilities.enabled_editions.includes(selectedEdition)) {
    return {
      edition,
      aiVoiceAvailable: false,
      aiVoiceUnavailableReason: `AI voice is not enabled for ${selectedEdition}. Device voice remains available.`,
    };
  }

  return {
    edition,
    aiVoiceAvailable: true,
    aiVoiceUnavailableReason: '',
  };
}

/**
 * Browsers often lack a Thai device voice, so AI voice is the default whenever it is
 * available. An explicit user choice always wins.
 */
export function resolveTranslationVoiceEngine(
  userChoice: ReaderTranslationVoiceEngine | null,
  aiVoiceAvailable: boolean,
): ReaderTranslationVoiceEngine {
  return userChoice ?? (aiVoiceAvailable ? 'ai' : 'device');
}
