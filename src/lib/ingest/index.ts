import type { BubbleSource } from '@/lib/db/enums';

/** Future POST /api/v1/ingest. Do not log `text`. */
export const INGEST_PATH = '/api/v1/ingest';

export const INGEST_SOURCES = ['web', 'shortcut', 'assistant', 'mcp'] as const;
export type IngestSource = (typeof INGEST_SOURCES)[number];

export interface IngestRequest {
  text: string;
  source: IngestSource;
  occurred_at?: string;
  meta?: Record<string, unknown>;
}

export interface IngestAccepted {
  bubble_id: string;
  status: 'pending';
}

const BUBBLE_SOURCE_BY_INGEST: Record<IngestSource, BubbleSource> = {
  web: 'web',
  shortcut: 'shortcut',
  assistant: 'api',
  mcp: 'mcp',
};

export function ingestSourceToBubbleSource(source: IngestSource): BubbleSource {
  return BUBBLE_SOURCE_BY_INGEST[source];
}
