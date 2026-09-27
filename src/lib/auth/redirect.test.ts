import { describe, expect, it } from 'vitest';
import { safeNextPath } from '@/lib/auth/redirect';

describe('safeNextPath', () => {
  it('keeps in-app paths, including the query string and hash', () => {
    expect(safeNextPath('/today')).toBe('/today');
    expect(safeNextPath('/ideas/abc')).toBe('/ideas/abc');
    expect(safeNextPath('/today?x=1#done')).toBe('/today?x=1#done');
  });

  it('drops external redirects and control characters', () => {
    expect(safeNextPath(null)).toBe('/');
    expect(safeNextPath('https://evil.example')).toBe('/');
    expect(safeNextPath('//evil.example')).toBe('/');
    expect(safeNextPath('/\\evil.example')).toBe('/');
    expect(safeNextPath('/\t/evil.example')).toBe('/');
    expect(safeNextPath('/%09/evil.example')).toBe('/');
    expect(safeNextPath('/%0a/evil.example')).toBe('/');
    expect(safeNextPath('/%0d/evil.example')).toBe('/');
    expect(safeNextPath('/%0A/evil.example')).toBe('/');
  });
});
