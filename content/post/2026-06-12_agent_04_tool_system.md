---
layout:		 single
title:       "Agent 04 一个简单实现（2）Tool System"
subtitle:    ""
description: " "
date:        2026-06-12T17:45:18+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent", "claude code"]
categories:  ["Tech" ]
URL: "2026/06/agent-04/"
math: False
---

上一章中，我们了解了 Agent Loop 的事件流架构；这一章，我们要展开实现让 agent 系统得以和外界交互的 tool system。

从结构上看，tool system 形如：

```text
LLM output
    ↓
Tool call parser
    ↓
Permission pipeline  ←── user / policy rules
    ↓
Scheduler  ←── concurrency declarations from tool metadata
    ↓
Executor
    ↓
Result formatter  ←── context budget from tool metadata
    ↓
Message history (next turn input)
```

核心思想在于，工具并不仅仅是可以调用的函数：它们是 self-describing 的对象，声明自身的行为属性，runtime 利用这些声明来做出调度、权限和呈现决策。LLM 从不会直接操作工具，它只会生成结构化的调用请求，由模型和实际 OS/filesystem 之间的 layered system 决定是否、何时、如何响应。

### 工具定义

工具定义是整个系统最基础的一层。这里需要明确的是，LLM 并不知道工具具体怎么实现，它只知道工具能做什么。比如，对一个 read 工具，LLM 能看到的只有：

```json
{
  "name": "Read",
  "description": "Read a file from disk",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string"
      }
    },
    "required": ["file_path"]
  }
}
```

它不知道具体的 readFile 函数是怎么实现的。因此，工具定义应该说是给 LLM 看的一个 prompt，这就是为什么 description 格外重要。

一个最简单的工具定义，就是名字-description-schema-函数的四元组：

```python
class ToolDef:
    """Definition of a single tool plugin.
    """
    name: str
    description: str
    schema: Dict[str, Any]
    # 传入 params 和 config
    func: Callable[[Dict[str, Any], Dict[str, Any]], str]
```

但在工业代码里，工具的实现要复杂得多。Claude Code 的工具定义大约如下（这也是精简后的版本）：

```typescript
export type Tool<
  Input extends AnyObject = AnyObject,
  Output = unknown,
  P extends ToolProgressData = ToolProgressData,
> = {
  // 身份
  aliases?: string[]       // 向后兼容的别名
  searchHint?: string      // 延迟发现时的关键词匹配
  
  // 核心方法
  call(args, context, canUseTool, parentMessage, onProgress?)
    : Promise<ToolResult<Output>>
  description(input, options): Promise<string>
  
  // Schema
  readonly inputSchema: Input           // Zod schema
  readonly inputJSONSchema?: ToolInputJSONSchema  // JSON Schema（MCP 工具用）
  
  // 行为声明
  isConcurrencySafe(input): boolean     // 是否可以与其他工具并行
  isEnabled(): boolean                  // 是否在当前环境中可用
  isReadOnly(input): boolean            // 是否是只读操作
  isDestructive?(input): boolean        // 是否执行不可逆操作
  interruptBehavior?(): 'cancel' | 'block'  // 用户中断时的行为
  
  // 权限
  checkPermissions(input, context): Promise<PermissionResult>
  validateInput?(input, context): Promise<ValidationResult>
  preparePermissionMatcher?(input): Promise<(pattern: string) => boolean>
  
  // 输出控制
  maxResultSizeChars: number            // 结果最大字符数
  readonly name: string
}
```

关注其中一些值得理解的设计：

- `searchHint` 在工具太多时，会做延迟加载和 tool discovery
- `call(...)` 直接把 runtime 对象传入
- `description(input, options): Promise<string>` 不是静态的，而是根据环境动态生成的，模型可以拿到实时的环境状态
- `inputSchema` 和 `inputJSONSchema` 是内置工具和 MCP 工具需要的不同 schema 格式
- 声明式的设计，工具主动声明它的行为特性，比如能否并行、是否只读、打断后应该如何处理（中止还是继续）等，让调度器可以作出正确的调度决策
- `maxResultSizeChars` 表明工具需要自己考虑 context budget，不能直接把所有结果都返回

