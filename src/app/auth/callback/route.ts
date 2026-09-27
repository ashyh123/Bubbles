import { NextResponse } from 'next/server';
import { callbackNextUrl, safeNextPath } from '@/lib/auth/redirect';
import { createClient } from '@/lib/supabase/server';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const nextPath = safeNextPath(url.searchParams.get('next'));
  // new URL('//evil.example', origin) leaves this site. Refuse that here too.
  const destination = callbackNextUrl(nextPath, url.origin);

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(destination);
    }
  }

  return NextResponse.redirect(new URL('/login?error=auth', url.origin));
}
