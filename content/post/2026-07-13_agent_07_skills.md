---
layout:		 single
title:       "Agent 07：一个简单实现（5）Skills"
subtitle:    ""
description: " "
date:        2026-07-13T15:42:19+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent", "claude code"]
categories:  ["Tech" ]
URL: "2026/07/agent-07/"
math: False
---

本章，我们将实现 agent 的 skills。

### Skills 结构设计

[Anthropic 官方工程博客](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)将 skills 定义为：它是由指令、脚本和资源组成的有序文件夹，agent 可以动态发现并加载这些文件夹，从而更好地完成特定任务。

一个标准的 skill 可以包含以下内容：

```text
pdf-skill/
├── SKILL.md            # Skill 元数据和核心指令（必需）
├── forms.md            # 表单填写指南（可选）
├── reference.md        # 详细 API 参考（可选）
└── scripts/            # 实用脚本
    └── extract_fields.py
```

其必需文档 `SKILL.md` 有一个 YAML frontmatter，这部分会在启动时加载到 system prompt 中。

```text
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---

# PDF Processing

## Quick start

Use pdfplumber to extract text from PDFs...

For advanced form filling, see [forms.md](forms.md).
```

在上面的示例中，它引用了附加文件 `forms.md`，这属于额外的链接文件，agent 可以根据需要阅览和查找；比如说，agent 应该只在需要填写表单的时候阅读 `forms.md`。

当 agent 想要调用一项 skill 时，其流程如此：它加载一个 Markdown 文件（ `SKILL.md` ），将其展开成详细的指令，将这些指令作为新的用户消息注入到对话上下文中，修改执行上下文（允许的工具、模型选择），并在这个修改后的环境中继续对话。

> Skills 和工具执行有本质的区别，工具执行操作并返回结果，skills 的作用是帮助 agent 做好准备来解决问题，而不是直接解决问题。

Claude Code 中，所有 Skill 最终都抽象为 Command 类型，和 Plugin、MCP 汇总在一起表示；简单起见，我们此处只实现单独的 Skill 数据结构。

```python
@dataclass
class SkillDef:
    name: str
    description: str
    triggers: list[str]          # ["/commit", "commit changes"]
    tools: list[str]             # ["Bash", "Read"]  (allowed-tools)
    prompt: str                  # full prompt body after frontmatter
    file_path: str
    # Enhanced fields
    when_to_use: str = ""        # when Claude should auto-invoke this skill
    arguments: list[str] = field(default_factory=list)  # named arg names
    model: str = ""              # model override
    user_invocable: bool = True  # appears in /skills list
    context: str = "inline"      # "inline" or "fork" (fork = sub-agent)
    source: str = "user"         # "user", "project", "builtin"
```

- `triggers` 触发词；
- `tools` 定义了 skill 无需用户批准即可使用的工具；
- `file_path` skill 文件在磁盘上的路径；
	- 注意不要和 `path` 相混淆：这个字段用于声明自己只在特定文件路径下生效，这一项存在时，它不会立即加载到可用列表，只有当模型操作匹配路径的文件时，skill 才被激活。

> 这种 lazy loading 设计有明确的性能目的：一个项目可能有大量 Skill，但不是所有 Skill 都与当前工作相关。通过路径过滤，Skill 列表保持精简，减少系统提示词中的 token 消耗。

- `when_to_use` 如果存在，会自动接到 description 后面；
- `arguments` 参数占位符，可以将参数动态注入到 skill 中；
- `user_invocable` 这个字段可以允许或阻止 agent 通过 `Skill` 工具自动调用技能；设置为 false 时，该技能将从 agent 显示的 `/skills` 列表中排除，用户只能通过 `/skill-name` 手动调用，适合需要用户显式控制的危险操作、配置命令或交互式工作流程；
- `context` 表示 skill 是在当前 session 执行，还是用一个 subagent 执行；
- `source` 系统会自动将 source 附加到 description 中（例如， `"(plugin:skills)"` ），这有助于在加载多个 skill 时区分来自不同 source 的 skill，也可以区分优先级。

### 发现和加载

Skills 通常会有多个来源：磁盘上的（即写在 `skills/` 文件夹下的 skills，又分为全局和项目级）、内置的、MCP server 上的。这些不同来源的 skills 会合并加载，需要在出现同名 skills 时高优先级能覆盖低优先级。此处我们实现的方式是按照优先级倒序加载，用字典 `seen[name]` 去重，因此 project 能覆盖 user 覆盖 builtin。

