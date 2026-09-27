import { getCurrentUser } from '@/lib/auth/session';

export default async function HomePage() {
  const { user } = await getCurrentUser();

  return (
    <main className="stack">
      <h1>把想法留下来</h1>
      <p className="muted">捕捉输入框会在下一个里程碑接上。现在先确认登录状态。</p>
      <section className="card">
        {user ? (
          <p>
            当前登录：<strong>{user.email ?? user.id}</strong>
          </p>
        ) : (
          <p>尚未登录。</p>
        )}
      </section>
    </main>
  );
}
