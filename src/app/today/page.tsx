import { redirect } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth/session';

export default async function TodayPage() {
  const { user } = await getCurrentUser();
  if (!user) {
    redirect('/login?next=/today');
  }

  return (
    <main className="stack">
      <h1>今日清单</h1>
      <p className="muted">
        每天 3–5 项会在后面的里程碑生成。这一页只用来确认登录后的路由已经受保护。
      </p>
      <section className="card">
        <p>
          当前登录：<strong>{user.email ?? user.id}</strong>
        </p>
      </section>
    </main>
  );
}