为什么要在这里使用如此丰富的 runtime 对象？原则在于：The tool knows things about itself that no central coordinator should have to hardcode. 比如，如果要添加一个有特殊并发行为的新工具，应该在工具本身中声明，而不是在 scheduler 中声明。

### Tool Registry

所有工具都会被注册到一个中心结构 registry：

```python
class ToolRegistry {
  tools: Map<string, Tool> # name -> Tool
}
```

这样，在执行某个工具时，可以直接通过工具名来调用；另外，我们可以直接在 runtime 添加/删除工具，而不需要修改 call sites。

工具注册到 registry 中有两种方式，静态和动态。通常而言，内置工具会直接在工具定义相关的函数附近逐个创建并注册（静态注册），MCP 等外部工具会动态注册，然后它们统一被放入 tool pool。

```python
# 静态注册内置工具
def _register_builtins() -> None:
    """Register all built-in tools into the central registry."""
    _tool_defs = [
        ToolDef(
            name="Read",
            schema=TOOL_SCHEMAS[0],
            func=lambda p, c: _read(**p),
        ),
        ...
    ]
    for td in _tool_defs:
    	register_tool(td)

# 动态注册 MCP 工具
# 此处的方法是子模块在自身文件末尾调用注册函数，import 即自动注册
# mcp/tools.py connects to configured MCP servers and registers their tools.
# Connection happens in a background thread so startup is not blocked.
import mcp.tools as _mcp_tools  # noqa: F401
```

在我们的简单实现中，系统就直接把 tool pool 里的所有工具都发给 LLM 了；但在成熟系统中通常会有 runtime selection，也就涉及前面看到的 `searchHint` 字段，通常会匹配用户输入和 hint 先提前筛选一轮可能会用到的工具，这样后面 LLM 选择工具时，不需要每次都阅读 50 个工具描述。

registry 选出了工具之后，prompt assembly 会把这些工具变成模型能理解的格式，拼在 system prompt 里，概念上类似于这样：

```text
System Prompt

You are Claude Code.

Available tools:

Tool: LS
Description: List files and directories.
Schema: {...}

Tool: Glob
Description: Find files matching a pattern.
Schema: {...}

Tool: Read
Description: Read file contents.
Schema: {...}
```

> 如同前面所说，Claude Code 里实际的 description 是 runtime 生成的，模型可以看到带上下文的工具。为什么要这样设计？静态 description 中会包含对执行环境的假设，而这些假设在实际中往往不成立：
>
> - “列出当前目录的文件” —— 当前目录是什么？
> - “运行 python 脚本” —— 哪个脚本？它已经安装了吗？
>
> 如果单纯地告知 LLM 可以调用某个工具，但这个工具实际上不可用，它会尝试执行然后失败，从而浪费对话轮次。动态 description 能提供更准确的环境，减少对工具的无意义调用。

### 执行和结果

我们的执行函数如下所示：

```python
def execute_tool(
    name: str,
    params: Dict[str, Any],
    config: Dict[str, Any],
    max_output: int = 32000,
) -> str:
    """Dispatch a tool call by name.

    Args:
        name: tool name
        params: tool input parameters dict
        config: runtime configuration dict
        max_output: maximum allowed output length in characters

    Returns:
        Tool result string, possibly truncated.
    """
    # 通过名字在 registry 中查找工具
    tool = get_tool(name)
    if tool is None:
        return f"Error: tool '{name}' not found."
	
	# 调用实现
    try:
        result = tool.func(params, config)
    except Exception as e:
        return f"Error executing {name}: {e}"

    if len(result) > max_output:
        # 结果过长时保留头尾，中间截断
        result = (
            result[:first_half]
            + f"\n[... {truncated} chars truncated ...]\n"
            + result[-last_quarter:]
        )

    return result
```

这里还不涉及并发的调度，工业系统里，当 API 响应包含多个工具调用时，会有 StreamingToolExecutor 负责决定如何执行它们，并行还是串行。

另外，工具执行期间还可能会有进度消息（搜索进度、文件读取进度、子进程输出），progress message 应该立刻 yield 给用户。

工具执行完之后，其结果会写入消息（此处还有 prompt assembly 的参与，将结果结构化），这样下一轮调用时，模型能够看到刚刚发生了什么，并据此决定下一步行动。

### Permission System

