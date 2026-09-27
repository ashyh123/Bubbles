import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import { safeNextPath } from '@/lib/auth/redirect';
import { isProtectedPath } from '@/lib/auth/routes';
import { readPublicSupabaseEnv } from '@/lib/env';

export function withSessionCookies(redirect: NextResponse, session: NextResponse): NextResponse {
  for (const cookie of session.headers.getSetCookie()) {
    redirect.headers.append('set-cookie', cookie);
  }
  return redirect;
}

function redirectToLogin(request: NextRequest, sessionResponse: NextResponse) {
  const redirectUrl = request.nextUrl.clone();
  const next = safeNextPath(
    `${request.nextUrl.pathname}${request.nextUrl.search}${request.nextUrl.hash}`,
  );
  redirectUrl.pathname = '/login';
  redirectUrl.search = '';
  redirectUrl.hash = '';
  redirectUrl.searchParams.set('next', next);
  return withSessionCookies(NextResponse.redirect(redirectUrl), sessionResponse);
}

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  let url: string;
  let anonKey: string;
  try {
    ({ url, anonKey } = readPublicSupabaseEnv());
  } catch {
    return isProtectedPath(request.nextUrl.pathname)
      ? redirectToLogin(request, supabaseResponse)
      : supabaseResponse;
  }

  const supabase = createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => {
          request.cookies.set(name, value);
        });
        supabaseResponse = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) => {
          supabaseResponse.cookies.set(name, value, options);
        });
      },
    },
  });

  try {
    // Refresh the session. Do not run other logic between client creation and getUser.
    const { data } = await supabase.auth.getUser();
    if (!data.user && isProtectedPath(request.nextUrl.pathname)) {
      return redirectToLogin(request, supabaseResponse);
    }
  } catch {
    // Auth failures can include tokens. Do not log them. Protected pages still require a session.
    if (isProtectedPath(request.nextUrl.pathname)) {
      return redirectToLogin(request, supabaseResponse);
    }
  }

  return supabaseResponse;
}
