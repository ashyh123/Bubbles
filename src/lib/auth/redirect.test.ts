import { describe, expect, it } from 'vitest';
import { safeNextPath } from '@/lib/auth/redirect';

describe('safeNextPath', () => {
  it('keeps in-app paths', () => {
    expect(safeNextPath('/today')).toBe('/today');
    expect(safeNextPath('/ideas/abc')).toBe('/ideas/abc');
  });

  it('drops external redirects', () => {
    expect(safeNextPath(null)).toBe('/');
    expect(safeNextPath('https://evil.example')).toBe('/');
    expect(safeNextPath('//evil.example')).toBe('/');
    expect(safeNextPath('/\\evil.example')).toBe('/');
  });
});
