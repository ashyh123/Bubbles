import { afterEach, describe, expect, it, vi } from 'vitest';
import { logEvent, redactForLog } from '@/lib/privacy/log';

const PRIVATE_IDEA = '想每天早上背10个单词';

describe('redactForLog', () => {
  it('keeps ids, counts, latency, and enums, and drops everything else', () => {
    expect(
      redactForLog({
        bubbleId: 'bubble_1',
        content: PRIVATE_IDEA,
        count: 2,
        latency_ms: 40,
        source: 'shortcut',
        nested: { text: 'secret note', source: 'web' },
      }),
    ).toEqual({
      bubbleId: 'bubble_1',
      count: 2,
      latency_ms: 40,
      source: 'shortcut',
    });
  });
});

describe('logEvent', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not print idea text', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {});
    logEvent('bubble.created', {
      bubbleId: 'bubble_1',
      content: PRIVATE_IDEA,
      count: 1,
      latency_ms: 12,
      source: 'web',
      meta: { idea: 'another private line' },
    });

    const line = spy.mock.calls[0]?.[0];
    expect(typeof line).toBe('string');
    expect(line).not.toContain(PRIVATE_IDEA);
    expect(line).not.toContain('another private line');
    expect(line).not.toContain('content');
    expect(line).toContain('bubble.created');
    expect(line).toContain('bubble_1');
    expect(line).toContain('"count":1');
    expect(line).toContain('"latency_ms":12');
    expect(line).toContain('"source":"web"');
  });
});
