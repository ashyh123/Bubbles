'use client';

import { useState, type FormEvent } from 'react';
import { createClient } from '@/lib/supabase/client';

export function LoginForm({ nextPath }: { nextPath: string }) {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setMessage(null);

    try {
      const supabase = createClient();
      const redirectTo = new URL('/auth/callback', window.location.origin);
      redirectTo.searchParams.set('next', nextPath);
      const { error: signInError } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: redirectTo.toString() },
      });
      if (signInError) {
        setError('发送登录链接失败，请稍后再试。');
        return;
      }
      setMessage(
        '登录链接已发送。本地开发请打开 Mailpit（http://127.0.0.1:54324）查看邮件。',
      );
    } catch {
      setError('登录服务还没准备好。确认本地 Supabase 已启动，并且 .env.local 已配置。');
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card stack" onSubmit={onSubmit}>
      <div>
        <label htmlFor="email">邮箱</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>
      <button type="submit" disabled={pending}>
        {pending ? '发送中…' : '发送登录链接'}
      </button>
      {error ? (
        <p className="alert" role="alert">
          {error}
        </p>
      ) : null}
      {message ? <p>{message}</p> : null}
    </form>
  );
}