```python
def load_skills(include_builtins: bool = True) -> list[SkillDef]:
    """Return skills from disk + builtins, deduplicated (project > user > builtin)."""
    seen: dict[str, SkillDef] = {}

    # Builtins go in first (lowest priority)
    if include_builtins:
        for sk in _BUILTIN_SKILLS:
            seen[sk.name] = sk

    # User-level next, project-level last (highest priority)
    skill_paths = _get_skill_paths()
    for i, skill_dir in enumerate(reversed(skill_paths)):
        src = "user" if i == 0 else "project"
        if not skill_dir.is_dir():
            continue
        for md_file in sorted(skill_dir.glob("*.md")):
            skill = _parse_skill_file(md_file, source=src)
            if skill:
                seen[skill.name] = skill

    return list(seen.values())
```

加载了 skills 列表之后，模型想要使用 skill，需要通过调用工具的形式，也就是把 Skill 这个组件本身包装成 Tool 接口：

```python
_SKILL_SCHEMA = {
    "name": "Skill",
    "description": (
        "Invoke a named skill (reusable prompt template). "
        "<available_skills>..."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name (e.g. 'commit', 'review')",
            },
            "args": {
                "type": "string",
                "description": "Arguments to pass to the skill (replaces $ARGUMENTS)",
                "default": "",
            },
        },
        "required": ["name"],
    },
}
```

换言之，Skill 工具是一个 meta-tool；具体的 skills 不在系统提示词中，而是在 `tools` 数组中作为 Skill 工具的 description 的一部分。

加载 skills 时，很重要的一个原则叫 Progressive Disclosure（渐进式披露）：先提供足够的信息帮助 agent 决定下一步行动，然后根据需要逐步披露更多细节。就 agent skills 而言，

1. Disclose 最少的 frontmatter（name, description, licence）；
2. 如果选择了一项 Skill，加载 SKILL.md；
3. 在 skill 执行过程中加载辅助资源、reference 和脚本。

上述的第一步就是通过 Skill 工具的 description 完成的。当用户要求“从 report.pdf 中提取文本”时，LLM 会根据 Skill 工具的 `<available_skills>`，自行选择要调用哪个 skill，然后发起一个工具调用，形如：

```json
{
  "type": "tool_use",
  "id": "toolu_123abc",
  "name": "Skill",
  "input": {
    "name": "pdf"
  }
}
```

> 注意，agent 选择 skill 的过程中没有任何算法，没有词汇匹配、语义匹配或者检索；这是完全基于 skill description 的 LLM 推理。

#### 动态上下文注入

虽然被包装成了工具调用的形式，但 skills 仍然和前面我们讲过的真正的 tool 有本质区别：skills 实际上相当于提示词注入，加上 context modifier。一方面，在注入 SKILL.md 时，可以在 prompt 中使用可变参数：

```python
def substitute_arguments(prompt: str, args: str, arg_names: list[str]) -> str:
    """Replace $ARGUMENTS (whole args string) and $ARG_NAME placeholders.

    Named args are positional: first word → first name, etc.
    """
    # Always substitute $ARGUMENTS
    result = prompt.replace("$ARGUMENTS", args)

    # Named args: split by whitespace
    arg_values = args.split()
    for i, arg_name in enumerate(arg_names):
        placeholder = f"${arg_name.upper()}"
        value = arg_values[i] if i < len(arg_values) else ""
        result = result.replace(placeholder, value)

    return result
```

此处只实现了用户参数，`$ARGUMENTS` 被替换为完整的参数字符串，命名参数 `${branch}` 被替换为对应的值；在完整的 Claude Code 实现里，还有两层参数替换：

- 内置变量：`${CLAUDE_SKILL_DIR}` 指向 Skill 所在目录，`${CLAUDE_SESSION_ID}` 是当前会话 ID。
- Shell 命令：Skill 内容中的 `` !`command` `` 和 ` ```! command ``` ` 语法会被实际执行（有一个函数叫 `executeShellCommandsInPrompt`），输出替换到 prompt 中，这是 Skill 与环境交互的关键能力；但出于安全考虑，MCP 来源的 Skill 禁止执行 shell 命令。

另一方面，执行 skills 时的 context 也有 inline 和 fork 的区别，前者可以直接复用当前的 state，后者则需要新建一个 state，并在有必要时覆盖当前的模型和工具。

