import { describe, expect, it } from 'vitest';
import { callbackNextUrl, safeNextPath } from '@/lib/auth/redirect';

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
    expect(safeNextPath('/.//evil.example')).toBe('/');
    expect(safeNextPath('/..//evil.example')).toBe('/');
    expect(safeNextPath('/a/..//evil.example')).toBe('/');
    expect(safeNextPath('/%2e//evil.example')).toBe('/');
    expect(safeNextPath('/%2E%2E//evil.example')).toBe('/');
    expect(safeNextPath('/today/..//evil.example?x=1')).toBe('/');
    expect(safeNextPath('/%2e%2e//x')).toBe('/');
    expect(safeNextPath('/./\\x')).toBe('/');
  });

  it('keeps encoded slashes and backslashes on this site', () => {
    expect(safeNextPath('/%2F/evil.example')).toBe('/%2F/evil.example');
    expect(safeNextPath('/%5C/evil.example')).toBe('/%5C/evil.example');
  });
});

describe('callbackNextUrl', () => {
  const origin = 'http://localhost:3000';

  it('refuses a protocol-relative path and keeps encoded same-origin paths', () => {
    expect(callbackNextUrl('//evil.example', origin).href).toBe(`${origin}/`);
    expect(callbackNextUrl('https://evil.example/x', origin).href).toBe(`${origin}/`);

    const encodedSlash = callbackNextUrl('/%2F/evil.example', origin);
    expect(encodedSlash.origin).toBe(origin);
    expect(encodedSlash.pathname).toBe('/%2F/evil.example');

    const encodedBackslash = callbackNextUrl('/%5C/evil.example', origin);
    expect(encodedBackslash.origin).toBe(origin);
    expect(encodedBackslash.pathname).toBe('/%5C/evil.example');
  });
});
