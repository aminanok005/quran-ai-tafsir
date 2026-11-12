export const AUDIO_CACHE_VERSION = 1;

export type AudioCacheSource = "recitation" | "translation-ai";
export type AudioCacheLanguage = "ar" | "th" | "en" | "id";

export interface AudioCacheKeyParts {
  source: AudioCacheSource;
  reciterOrVoice: string;
  language: AudioCacheLanguage;
  surah: number;
  ayah: number;
  format: string;
  speed?: number;
}

export function buildAudioCacheKey(parts: AudioCacheKeyParts): string {
  const speedPart =
    parts.source === "translation-ai" ? String(parts.speed ?? 1) : "native";
  return [
    `v${AUDIO_CACHE_VERSION}`,
    parts.source,
    encodeURIComponent(parts.reciterOrVoice),
    parts.language,
    String(parts.surah),
    String(parts.ayah),
    speedPart,
    parts.format.replace(/[^a-z0-9]+/gi, ""),
  ].join(":");
}

export function formatFromContentType(contentType: string | null | undefined): string {
  const type = contentType?.split(";", 1)[0]?.trim().toLowerCase() ?? "";
  if (type === "audio/mpeg" || type === "audio/mp3") return "mp3";
  if (type === "audio/wav" || type === "audio/wave" || type === "audio/x-wav") return "wav";
  if (type === "audio/ogg") return "ogg";
  if (type === "audio/mp4" || type === "audio/aac") return "m4a";
  return "bin";
}

export function formatFromUrl(url: string): string {
  try {
    const path = new URL(url, "https://local.invalid").pathname.toLowerCase();
    const match = path.match(/\.([a-z0-9]+)$/);
    return match?.[1] ?? "mp3";
  } catch {
    return "mp3";
  }
}