```python
def execute_skill(
    skill: SkillDef,
    args: str,
    state,
    config: dict,
    system_prompt: str,
) -> Generator:
    """Execute a skill.

    If skill.context == "fork", runs as an isolated sub-agent and yields its events.
    Otherwise (inline), injects the rendered prompt into the current agent loop.

    Args:
        skill: SkillDef to execute
        args: raw argument string from user (after the trigger word)
        state: AgentState
        config: config dict (may contain _depth, model, etc.)
        system_prompt: current system prompt string
    Yields:
        agent events (TextChunk, ToolStart, ToolEnd, TurnDone, …)
    """
    # 加载 SKILL.md，替换参数
    rendered = substitute_arguments(skill.prompt, args, skill.arguments)
    message = f"[Skill: {skill.name}]\n\n{rendered}"

    if skill.context == "fork":
        yield from _execute_forked(skill, message, config, system_prompt)
    else:
        yield from _execute_inline(message, state, config, system_prompt)

def _execute_inline(message: str, state, config: dict, system_prompt: str) -> Generator:
    """Run skill prompt inline in the current conversation."""
    import agent as _agent
    yield from _agent.run(message, state, config, system_prompt)

def _execute_forked(
    skill: SkillDef,
    message: str,
    config: dict,
    system_prompt: str,
) -> Generator:
    """Run skill as an isolated sub-agent (separate conversation context)."""
    import agent as _agent
	
	# 修改执行上下文，覆盖模型和工具
    # Build a sub-agent config with depth tracking
    depth = config.get("_depth", 0) + 1
    sub_config = {**config, "_depth": depth, "_system_prompt": system_prompt}
    if skill.model:
        sub_config["model"] = skill.model
    # allowed-tools 表示这些工具已经预先批准，不需要询问用户
    if skill.tools:
        sub_config["_allowed_tools"].append(skill.tools)

    # Run in fresh state (no shared history)
    # 这里是简化实现，实际上 fork 语义下应该有更清晰的输出机制，现在把所有东西都 yield 出来，工具调用、错误和中间状态都会暴露；更简洁的方式是 forked agent 生成一个最终结果消息，并将其作为单个 tool_result 注入回来
    sub_state = _agent.AgentState()
    yield from _agent.run(message, sub_state, sub_config, system_prompt)
```

注意，skill 的 prompt 要用 `role: "user"` 注入，因为它是临时行为，不能像 system prompt 那样在整个对话过程中都持续影响模型。

为了不让用户在 CLI 界面被上千词的 skills prompt 淹没，Claude Code 采用了注入两条 user 消息的办法，采用一个标志 `isMeta` 来控制其是否显示在消息界面中：

- 第一条 metadata，`isMeta: false`，用户可见，展示当前 skill 已经被加载进来，长度控制在 50-200 词；
- 第二条 skill prompt，`isMeta: true`，加载 SKILL.md 的全部内容，只发送给 API，用户不可见。

显示在界面上的 metadata 形如：

```text
<command-message>The "pdf" skill is loading</command-message>
<command-name>pdf</command-name>
<command-args>report.pdf</command-args>
```

### Skills 执行

在上述步骤之后，系统构建完整的消息列表发给 API，包含所有之前的对话消息，以及新注入的 skills 消息。以操作 pdf 为例，消息列表大概如下：

```json
// Complete message array sent to API for Turn 1
{
  model: "claude-sonnet-4-5-20250929",
  messages: [
    {
      role: "user",
      content: "Extract text from report.pdf"
    },
    {
      role: "assistant",
      content: [
        {
          type: "tool_use",
          id: "toolu_123abc",
          name: "Skill",
          input: { command: "pdf" }
        }
      ]
    },
    {
      role: "user",
      content: "<command-message>The \"pdf\" skill is loading</command-message>\n<command-name>pdf</command-name>"
      // isMeta: false (default) - VISIBLE to user in UI
    },
    {
      role: "user",
      content: "You are a PDF processing specialist...\n\n## Process\n1. Validate PDF exists\n2. Run pdftotext...",
      isMeta: true  // HIDDEN from UI, sent to API
    },
    {
      role: "user",
      content: {
        type: "command_permissions",
        allowedTools: ["Bash(pdftotext:*)", "Read", "Write"],
        model: undefined
      }
    }
  ]
}
```

在这之后，模型就有了专门的 pdf 处理流程 prompt 和 pre-approved 权限调用工具 `Bash(pdftotext:*), Read, Write`（执行上下文）。

