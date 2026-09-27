import Link from 'next/link';
import type { CurrentUser } from '@/lib/auth/session';

export function SiteHeader({ user }: { user: CurrentUser | null }) {
  return (
    <header className="site-header">
      <Link href="/" className="wordmark">
        Bubble
      </Link>
      {user ? (
        <form action="/auth/signout" method="post" className="session">
          <span>{user.email ?? '已登录'}</span>
          <button type="submit">退出</button>
        </form>
      ) : (
        <Link href="/login" className="button">
          登录
        </Link>
      )}
    </header>
  );
}
