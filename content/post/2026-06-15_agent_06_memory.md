---
layout:		 single
title:       "Agent 06：一个简单实现（4）Memory"
subtitle:    ""
description: " "
date:        2026-06-15T18:39:30+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent", "claude code"]
categories:  ["Tech" ]
URL: "2026/06/agent-06/"
math: False
---

本章，我们将实现 agent 的记忆系统。这个系统将维护一套结构化的持久记忆，让 AI 能够记住我们的偏好和会话历史；另外，agent 可以自动在会话过程中保存记忆，不需要我们手动执行。

### 文件系统设计

Claude Code 的记忆系统采用的是“记忆即文件”的存储方式，每条记忆都是一个独立的 markdown 文件，全部存在统一的 `/memory` 文件夹下。有两个记忆范围目录，分别是：
- `user` 级：`~/.claude/memory/<slug>.md`，跨项目共享
- `project` 级：`.claude/memory/<slug>.md`，仅当前项目

```text
~/.claude/memory/
  MEMORY.md                    # 索引文件，每行一条指针
  user_role.md                 # 独立记忆文件
  feedback_testing.md           # 独立记忆文件
  project_auth_rewrite.md      # 独立记忆文件
  reference_linear_project.md  # 独立记忆文件
```

在 `/memory` 中会有一个固定的索引文件 MEMORY.md，每行存储一条具体记忆文件的链接，每次读写记忆时也会自动更新。它的格式如下：

```text
- [name1](file1.md) - description
- [name2](file2.md) — description
...
```

这里的 description 非常简短，因为我们在上一章的 System Prompt 小节中以及提到过，MEMORY.md 是要在每次 session 开始时注入到 system prompt 中的，所以它必须要简洁；我们给它定义两个约束，分别是行数上限和字节数上限，达到任一上限就会触发截断。

```python
# Maximum lines/bytes for the index file
MAX_INDEX_LINES = 200
MAX_INDEX_BYTES = 25_000

# 截断函数中，找到上限之前的最后一个换行符，以免切断一条记忆的中间
if len(truncated.encode()) > MAX_INDEX_BYTES:
        # Cut at last newline before byte limit
        raw_bytes = truncated.encode()
        cut = raw_bytes[:MAX_INDEX_BYTES].rfind(b"\n")
        truncated = raw_bytes[: cut if cut > 0 else MAX_INDEX_BYTES].decode(errors="replace")
```

具体到每条记忆来说，我们实现的一条记忆的数据结构如下：

```python
class MemoryEntry:
    """A single memory entry loaded from a .md file.

    Attributes:
        name:        human-readable name (also the display title in the index)
        description: short one-line description (used for relevance decisions)
        type:        "user" | "feedback" | "project" | "reference"
        content:     body text of the memory
        file_path:   absolute path to the .md file on disk
        created:     date string, e.g. "2026-04-02"
        scope:       "user" | "project" — which directory this was loaded from
    """
    name: str
    description: str
    type: str
    content: str
    file_path: str = ""
    created: str = ""
    scope: str = "user"
```

可以看到，其中定义了一条记忆的类型。Claude Code 给记忆定义了固定的四种类型：

- `user` 记录用户的角色、目标、偏好、职责、知识背景，比如“用户有 C++ 的后端背景，但是没有接触过 React”
- `feedback` 指导工作方式，包括用户的纠正以及确认；写这部分记忆的时候要求先写规则，再明确 `Why` 和 `How to apply`
- `project` 不可从代码/git 推导的进行中工作、目标、决策、bug、事故；写这部分记忆的时候相对日期要转成绝对日期
- `reference` 外部资源的指针，告诉模型在哪里能找到信息（issue tracker、Grafana、Slack 频道、文档）

什么不需要保存？代码模式、架构、文件路径、git 历史、调试修复方案、CLAUDE.md 已有内容、临时任务状态，这些都是可以直接从当前工作目录里推导的东西；即使用户明确要求保存 PR 列表，也应该追问「哪部分是 surprising/非显而易见的？」，只保存那部分。

每个记忆文件都带有一个设计好的 YAML frontmatter，这样有助于读写。

```markdown
---
name: {{memory name}}
description: {{one-line description — used to decide relevance, so be specific}}
type: {{user | feedback | project | reference}}
---

{{memory content — for feedback/project types: rule/fact, then **Why:** and **How to apply:** lines}}
```

举例，假如用户说「测试不要 mock 数据库」，agent 应该自动保存一条记忆：