> By treating specialized knowledge as _prompts that modify conversation context_ and _permissions that modify execution context_ rather than _code that executes_, Claude Code achieves flexibility, safety, and composability that would be difficult with traditional function calling. — Han Lee, [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

### REPL 中的 Skills

**除了**模型自主调用之外，另一种使用 skills 的方式是用户显式要求调用，比如输入 `/code-review fix bug`。回顾我们在[第一部分](https://liyixian06.github.io/2026/06/agent-03/#repl)里提到的 REPL，它是前台的主循环，负责处理 agent loop 抛出的事件；此处，在将用户输入提交给 `run(...)` 之前，首先要识别并处理所有 "/" 开头的命令。

```python
def repl(config: dict, initial_prompt: str = None):
	while True:
		# 捕捉用户输入
        try:
            cwd_short = Path.cwd().name
            prompt = clr(f"\n[{cwd_short}] ", "dim") + clr("❯ ", "cyan", "bold")
            user_input = input(prompt).strip()
        if not user_input:
            continue
		
		# 首先处理 "/" 开头的命令，包括内置斜杠命令和 skills
        result = handle_slash(user_input, state, config)
        # 如果识别到 skills，就注入
        if isinstance(result, tuple):
            skill, skill_args = result
            info(f"Running skill: {skill.name}" + (f" [{skill.context}]" if skill.context == "fork" else ""))
            try:
                from skill import substitute_arguments
                rendered = substitute_arguments(skill.prompt, skill_args, skill.arguments)
                run_query(f"[Skill: {skill.name}]\n\n{rendered}")
            except KeyboardInterrupt:
                print(clr("\n  (interrupted)", "yellow"))
            continue
        if result:
            continue
        ...
```

也就是说，在专门的处理函数 `handle_slash` 中，一次实现两种斜杠开头的功能：拆出斜杠命令 cmd，查内置 `COMMANDS` 表，如果发现 cmd 不是内置的斜杠命令（比如 `/help`，`/clear`，`/model`），就 fallback 到认为用户想要调用 skills，进入 skills 查找和调用。

```python
def handle_slash(line: str, state, config) -> Union[bool, tuple]:
    """Handle /command [args]. Returns True if handled, tuple (skill, args) for skill match."""
    if not line.startswith("/"):
        return False
    parts = line[1:].split(None, 1)
    if not parts:
        return False
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    handler = COMMANDS.get(cmd)
    if handler:
        handler(args, state, config)
        return True

    # Fall through to skill lookup
    from skill import find_skill
    skill = find_skill(line)
    if skill:
        cmd_parts = line.strip().split(maxsplit=1)
        skill_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        # 返回 tuple，告诉 REPL 这是个 skill，要继续处理
        return (skill, skill_args)

    err(f"Unknown command: /{cmd}  (type /help for commands)")
    return True
```

`find_skill` 的实现比较简单：取输入第一个词 `/code-review`，逐个遍历所有 skill 的 triggers 列表，精确匹配（\=\=）或前缀匹配（`startswith`）。

```python
def find_skill(query: str) -> Optional[SkillDef]:
    """Find a skill whose trigger matches the first word (or whole string) of query."""
    query = query.strip()
    if not query:
        return None

    first_word = query.split()[0]
    for skill in load_skills():
        for trigger in skill.triggers:
            if first_word == trigger:
                return skill
            if trigger.startswith(first_word + " "):
                return skill
    return None
```

> 这和之前所说的“agent 选择 skill 的过程中没有任何算法”是不矛盾的，前者是模型通过推理调用，此处是用户用确定的字符串调用。

### Skills 设计原则

Skillls 的核心矛盾在于能力与可预测性之间的平衡。如果 skills 系统赋予模型过大的自由度（例如任意执行 shell、完全访问工具），就会变得不可预测且难以 audit。而如果限制过多（例如仅支持静态 prompt 注入），则会失去 skills 的价值所在。shell 替换 + `allowed-tools` + `context: fork` 三元组是一个合理的解决方案：skills 可以在加载时与环境交互（shell 替换），可以缩窄执行环境（`allowed-tools`），并且可以隔离（fork）。其缺点在于复杂性和 attack surface。

另外，skills 应该是幂等的。一个设计良好的 skill 无论在会话中被调用多少次，都应该产生相同的上下文 modification；Claude Code 通过会话级缓存来处理这个问题（一旦加载，主体就会保留在上下文中）。需要在注入时进行去重，或者增加一个已加载技能的注册表。
