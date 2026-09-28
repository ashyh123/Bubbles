# Bubble

本地命令行学习助手的最小 demo（v0）。你给出一个学习想法，Bubble 调用一次大模型，把它拆成最多 3 条可以马上开始的动作：打开网页、打开 B 站搜索，或在终端打印一段 150–200 字的简介。

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
| `BUBBLE_API_KEY` | 必填，和 `DEEPSEEK_API_KEY` 二选一 |
| `DEEPSEEK_API_KEY` | 与上一行相同。两个都没设时，提示是 `缺少 BUBBLE_API_KEY，请参考 .env.example 配置` |
| `BUBBLE_BASE_URL` | 可选，默认 `https://api.deepseek.com` |
| `BUBBLE_MODEL` | 必填，例如 `deepseek-chat` |
| `BUBBLE_REASONING_EFFORT` | 可选，默认 `low`。模型不接受该参数时会去掉后重试 |
| `BUBBLE_TIMEOUT` | 可选，模型请求超时秒数，默认 `45`。超时只打印一句中文提示 |
| `BUBBLE_TASTE_PATH` | 可选，默认 `~/.bubble/taste.md` |

```bash
cp .env.example .env
# 编辑 .env，填入密钥和 BUBBLE_MODEL
set -a && source .env && set +a
```

<!-- 下方“示例输出”里的网址和标题都是示例，不是真实运行结果。录好真实终端演示后替换。 -->

## 用法

```bash
bubble "完成 CS61B Project 1"      # 把一个想法拆成 3 条马上能做的动作
bubble remember "CS61B 用 sp21 版"  # 往 taste.md 追加一条偏好
```

`remember` 成功后打印 `记住了：… （写入 taste.md）`。文件里实际追加的一行带当天日期。下次拆分时，整份 `taste.md` 会放进提示词，并标明这是用户自己的偏好。

## 小技巧

把常用页面的真实网址写进 `taste.md`，拆分时会优先用它们，不用靠模型猜路径。例如：

```
CS61B 用 sp21 版
CS61B Project 1 说明页：https://sp21.datastructur.es/materials/proj/proj1/proj1
```

上面的网址是示例，请换成你自己核对过的地址。

### 示例输出（示例数据）

```
$ bubble "完成 CS61B Project 1"
正在拆分…（通常 10 秒内）

① 打开 CS61B sp21 · Project 1 说明页     推荐先做 · 按你的 taste
② B站搜索「CS61B Project 1」
③ 看一份 200 字的作业简介

选一条 [1-3]，回车退出 › 1
将打开 https://sp21.datastructur.es/materials/proj/proj1/proj1  确认？[Y/n] ›
已打开。
```

## 终端交互规则

1. **等待**：调用模型期间只显示一行 `正在拆分…（通常 10 秒内）`，不刷屏、不打印中间过程。模型请求默认 45 秒超时（`BUBBLE_TIMEOUT` 可改）。超时后只打印 `这次拆分太久了，请稍后再试一次`，退出码非 0，不打印堆栈。
2. **条目**：每条动作占一行，开头写要打开或要做什么，后面跟标题，行首用 ①②③ 编号。
   - 第一条在行尾标 `推荐先做`。
   - 这条动作用到了 `taste.md` 里的内容，就在行尾加 `按你的 taste`（和“推荐先做”之间用 ` · ` 隔开）。
   - 三类动作的写法：
     - `open_url`：`打开 <站点/课程> · <页面标题>`
     - `video_search`：`B站搜索「<关键词>」`
     - `brief`：`看一份 200 字的<主题>简介`
3. **打不开的网址**：原页面打不开、但同一主机的 https 首页能打开时，保留这条动作，标题换成首页，行尾加 `原页面打不开，已换成首页`（和其他标注之间用 ` · ` 隔开）。确认时打印首页的完整网址。首页也打不开时，那条不显示、不补占位，编号连续，末尾加一行 `有 N 条链接打不开，已略过`。“换成首页”和“略过”分开写进日志。原网址本身不合法（http、`user@host` 伪装等）时不尝试退回，直接丢弃。
4. **选择**：提示 `选一条 [1-N]，回车退出 ›`。直接回车表示退出，什么都不执行。输入超出范围时提示一次 `请输入 1-N`，再等输入。
5. **确认**：`open_url` 和 `video_search` 执行前打印**完整网址**，提示 `确认？[Y/n]`，默认是，回车即执行；输入 `n` 返回选择。`brief` 不需要确认，直接把简介打印在终端里。
6. **执行后**：打开网页后打印 `已打开。` 并退出。
7. **出错**：没有可用动作时打印 `这次没拆出能用的动作，换个说法再试一次？`，退出码非 0。缺少密钥时打印 `缺少 BUBBLE_API_KEY，请参考 .env.example 配置`，不打印堆栈。
8. **remember**：`bubble remember "…"` 追加成功后打印一行 `记住了：… （写入 taste.md）`。

## 文案原则

- 全中文，一句话一行，不用 emoji。
- 不解释模型、推理过程或内部字段名。
- 除完整网址外，每行不超过终端 80 列；标题过长用 `…` 截断。

打不开的链接不会出现在列表里。丢掉的原因和条数写在 `~/.bubble/log`（写不了文件时改打到 stderr）。

## 安全规则

- 模型只能在三种类型里填参数：`open_url`、`video_search`、`brief`。未知类型直接丢掉。
- `open_url` 只允许 `https`，不允许用户名或密码（URL 里出现 `@` 就拒绝），主机不能是 IP。展示之前用 httpx 请求一次：先 HEAD，失败再 GET，超时 5 秒，跟随重定向，最终地址仍须是 `https`。这一页打不开时，只再请求同一主机的 https 首页；首页能打开就改打开首页，标题换成首页。首页也打不开才丢掉。http、`user@host` 这类不合法网址不退回，直接丢弃。日志分别计数「退回首页」和「丢弃」。探测网页的 5 秒和模型请求的 45 秒是两回事。
- **已知缺口**：v0 的 `open_url` 没有域名白名单，只要求 https 且能打开。`bilibili.com.evil.com` 这种仿冒域名如果本身是 https 并且探测成功，不会被白名单拦住。
- `video_search` 不向 B 站发请求。程序只用关键词自己拼 `https://search.bilibili.com/all?keyword=<urlencode>`，并检查格式。模型给出的 URL 一律不用。
- 任何类型都不执行 shell。模型输出里的命令文本只会被丢掉或当作简介原文打印，不会交给系统执行。
- 模型输出解析失败时，用同一提示再请求 1 次。仍然没有可用动作时，只打印规则 7 那一句，不打印堆栈。
- 密钥只来自环境变量。

提示词在 [`bubble/prompts/plan.md`](bubble/prompts/plan.md)。

## 不做的范围

这个 demo 不做：Jev 判断、MCP、后台运行和系统通知、打开本地项目或软件、自动推断品味、SQLite、资料整理与学术诚信过滤、评测集、网页界面、登录和多用户、云端部署、open_url 域名白名单。CI 也只做这一件：GitHub Actions 跑 `ruff check` 和 `pytest`，不调用真实模型。

## 开发

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

测试全部 mock 了模型客户端和 httpx，不需要密钥。`tests/safety/` 是不联网的安全用例。
