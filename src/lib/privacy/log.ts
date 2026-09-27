const REDACTED = '[redacted]';

const SENSITIVE_KEYS = new Set([
  'content',
  'text',
  'idea',
  'note',
  'title',
  'reason_text',
  'body',
  'prompt',
]);

function isSensitiveKey(key: string): boolean {
  return SENSITIVE_KEYS.has(key.toLowerCase());
}

/** Strip idea text and similar private fields before anything is written to logs. */
export function redactForLog(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactForLog(item));
  }
  if (value && typeof value === 'object') {
    const redacted: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value)) {
      redacted[key] = isSensitiveKey(key) ? REDACTED : redactForLog(child);
    }
    return redacted;
  }
  return value;
}

/**
 * Structured log line. `event` must be a stable identifier, never the idea itself.
 * Fields named content/text/idea/note/title/reason_text/body/prompt are replaced.
 */
export function logEvent(event: string, fields: Record<string, unknown> = {}): void {
  const safe = redactForLog(fields);
  console.info(JSON.stringify({ event, ...(safe as Record<string, unknown>) }));
}
