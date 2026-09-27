const ID_KEY = /^(id|.+Id|.+_id)$/;
const COUNT_KEY = /^(count|.+Count|.+_count)$/;
const LATENCY_KEYS = new Set([
  'latency',
  'latencyMs',
  'latency_ms',
  'durationMs',
  'duration_ms',
]);
const ENUM_KEYS = new Set([
  'source',
  'status',
  'provider',
  'action',
  'kind',
  'size',
  'mode',
  'category',
  'category_status',
  'breakdown_status',
  'breakdown_reason',
  'breakdown_error',
  'question_key',
]);

function isAllowedKey(key: string): boolean {
  return ID_KEY.test(key) || COUNT_KEY.test(key) || LATENCY_KEYS.has(key) || ENUM_KEYS.has(key);
}

/**
 * Keep only identifiers, counts, latency, and known enums.
 * Every other key is dropped, including nested private text.
 */
export function redactForLog(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactForLog(item));
  }
  if (value && typeof value === 'object') {
    const redacted: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value)) {
      if (!isAllowedKey(key)) continue;
      redacted[key] = redactForLog(child);
    }
    return redacted;
  }
  return value;
}

/** Structured log line. `event` is a stable identifier, never the idea itself. */
export function logEvent(event: string, fields: Record<string, unknown> = {}): void {
  const safe = redactForLog(fields);
  console.info(JSON.stringify({ event, ...(safe as Record<string, unknown>) }));
}
