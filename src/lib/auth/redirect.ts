const CONTROL_CHARS = /[\u0000-\u001F\u007F]/;
const ENCODED_CONTROLS = /%(?:0[0-9a-f]|1[0-9a-f]|7f)/i;

/**
 * Allow only a same-origin relative path after login.
 * Control characters are rejected before parsing so a tab or newline cannot
 * change the host. The returned value is pathname + search + hash.
 */
export function safeNextPath(
  value: string | null | undefined,
  base = 'http://localhost:3000',
): string {
  if (!value) return '/';
  if (CONTROL_CHARS.test(value) || ENCODED_CONTROLS.test(value) || value.includes('\\')) {
    return '/';
  }

  let url: URL;
  try {
    url = new URL(value, base);
  } catch {
    return '/';
  }

  if (url.origin !== new URL(base).origin || url.pathname.startsWith('//')) return '/';
  return `${url.pathname}${url.search}${url.hash}`;
}
