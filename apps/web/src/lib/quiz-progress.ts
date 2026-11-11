export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface QuizAttempt {
  score: number;
  total: number;
  at: number;
}

export interface QuizHistory {
  attempts: QuizAttempt[];
  best: number | null;
}

const PREFIX = 'quran-ai:quiz-progress:';
const MAX_ATTEMPTS = 20;

function readAttempts(storage: StorageLike, key: string): QuizAttempt[] {
  try {
    const parsed: unknown = JSON.parse(storage.getItem(PREFIX + key) ?? '[]');
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item): item is QuizAttempt =>
        typeof item?.score === 'number' && typeof item?.total === 'number' && typeof item?.at === 'number',
    );
  } catch {
    return [];
  }
}

export function getQuizHistory(storage: StorageLike, key: string): QuizHistory {
  const attempts = readAttempts(storage, key);
  return {
    attempts,
    best: attempts.length ? Math.max(...attempts.map((attempt) => attempt.score)) : null,
  };
}

export function recordQuizResult(
  storage: StorageLike,
  key: string,
  result: { score: number; total: number },
  now: number = Date.now(),
): void {
  const { score, total } = result;
  if (!Number.isInteger(score) || !Number.isInteger(total) || total < 1 || score < 0 || score > total) return;
  try {
    const attempts = [...readAttempts(storage, key), { score, total, at: now }].slice(-MAX_ATTEMPTS);
    storage.setItem(PREFIX + key, JSON.stringify(attempts));
  } catch {
    // Progress is a convenience; quota or privacy-mode failures must not break the quiz.
  }
}
