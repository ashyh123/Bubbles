import { safeNextPath } from '@/lib/auth/redirect';
import { LoginForm } from './login-form';

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[]; error?: string | string[] }>;
}) {
  const params = await searchParams;
  const nextValue = Array.isArray(params.next) ? params.next[0] : params.next;
  const errorValue = Array.isArray(params.error) ? params.error[0] : params.error;

  return (
    <main className="stack">
      <h1>登录</h1>
      <p className="muted">
        输入邮箱即可。我们发一封魔法链接，不需要密码。本地开发时邮件不会真的寄出，去
        Mailpit 打开它。
      </p>
      {errorValue === 'auth' ? (
        <p className="alert" role="alert">
          登录链接无效或已过期。
        </p>
      ) : null}
      <LoginForm nextPath={safeNextPath(nextValue)} />
    </main>
  );
}