```markdown
---
name: feedback_testing
type: feedback
scope: user
description: Integration tests must hit a real DB, not mocks
---

Don't mock the database in tests.
**Why:** mocks hide query/schema bugs until prod.
**How to apply:** when writing tests that touch the DB layer, spin up the test DB instead of using unittest.mock.
```

### 记忆扫描

定义一个轻量 descriptor，保存从记忆文件的 frontmatter 提取出的 metadata：

```python
class MemoryHeader:
    """Lightweight descriptor loaded from a memory file's frontmatter.

    Attributes:
        filename:    basename of the .md file
        file_path:   absolute path
        mtime_s:     modification time (seconds since epoch)
        description: value from frontmatter `description:` field
        type:        value from frontmatter `type:` field
        scope:       "user" or "project"
    """
    filename: str
    file_path: str
    mtime_s: float
    description: str
    type: str
    scope: str
```

提供扫描函数，递归扫描记忆目录下所有的 markdown 文件（除 MEMORY.md 之外），读取每个文件的前 30 行 frontmatter，然后按修改时间倒序排列。

```python
def scan_memory_dir(mem_dir: Path, scope: str) -> list[MemoryHeader]:
    """Scan a single memory directory and return headers sorted newest-first.

    Reads only the frontmatter (first ~30 lines) for efficiency.
    Silently skips unreadable files. Caps at MAX_MEMORY_FILES entries.
    """
    if not mem_dir.is_dir():
        return []

    headers: list[MemoryHeader] = []
    for fp in mem_dir.glob("*.md"):
        if fp.name == INDEX_FILENAME:
            continue
        try:
            stat = fp.stat()
            # Read only the first 30 lines for frontmatter
            lines = fp.read_text(errors="replace").splitlines()[:30]
            snippet = "\n".join(lines)
            meta, _ = parse_frontmatter(snippet)
            headers.append(MemoryHeader(
                filename=fp.name,
                file_path=str(fp),
                mtime_s=stat.st_mtime,
                description=meta.get("description", ""),
                type=meta.get("type", ""),
                scope=scope,
            ))
        except Exception:
            continue

    headers.sort(key=lambda h: h.mtime_s, reverse=True)
    return headers[:MAX_MEMORY_FILES]
```

扫描结果可以格式化为文本清单 manifest，供记忆检索和提取的 prompt 使用：

```python
def format_memory_manifest(headers: list[MemoryHeader]) -> str:
    """Format a list of MemoryHeader as a text manifest.

    Format per line:  [type/scope] filename (age): description
    Example:
        [feedback/user] feedback_testing.md (3 days ago): Don't mock DB in tests
        [project/project] project_freeze.md (today): Merge freeze until 2026-04-10
    """
    lines = []
    for h in headers:
        tag = f"[{h.type}/{h.scope}]" if h.type else f"[{h.scope}]"
        age = memory_age_str(h.mtime_s)
        if h.description:
            lines.append(f"- {tag} {h.filename} ({age}): {h.description}")
        else:
            lines.append(f"- {tag} {h.filename} ({age})")
    return "\n".join(lines)
```
### 记忆注入

记忆被注入到上下文中，有两个途径：通过 system prompt，以及 AI 自己根据用户输入查询相关记忆。前者我们在上一章已经触及过了，就是将 MEMORY.md 的内容经过截断处理后，和整个记忆系统的指南（位置、格式、类型、如何保存、示例）注入到 system prompt 中。下面主要讲后者。

Claude Coded 的记忆检索实际上非常简单，就是把我们之前扫描 memory 目录生成的 manifest 列表，调用一个 sonnet 模型做 sideQuery 来判断哪些记忆和当前对话最相关。

```typescript
// src/memdir/findRelevantMemories.ts, 第 18-24 行
const SELECT_MEMORIES_SYSTEM_PROMPT = `You are selecting memories that will be useful to Claude Code as it processes a user's query. You will be given the user's query and a list of available memory files with their filenames and descriptions. Return a list of filenames for the memories that will clearly be useful (up to 5). Only include memories that you are certain will be helpful...`
```

这个 selector prompt 很保守，明确要求最多返回 5 条结果，不确定就返回空；如果某些工具当前已经成功使用，不要再把这些工具的参考文档 memory 选进来。另外，记忆注入时还有去重环节，避免已经读过的记忆被重复注入——如果本轮或者前几轮已经通过 FileRead/Write/Edit 读过对应 memory 文件，就不再重复召回。

