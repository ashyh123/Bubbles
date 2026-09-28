# Bubble

本地命令行学习助手的最小 demo（v0）。你给出一个学习想法，Bubble 调用一次大模型，把它拆成 3 条可以马上开始的动作：打开网页、打开 B 站搜索，或在终端打印一段约 200 字的简介。

项目方向已经从 Next.js 网页改成本地 Python 命令行。早先的网页方案在未合并的 PR #1（分支 `cursor/milestone-1-foundation-61be`）里，本分支不使用、也不修改那条分支。`main` 上如果还有旧的网页文件，这里不会删；新代码都在仓库根目录的 `bubble/` 包。

## 安装

需要 Python 3.10+。运行时依赖只有 `openai` 和 `httpx`。打开浏览器用的是标准库 `webbrowser`。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 配置环境变量

仓库里只有 [`.env.example`](.env.example)，没有真实密钥。把密钥放在本机环境里，不要写进仓库。

| 变量 | 说明 |
|---|---|
| `BUBBLE_API_KEY` | 必填。DeepSeek（或其它 OpenAI 兼容接口）的密钥 |
| `BUBBLE_BASE_URL` | 可选，默认 `https://api.deepseek.com` |
| `BUBBLE_MODEL` | 必填，例如 `deepseek-chat` |
| `BUBBLE_REASONING_EFFORT` | 可选，默认 `low`。模型不接受该参数时会去掉后重试 |
| `BUBBLE_TASTE_PATH` | 可选，默认 `~/.bubble/taste.md` |

```bash
cp .env.example .env
# 编辑 .env，填入 BUBBLE_API_KEY 和 BUBBLE_MODEL
set -a && source .env && set +a
```

## 用法

```bash
bubble "完成 CS61B Project 1"
bubble remember "CS61B 用 sp21 版"
```

`remember` 把一句偏好追加到 taste 文件，前面带当天日期。下次拆分时，整份文件会放进提示词，并标明这是用户自己的偏好。

## 示例终端输出

有 taste「CS61B 用 sp21 版」时，一次可能的输出（网址以模型当次返回、且探测成功的结果为准）：

```text
正在拆分…
① 打开 CS61B sp21 Project 1 说明页 （推荐先做 · 按你的 taste）
② B站搜索「CS61B sp21 Project 1」 （按你的 taste）
③ Project 1 简介
选一条（回车退出）：1
https://sp21.datastructur.es/materials/proj/proj1/proj1
确认？[Y/n] y
```

直接回车退出。`open_url` 和 `video_search` 会先打印完整网址，再问 `确认？[Y/n]`，直接回车表示确认。`brief` 选中后直接打印正文。

打不开的链接不会出现在列表里。如果丢掉了链接，列表末尾有一行：

```text
正在拆分…
① B站搜索「操作系统 调度」 （推荐先做）
② 调度算法简介
有 1 条链接打不开，已略过
选一条（回车退出）：
```

丢掉的原因写在 `~/.bubble/log`（写不了文件时改打到 stderr）。

## 安全规则

- 模型只能在三种类型里填参数：`open_url`、`video_search`、`brief`。未知类型直接丢掉。
- `open_url` 只允许 `https`，不允许用户名或密码（URL 里出现 `@` 就拒绝），主机不能是 IP。展示之前用 httpx 请求一次：先 HEAD，失败再 GET，超时 5 秒，跟随重定向，最终地址仍须是 `https`。失败就丢掉并写日志。
- `video_search` 不向 B 站发请求。程序只用关键词自己拼 `https://search.bilibili.com/all?keyword=<urlencode>`，并检查格式。模型给出的 URL 一律不用，因此 `bilibili.com.evil.com` 这类仿冒主机不会被打开。
- 任何类型都不执行 shell。模型输出里的命令文本只会被丢掉或当作简介原文打印，不会交给系统执行。
- 模型输出解析失败时，用同一提示再请求 1 次。
- 密钥只来自环境变量。

提示词在 [`bubble/prompts/plan.md`](bubble/prompts/plan.md)。

## 不做的范围

这个 demo 不做：Jev 判断、MCP、后台运行和系统通知、打开本地项目或软件、自动推断品味、SQLite、资料整理与学术诚信过滤、评测集、网页界面、登录和多用户、云端部署。CI 也只做这一件：GitHub Actions 跑 `ruff check` 和 `pytest`，不调用真实模型。

## 开发

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

测试全部 mock 了模型客户端和 httpx，不需要密钥。
