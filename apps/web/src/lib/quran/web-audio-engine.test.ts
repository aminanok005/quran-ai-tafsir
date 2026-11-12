import { createWebAudioEngine } from './web-audio-engine';

function contextStub() {
  const sources: Array<{ start: jest.Mock; stop: jest.Mock; disconnect: jest.Mock }> = [];
  const context = {
    state: 'running',
    currentTime: 0,
    destination: {},
    resume: jest.fn(async () => undefined),
    close: jest.fn(async () => undefined),
    decodeAudioData: jest.fn(async () => ({ duration: 1 } as AudioBuffer)),
    createBufferSource: jest.fn(() => {
      const source = {
        buffer: null,
        playbackRate: { value: 1 },
        connect: jest.fn(),
        start: jest.fn(),
        stop: jest.fn(),
        disconnect: jest.fn(),
      };
      sources.push(source);
      return source;
    }),
    createGain: jest.fn(() => ({
      gain: {
        value: 1,
        setValueAtTime: jest.fn(),
        cancelScheduledValues: jest.fn(),
        linearRampToValueAtTime: jest.fn(),
      },
      connect: jest.fn(),
      disconnect: jest.fn(),
    })),
  } as unknown as AudioContext;
  return { context, sources };
}

describe('Web Audio engine', () => {
  it('decodes and plays a buffer, then stops active sources', async () => {
    const { context, sources } = contextStub();
    const engine = createWebAudioEngine({
      createContext: () => context,
      wait: async () => undefined,
    });
    const buffer = await engine.decode(new ArrayBuffer(4));

    await engine.playBuffer(buffer, 1, new AbortController().signal);
    expect(context.decodeAudioData).toHaveBeenCalledTimes(1);
    expect(sources).toHaveLength(1);
    expect(sources[0].start).toHaveBeenCalledTimes(1);

    engine.stop();
    expect(sources[0].stop).toHaveBeenCalled();
  });

  it('starts armed next buffer during current playback completion', async () => {
    const { context, sources } = contextStub();
    const engine = createWebAudioEngine({
      createContext: () => context,
      wait: async () => undefined,
    });
    const current = { duration: 1 } as AudioBuffer;
    const next = { duration: 1 } as AudioBuffer;

    engine.armNext(next, 1);
    await engine.playBuffer(current, 1, new AbortController().signal);

    expect(sources).toHaveLength(2);
    expect(sources[1].start).toHaveBeenCalledTimes(1);
  });

  it('rejects immediately when signal is already aborted', async () => {
    const { context } = contextStub();
    const engine = createWebAudioEngine({ createContext: () => context });
    const controller = new AbortController();
    controller.abort();

    await expect(
      engine.playBuffer({ duration: 1 } as AudioBuffer, 1, controller.signal),
    ).rejects.toThrow('Playback cancelled');
  });
});
