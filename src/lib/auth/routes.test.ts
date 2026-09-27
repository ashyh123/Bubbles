import { describe, expect, it } from 'vitest';
import { isProtectedPath } from '@/lib/auth/routes';

describe('isProtectedPath', () => {
  it('protects reserved app sections', () => {
    expect(isProtectedPath('/today')).toBe(true);
    expect(isProtectedPath('/habits/new')).toBe(true);
    expect(isProtectedPath('/settings')).toBe(true);
  });

  it('leaves the capture page and auth routes public', () => {
    expect(isProtectedPath('/')).toBe(false);
    expect(isProtectedPath('/login')).toBe(false);
    expect(isProtectedPath('/auth/callback')).toBe(false);
    expect(isProtectedPath('/today-archive')).toBe(false);
  });
});
