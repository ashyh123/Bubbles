/** Paths reserved for later milestones. Homepage stays public. */
export const PROTECTED_PATH_PREFIXES = [
  '/today',
  '/habits',
  '/settings',
  '/goals',
  '/categories',
  '/ideas',
] as const;

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PATH_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}
