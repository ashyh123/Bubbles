import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import { isProtectedPath } from '@/lib/auth/routes';
import { safeNextPath } from '@/lib/auth/redirect';
import { readPublicSupabaseEnv } from '@/lib/env';

function redirectToLogin(request: NextRequest) {
  const redirectUrl = request.nextUrl.clone();
  redirectUrl.pathname = '/login';
  redirectUrl.searchParams.set('next', safeNextPath(request.nextUrl.pathname));
  return NextResponse.redirect(redirectUrl);
}

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  let url: string;
  let anonKey: string;
  try {
    ({ url, anonKey } = readPublicSupabaseEnv());
  } catch {
    return isProtectedPath(request.nextUrl.pathname)
      ? redirectToLogin(request)
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
      return redirectToLogin(request);
    }
  } catch {
    // Auth failures can include tokens. Do not log them. Protected pages still require a session.
    if (isProtectedPath(request.nextUrl.pathname)) {
      return redirectToLogin(request);
    }
  }

  return supabaseResponse;
}
