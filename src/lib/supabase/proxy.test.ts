import { NextResponse } from 'next/server';
import { describe, expect, it } from 'vitest';
import { withSessionCookies } from '@/lib/supabase/proxy';

describe('withSessionCookies', () => {
  it('copies refreshed cookies onto the redirect', () => {
    const session = NextResponse.next();
    session.cookies.set('sb-access-token', 'refreshed', { path: '/' });
    const redirect = NextResponse.redirect('http://localhost:3000/login?next=%2Ftoday%3Fx%3D1');

    withSessionCookies(redirect, session);

    expect(redirect.headers.get('location')).toContain('next=%2Ftoday%3Fx%3D1');
    expect(redirect.headers.getSetCookie().join(';')).toContain('sb-access-token=refreshed');
  });
});
