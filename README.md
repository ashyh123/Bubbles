# Bubble

把零散的想法变成每天都能做一点的小行动。

这个仓库目前是第 1 个里程碑：可运行的 Next.js（App Router）+ TypeScript + Supabase 骨架。捕捉、判定、今日清单和目标树留在后续里程碑，目录已经为它们留好位置。

## 先决条件

- Node.js 22+
- pnpm 10
- Docker（跑本地 Supabase）
- [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started) 2.x

## 本地启动

```bash
pnpm install
cp .env.example .env.local
supabase start
supabase db reset
pnpm dev
```

`supabase db reset` 会按顺序执行 `supabase/migrations/` 和 `supabase/seed.sql`。

`supabase start` 结束后看它打印的 API URL 和 key。`.env.example` 里的 anon / service role 是 Supabase CLI 自带的本地演示密钥，不是线上密钥。如果本机 `supabase status` 打印的值不一样，用那个覆盖 `.env.local`。不要把真实密钥提交进仓库。

打开 <http://127.0.0.1:3000>。登录页只发邮箱魔法链接。本地邮件不会真的寄出，到 Mailpit <http://127.0.0.1:54324> 打开链接。首次登录时，`auth.users` 上的触发器会插入 `profiles`：时区 `Asia/Shanghai`，`judge_confidence_min` `0.60`。

## 脚本

| 命令             | 作用           |
| ---------------- | -------------- |
| `pnpm dev`       | 开发服务器     |
| `pnpm lint`      | ESLint         |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm test`      | Vitest         |
| `pnpm build`     | 生产构建       |
| `pnpm format`    | Prettier       |

RLS 用 pgTAP，需要本机 Docker：

```bash
supabase test db
```

测试在事务里创建两个用户，确认用户 B 读不到用户 A 的 bubbles，并在结束时回滚。

## 目录

```
src/app/            页面。首页占位，/login 魔法链接，/today 受保护占位
src/proxy.ts        Next.js 16 请求代理（原 middleware）：刷新会话，未登录则离开受保护路径
src/lib/supabase/   浏览器、Server Component、service role 三种客户端
src/lib/db/         与迁移一致的 Database 类型
src/lib/auth/       受保护路径、登录后的回跳
src/lib/privacy/    日志脱敏。不要把想法原文打到日志里
src/lib/judge/      可插拔判定器接口
src/lib/feed/       今日清单评分权重
src/lib/habits/     习惯权重常量
src/lib/goals/      目标树常量
src/lib/ingest/     Ingest API 的请求形状
supabase/migrations 全部表、RLS、索引
supabase/seed.sql   6 个类别和每个类别 5–8 个预设微习惯
supabase/tests      pgTAP RLS 测试
```

受保护路径前缀：`/today`、`/habits`、`/settings`、`/goals`、`/categories`、`/ideas`。首页保持公开，用来显示当前登录用户。

## 环境变量

见 `.env.example`。

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`（只在服务端使用，绕过 RLS）
- `AI_GATEWAY_API_KEY`（本里程碑不调用模型，可以为空）
- `JUDGE_PROVIDER`：`llm`（默认）或 `jev`

## 隐私

想法和习惯都是私密数据。表全部开启 RLS，按 `user_id` 隔离。`categories` 以及 `user_id` 为空的预设习惯对已登录用户只读。

打日志用 `logEvent`（`src/lib/privacy/log.ts`）。它会把 `content`、`text`、`idea`、`note`、`title`、`reason_text`、`body`、`prompt` 换成 `[redacted]`。不要 `console.log` 想法原文。

## 设计取舍

- Next.js 16 把 Middleware 改名为 Proxy，所以会话刷新和路由保护写在 `src/proxy.ts`，行为与以前的 middleware 相同。
- 枚举用 `text` + `CHECK`，没有建 Postgres enum，后面改值只要改约束。TypeScript 联合类型在 `src/lib/db/enums.ts`。
- `judge_results`、`links`、`feed_items`、`goal_nodes` 额外存了 `user_id`，RLS 可以直接比较，不必 join。
- 类别是全局预设，没有 `user_id`。预设习惯 `source = 'preset'` 且 `user_id` 为空；用户自己的习惯必须带 `user_id`。
- `(user_id, idempotency_key)` 是部分唯一索引，只在 key 非空时生效，避免没有 key 的网页捕捉互相冲突。
- 向量索引用 HNSW cosine，对应 PRD 里 0.85 的相似度阈值。维度 1536。
- `goal_nodes.status` 用 `open` / `done` / `dismissed`。`goal_trees.mode` 用 `concrete` / `bigger`。
- API 令牌只存小写 SHA-256 十六进制哈希，scope 目前只允许 `bubbles:write`。
- 类型文件是按迁移手写的。本地库起来之后可以用 `supabase gen types typescript --local --schema public` 覆盖 `src/lib/db/database.types.ts`。