Claude Code 实现记忆检索其实是用了异步 prefetch，也就是在每轮对话的开头，启动一个异步预取，它不会阻塞主流程，而是在模型流式输出和工具执行期间后台运行；中途如果 prefetch 完成，就把结果作为 `relevant_memories` attachment 插入。

但是我们在简单实现里，可以直接把记忆检索包装成一个工具，和保存/删除/列出记忆 manifest 一样，让模型按需调用：

```python
register_tool(ToolDef(
    name="MemorySearch",
    schema={
        "name": "MemorySearch",
        "description": (
            "Search persistent memories by keyword. Returns matching entries with "
            "content preview and staleness warning for old memories. "
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (default: 5)",
                },
                "scope": {
                    "type": "string",
                    "enum": ["user", "project", "all"],
                    "description": "Which scope to search (default: 'all')",
                },
            },
            "required": ["query"],
        },
    },
    func=_memory_search,
    read_only=True,
    concurrent_safe=True,
))
```

### 过期提醒

对于每条记忆的时间，提供一套人类可读的时间格式：

```python
def memory_age_days(mtime_s: float) -> int:
    """Days since mtime_s (floor-rounded, clamped to 0 for future times)."""
    return max(0, math.floor((time.time() - mtime_s) / 86_400))


def memory_age_str(mtime_s: float) -> str:
    """Human-readable age: 'today', 'yesterday', or 'N days ago'."""
    d = memory_age_days(mtime_s)
    if d == 0:
        return "today"
    if d == 1:
        return "yesterday"
    return f"{d} days ago"
```

> 为什么要把时间戳转成“47 天前”而不是 ISO 格式？因为模型在日期算术上表现很差——看到 `2026-02-12T08:33:00Z` 不会自动意识到这是很久以前的，但看到 47 days ago 会立即触发过时性推理。

如果是超过一天的记忆，会标注过时警告：

```python
def memory_freshness_text(mtime_s: float) -> str:
    """Staleness caveat for memories older than 1 day (empty string if fresh).

    Motivated by user reports of stale code-state memories (file:line
    citations to code that has since changed) being asserted as fact.
    """
    d = memory_age_days(mtime_s)
    if d <= 1:
        return ""
    return (
        f"This memory is {d} days old. "
        "Memories are point-in-time observations, not live state — "
        "claims about code behavior or file:line citations may be outdated. "
        "Verify against current code before asserting as fact."
    )
```

这里提醒模型，memory 只是某个时间点上的快照，不能直接把它当作事实，涉及代码或文件时需要重新验证。

Claude Code 的记忆系统 system prompt 中也有这方面的说明，要求模型在基于记忆推荐之前先验证：

```typescript
// src/memdir/memoryTypes.ts, 第 240-256 行
export const TRUSTING_RECALL_SECTION: readonly string[] = [
  '## Before recommending from memory',
  '',
  'A memory that names a specific function, file, or flag is a claim that ' +
  'it existed *when the memory was written*. It may have been renamed, ' +
  'removed, or never merged. Before recommending it:',
  '',
  '- If the memory names a file path: check the file exists.',
  '- If the memory names a function or flag: grep for it.',
  '- If the user is about to act on your recommendation: verify first.',
  '',
  '"The memory says X exists" is not the same as "X exists now."',
]
```

### 设计原则

我们这次的简单实现其实已经非常接近 Claude Code 的记忆系统了，这也可以看出，它的记忆是刻意做得非常简单：

- 使用文件系统和 markdown 存储长期记忆，通过路径解析或者模型发起的读取操作加载。

> 没有用 SQLite、LevelDB 或任何嵌入式数据库，直接用文件系统。这看起来原始，但它带来了可调试性（直接 `cat` 查看）、可迁移性（直接复制目录）和可操作性（任何编辑器都能改）。对于一个记忆条目通常不超过 200 个、每个文件不超过几 KB 的系统，文件系统的性能完全够用。

- 记忆检索没有使用向量数据库、embedding 或者 BM25 索引，而是直接让另一个模型（sonnet）自己根据索引来推理。

第三方库（memsearch、claude-mem）的存在恰恰是因为原生系统如此简单，而这种简单性在大规模应用时或多或少存在着一些局限性。原生系统的设计理念是将检索问题置于模型推理内部，而不是外部，这种方式更简单，也更容易调试，但随着内存空间增长到无法容纳在短索引中的程度，性能会不可避免地下降。
