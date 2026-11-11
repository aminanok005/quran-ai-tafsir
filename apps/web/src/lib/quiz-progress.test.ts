import { getQuizHistory, recordQuizResult, type StorageLike } from './quiz-progress';

function memoryStorage(): StorageLike {
  const data = new Map<string, string>();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => void data.set(key, value),
  };
}

describe('quiz progress', () => {
  it('records results newest-last and reports best score', () => {
    const storage = memoryStorage();
    recordQuizResult(storage, 'k', { score: 2, total: 5 }, 1);
    recordQuizResult(storage, 'k', { score: 4, total: 5 }, 2);
    const history = getQuizHistory(storage, 'k');
    expect(history.attempts.map((a) => a.score)).toEqual([2, 4]);
    expect(history.best).toBe(4);
  });

  it('keeps only the latest 20 attempts', () => {
    const storage = memoryStorage();
    for (let i = 0; i < 25; i += 1) recordQuizResult(storage, 'k', { score: i % 6, total: 5 }, i);
    expect(getQuizHistory(storage, 'k').attempts).toHaveLength(20);
  });

  it('ignores corrupt stored data and invalid results', () => {
    const storage = memoryStorage();
    storage.setItem('quran-ai:quiz-progress:k', '{not json');
    expect(getQuizHistory(storage, 'k')).toEqual({ attempts: [], best: null });
    recordQuizResult(storage, 'k', { score: 9, total: 5 }, 1);
    expect(getQuizHistory(storage, 'k').attempts).toEqual([]);
  });

  it('does not throw when storage is unavailable', () => {
    const broken: StorageLike = {
      getItem: () => { throw new Error('denied'); },
      setItem: () => { throw new Error('denied'); },
    };
    expect(() => recordQuizResult(broken, 'k', { score: 1, total: 5 }, 1)).not.toThrow();
    expect(getQuizHistory(broken, 'k').attempts).toEqual([]);
  });
});