Permission system 实际上是成熟 agent 和 toy agent 最大的区别之一——工具系统作为 destructive 的外挂，最关键的设计不是能力，而是约束——但是这里我们只做简单的实现，更详细的留待日后再讲。

通常而言，校验一个工具的权限时，首先检查已经设定好的规则（always allow 或 always deny），只有在无法自己判断时，才请求用户授权。

```python
for tc in assistant_turn.tool_calls:
            yield ToolStart(...)

            # Permission gate
        	# 还记得前面 Claude Code 工具定义中的权限字段吗？
            permitted = _check_permission(tc, config)
            if not permitted:
                req = PermissionRequest(description=_permission_desc(tc))
                yield req
                permitted = req.granted

            if not permitted:
                result = "Denied: user rejected this operation"
            else:
                result = execute_tool(...)
```

具体而言，在请求用户授权之前，我们会有一整套评估工具调用的流水线：

- 权限模式检查，根据当前的 permission mode 决定是否需要用户确认
- alwaysAllow 规则
- alwaysDeny 规则
- BASH classifier，特定用于 bash 工具，自动判断命令是否安全

```python
def _check_permission(tc: dict, config: dict) -> bool:
    """Return True if operation is auto-approved (no need to ask user)."""
    # 检查权限模式，根据权限模式选择不同的放行策略
    perm_mode = config.get("permission_mode", "auto")
    if perm_mode == "accept-all":
        return True
    if perm_mode == "manual":
        return False   # always ask

    # "auto" mode: only ask for writes and non-safe bash
    name = tc["name"]
    if name in ("Read", "Glob", "Grep", "WebFetch", "WebSearch"):
        return True
    if name == "Bash":
        from tools import _is_safe_bash
        return _is_safe_bash(tc["input"].get("command", ""))
    return False   # Write, Edit → ask


# BASH classifier 的实现非常直接，就是列出所有安全的命令，判断是不是
# 这个方式并不算安全，比如 python script.py 就可以通过检查
# ── Safe bash commands (never ask permission) 

_SAFE_PREFIXES = (
    "ls", "cat", "head", "tail", "pwd", "echo", "printf", 
    "git log", "git status", "git diff", "git branch",
    "find ", "grep ", "python ", "python3 ",
    ...
)

def _is_safe_bash(cmd: str) -> bool:
    c = cmd.strip()
    return any(c.startswith(p) for p in _SAFE_PREFIXES)
```

如果经过了 `check_permission` 还是无法决定，才会调用 `PermissionRequest` 弹出交互式请求。

```python
# REPL 循环里，遇到 yield 出的 PermissionRequest 就调用交互函数
for event in run(user_input, state, config, system_prompt):
    if ...
    elif isinstance(event, PermissionRequest):
        event.granted = ask_permission_interactive(event.description, config)

# 交互函数
def ask_permission_interactive(desc: str, config: dict) -> bool:
    try:
        print()
        ans = input(clr(f"  Allow: {desc}  [y/N/a(ccept-all)] ", "yellow")).strip().lower()
        # 如果选择了总是允许，那么就修改权限模式
        if ans == "a":
            config["permission_mode"] = "accept-all"
            ok("  Permission mode set to accept-all for this session.")
            return True
        return ans in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print()
        return False
```

很有趣的是，permission system 还会把用户行为写入上下文，比如用户刚才拒绝了调用某个工具/某个命令，于是 LLM 会重新规划。

### 设计原则

- 将工具 contract 和工具实现分开。最通用的模式是，caller 与 declared interface（ `isReadOnly` 、 `isConcurrencySafe` 、 `checkPermissions` ）交互，而不是与函数体交互，这样系统无需运行工具，即可检查其声明的内容。
- Permission pipeline 应该按照 cost 排序，而不是按照重要性排序。速度快、成本低的检查（权限模式、always allow/deny）优先进行，成本高的、交互式检查（请求用户授权）后进行，这样最常见的情况（auto approve）可以最快地通过。
- Context budget 在任何时候都是首要考虑的，工具返回结果时也不例外。
- Tool metadata enables scheduling decisions you can't make otherwise.
- 用户行为是模型的输入。将 permission deny 写在上下文中，比任何 retry logic 都更 robust，因为它利用了模型自身的推理能力来处理 recovery。
