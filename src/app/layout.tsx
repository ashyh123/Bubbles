import type { Metadata } from 'next';
import { SiteHeader } from '@/components/site-header';
import { getCurrentUser } from '@/lib/auth/session';
import './globals.css';

export const metadata: Metadata = {
  title: 'Bubble',
  description: '把零散的想法变成每天都能做一点的小行动。',
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { user, configMissing } = await getCurrentUser();

  return (
    <html lang="zh-CN">
      <body>
        <div className="shell">
          <SiteHeader user={user} />
          {configMissing ? (
            <p className="alert">
              还没有配置 Supabase 环境变量。见 README 的本地启动步骤。
            </p>
          ) : null}
          {children}
        </div>
      </body>
    </html>
  );
}
