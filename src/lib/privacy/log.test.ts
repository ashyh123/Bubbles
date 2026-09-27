import { afterEach, describe, expect, it, vi } from 'vitest';
import { logEvent, redactForLog } from '@/lib/privacy/log';

const PRIVATE_IDEA = '想每天早上背10个单词';

describe('redactForLog', () => {
  it('replaces private text fields and keeps identifiers', () => {
    expect(
      redactForLog({
        bubbleId: 'bubble_1',
        content: PRIVATE_IDEA,
        nested: { text: 'secret note', source: 'web' },
        items: [{ title: '睡前拉伸' }],
      }),
    ).toEqual({
      bubbleId: 'bubble_1',
      content: '[redacted]',
      nested: { text: '[redacted]', source: 'web' },
      items: [{ title: '[redacted]' }],
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
      meta: { idea: 'another private line' },
    });

    const line = spy.mock.calls[0]?.[0];
    expect(typeof line).toBe('string');
    expect(line).not.toContain(PRIVATE_IDEA);
    expect(line).not.toContain('another private line');
    expect(line).toContain('bubble.created');
    expect(line).toContain('bubble_1');
    expect(line).toContain('[redacted]');
  });
});
