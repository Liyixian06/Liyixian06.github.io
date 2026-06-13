---
layout:		 single
title:       "Agent 05：一个简单实现（3）上下文管理"
subtitle:    ""
description: " "
date:        2026-06-13T20:50:58+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent", "claude code"]
categories:  ["Tech" ]
URL: "2026/06/agent-05/"
math: False
---

本章，我们将实现 agent 的上下文管理系统。
### System Prompt

在任何一次调用 LLM 之前，都要先组装 system prompt。与代码不同，system prompt 是指导性的，无法进行单元测试，而且它的“执行”依赖于一个我们无法完全控制其行为的 LLM。  

哪些内容应该放在代码里，哪些放在 system prompt 里？有一个特定的原则：代码处理那些确定性的、可以验证的事情，system prompt 处理需要判断或概括的事情。如果某个行为绝对不能违反，它必须体现在代码中，而如果某个行为需要模型推断上下文并进行调用，则应该放在 prompt 中。这包括：什么时候需要询问用户，什么时候自行决定；如何处理歧义；当存在多种有效方法时该怎么做；以及如何传达不确定性。

System prompt 是非常 structured 的文档。它通常包括下面的内容：

- 身份和能力说明
	- 不是简单地说“你是一个有用的助手”，而是明确地说明 agent 是什么，它能做什么，不能做什么 ，这样才能让模型正确地 self-model。比如，Claude Code 的提示不仅是“you are a coding agent”，而是描述了 agent loop，它会调用工具，行为会产生现实世界的后果。这可以防止模型像在普通对话环境中那样进行推理。
- 运行环境描述
	- Agent 运行的环境是什么操作系统、哪个 shell、遵循什么工作目录约定，以及有哪些工具可用？
- 工具使用
	- 在什么情况下应该调用每个工具，调用前需要收集哪些信息，如何解读结果，以及失败时该如何处理。这部分通常是 system prompt 里最长的。
- 不确定性下的 decision-making policy
	- 当 agent 不知道答案时该怎么做？明确地指导模型：何时应该请求用户进一步说明，何时应该自行做出合理假设；如何表达不确定性；何时任务的歧义过多而应该停止，何时应该采取保守的 interpretation 继续执行。
- 任务分解和规划
	- 具体给 coding agent，模型应该先计划后行动，还是 act-then-reflect？它应该如何处理超出预期规模的任务？它应该主动使用 TodoWrite，还是只在处理耗时较长的任务时才使用？Claude Code 的 system prompt 让模型在修改文件之前进入 plan mode，以确保 destructive 的操作三思而后行。
- 错误处理和恢复
	- 工具调用失败时会发生什么？如果 bash 命令返回非零退出码会怎样？如果文件不在模型预期的位置？这里会列出恢复策略：使用不同的参数重试一次、在放弃前搜索文件、询问用户情况是否真的无法恢复。如果没有这部分，模型要么会陷入无限重试，要么会过早放弃。
- 通信和输出格式
	- 模型应该如何传达其进度、reasoning 和结果？此处包含了 verbosity、何时使用 markdown 而非纯文本、如何表明模型正在执行长时间运行的任务，以及如何在用户需要做出决策时呈现选项。这部分其实很重要，因为和用户体验直接挂钩。
- 行为约束和 safety invariants
	- “Never do this”的部分。和代码强制执行的硬性约束不同，这些是策略层面的约束，需要根据实际情况进行判断：不要在未确认的情况下进行不可逆的更改；不要在没有明确指示的情况下提交到 main 分支；不要在存在更安全的替代方案时删除文件。
- Session state 和记忆
	- 对于有外部记忆系统的 agent：应该如何使用这些记忆？哪些信息应该保存在 CLAUDE.md 文件中，哪些信息应该保存在 session 待办事项文件中，哪些信息应该保存在长期记忆中？

有些东西不适合出现在 system prompt 中：统计任何东西的次数（重试次数、对话轮次）、硬性限制（最大文件大小、timeout 值）、需要严格执行的顺序、任何需要不在 context 中的外部状态的东西——这些任务交给代码去做更合适。

在我们的简易实现中，system prompt 也至少需要包含下面这些信息：

```python
def build_system_prompt() -> str:
	# TEMPLATE 包含了身份、可用工具、行为指南
    # 注入当前日期、工作目录、平台信息、Git 信息、CLAUDE.md
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d %A"),
        cwd=str(Path.cwd()),
        platform=platform.system(),
        git_info=get_git_info(),
        claude_md=get_claude_md(),
    )
    # 持久化记忆
    memory_ctx = get_memory_context()
    if memory_ctx:
        prompt += f"\n\n# Memory\nYour persistent memories:\n{memory_ctx}\n"
    return prompt
```
### Compaction

一个 agent session 可能会持续很长时间，在大量的阅读文件、编辑、执行命令中，再大的上下文窗口也有填满的时候。上下文压缩（context compact）试图解决的问题是：如何在有限的上下文窗口中保留尽可能完整的语义？

没有一个单一策略能应对所有类型的 context pressure；和 permission system 类似地，我们有多层的上下文压缩流水线来处理这个问题。

#### Token 估算

在决定什么时候压缩之前，有一个基础的问题：现在使用了多少 token？

我们采用粗略的估算方式，直接将所有字符的长度除以 3.5（使用 3.5 字节/token 的比率）：

```python
def estimate_tokens(messages: list) -> int:
    """Estimate token count by summing content lengths / 3.5.

    Args:
        messages: list of message dicts with "content" field (str or list of dicts)
    Returns:
        approximate token count, int
    """
    total_chars = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    # Sum all string values in the block
                    for v in block.values():
                        if isinstance(v, str):
                            total_chars += len(v)
        # Also count tool_calls if present
        for tc in m.get("tool_calls", []):
            if isinstance(tc, dict):
                for v in tc.values():
                    if isinstance(v, str):
                        total_chars += len(v)
    return int(total_chars / 3.5)
```

Claude Code 的估算策略会稍微复杂一些，考虑了多种 content block 的类型，分别处理，但总的来说，思路是一致的。

```typescript
// 估算消息数组的总 token 消耗量
// 需要分别处理不同类型的 content block，因为它们的 token 特征各不相同
export function estimateMessageTokens(messages: Message[]): number {
  let totalTokens = 0
  for (const message of messages) {
    // 只统计用户和助手消息，跳过系统消息等其他类型
    if (message.type !== 'user' && message.type !== 'assistant') {
      continue
    }
    // 非数组内容（纯字符串）不在此处理
    if (!Array.isArray(message.message.content)) {
      continue
    }
    // 遍历每个 content block，按类型选择不同的估算策略
    for (const block of message.message.content) {
      if (block.type === 'text') {
        // 纯文本：直接用字符长度除以字节比率
        totalTokens += roughTokenCountEstimation(block.text)
      } else if (block.type === 'tool_result') {
        // 工具返回结果：可能包含嵌套的文本和图片，需要专门的计算函数
        totalTokens += calculateToolResultTokens(block)
      } else if (block.type === 'image' || block.type === 'document') {
        // 图片和文档：无法通过字符长度估算，使用固定值 2000 token
        totalTokens += IMAGE_MAX_TOKEN_SIZE
      } else if (block.type === 'thinking') {
        // 模型的思考过程：与普通文本相同的估算方式
        totalTokens += roughTokenCountEstimation(block.thinking)
      } else if (block.type === 'tool_use') {
        // 工具调用：将工具名和序列化后的输入参数合并估算
        totalTokens += roughTokenCountEstimation(
          block.name + jsonStringify(block.input ?? {}),
        )
      }
      // ...其他类型（如 redacted_thinking 等）
    }
  }
  // 乘以 4/3（约 1.33）作为安全系数
  // 粗略估算天然偏低，加上这个系数避免"以为还有空间但实际已溢出"的问题
  return Math.ceil(totalTokens * (4 / 3))
}
```

实际上，Anthropic 有个叫 `countTokens` 的 API 可以精确计数，真正在压缩策略里使用的方法是：先从最后一个有 API usage 数据的 assistant 消息获取精确的 token 数，后面的消息再使用上述的估算，相加两者得到总量，这样能达到精确和速度的平衡。

#### 压缩策略

什么时候该开始压缩？一般来说，会有几级阈值，每级到有效窗口上限的距离不同，触发不同的压缩行为；我们就将 threshold 设置为最大窗口的 70%，到达这个限制时自动压缩。

> 不是整个窗口空间都能用于对话，要为输出预留空间。

**工具结果清理**

Microcompact 是最轻量的压缩策略，它直接清理对话历史中旧的工具调用结果。理由很简单：查找、阅读文件等操作通常会返回非常长的结果，但在若干轮对话之后，这些结果的原文就不太重要了，可以清理掉。

Claude Code 定义了哪些工具的结果可以清理：

```typescript
// 可被 microcompact 清理的工具集合
// 选择标准：输出量大、信息密度随时间递减的"读取类"和"输出密集型"工具
// 注意：TodoRead、ToolSearch 等输出小、信息密度高的工具故意不在此列
const COMPACTABLE_TOOLS = new Set<string>([
  FILE_READ_TOOL_NAME,      // 文件读取——返回结果可能有数千行代码
  ...SHELL_TOOL_NAMES,      // Shell 命令——编译日志、测试输出等可能非常冗长
  GREP_TOOL_NAME,           // 搜索结果——匹配内容可能很多
  GLOB_TOOL_NAME,           // 文件匹配列表
  WEB_SEARCH_TOOL_NAME,     // 网页搜索结果
  WEB_FETCH_TOOL_NAME,      // 网页抓取内容
  FILE_EDIT_TOOL_NAME,      // 文件编辑的 diff 输出
  FILE_WRITE_TOOL_NAME,     // 文件写入的确认输出
])
```

不过我们的实现中就不管这些了，只要是旧的工具结果，一律都清理掉。

```python
def snip_old_tool_results(
    messages: list,
    max_chars: int = 2000,
    preserve_last_n_turns: int = 6,
) -> list:
    """Truncate tool-role messages older than preserve_last_n_turns from end.

    For old tool messages whose content exceeds max_chars, keep the first half
    and last quarter, inserting '[... N chars snipped ...]' in between.
    Mutates in place and returns the same list.

    Args:
        messages: list of message dicts (mutated in place)
        max_chars: maximum character length before truncation
        preserve_last_n_turns: number of messages from end to preserve
    Returns:
        the same messages list (mutated)
    """
    # 只清理最近n轮之前的旧结果
    cutoff = max(0, len(messages) - preserve_last_n_turns)
    for i in range(cutoff):
        m = messages[i]
        if m.get("role") != "tool":
            continue
        content = m.get("content", "")
        if not isinstance(content, str) or len(content) <= max_chars:
            continue
        # ...计算前半段和后1/4段
        m["content"] = f"{first_half}\n[... {snipped} chars snipped ...]\n{last_quarter}"
    return messages
```

**LLM 摘要**

Microcompact 不足以解决问题时，我们就该启动 LLM 压缩了：把旧消息拼接成文本，调用 LLM 生成一段摘要。

> 压缩 prompt 也是要设计的，至少要包括下面几个部分：
> - 用户消息
> - 请求和意图
> - 文件和代码片段
> - 遇到的错误/问题，和解决方法
> - 当前工作
> - 待完成的任务


```python
def compact_messages(messages: list, config: dict) -> list:
    """Compress old messages into a summary via LLM call.

    Splits at find_split_point, summarizes old portion, returns
    [summary_msg, ack_msg, *recent_messages].

    Args:
        messages: full message list
        config: agent config dict (must contain "model")
    Returns:
        new compacted message list
    """
    # 计算分割点，可以只压缩一部分内容
    # 这里是选择压缩分割点前面的消息，也可以压缩后面的
    split = find_split_point(messages)
    if split <= 0:
        return messages

    old = messages[:split]
    recent = messages[split:]

    # Build summary request
    old_text = ""
    for m in old:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, str):
            old_text += f"[{role}]: {content[:500]}\n"
        elif isinstance(content, list):
            old_text += f"[{role}]: (structured content)\n"

    summary_prompt = (
        "Summarize the following conversation history concisely. "
        "Preserve key decisions, file paths, tool results, and context "
        "needed to continue the conversation:\n\n" + old_text
    )

    # Call LLM for summary
    # 实际上压缩是要用一个 forked subagent 来做的，这里简化实现，直接调用了
    summary_text = ""
    for event in providers.stream(
        model=config["model"],
        system="You are a concise summarizer.",
        messages=[{"role": "user", "content": summary_prompt}],
        tool_schemas=[],
        config=config,
    ):
        if isinstance(event, providers.TextChunk):
            summary_text += event.text
	
	# 用两条新消息替换整个被压缩的部分
    summary_msg = {
        "role": "user",
        "content": f"[Previous conversation summary]\n{summary_text}",
    }
    ack_msg = {
        "role": "assistant",
        "content": "Understood. I have the context from the previous conversation. Let's continue.",
    }
    return [summary_msg, ack_msg, *recent]
```

Claude Code 的 prompt 使用了两阶段结构，先让 LLM 在 `<analysis>` 标签中整理思路，然后在 `<summary>` 标签中输出最终摘要，这样能得到比较高质量的结果，最后再把 `<analysis>` 部分去掉。

最终，把上面的两阶段压缩合并到一起，就有了我们的 compact 函数：

```python
def maybe_compact(state, config: dict) -> bool:
    """Check if context window is getting full and compress if needed.

    Runs snip_old_tool_results first, then auto-compact if still over threshold.

    Args:
        state: AgentState with .messages list
        config: agent config dict (must contain "model")
    Returns:
        True if compaction was performed
    """
    model = config.get("model", "")
    limit = get_context_limit(model)
    # 这里的 70% 是简化实现
    threshold = limit * 0.7

    if estimate_tokens(state.messages) <= threshold:
        return False

    # Layer 1: snip old tool results
    snip_old_tool_results(state.messages)

    if estimate_tokens(state.messages) <= threshold:
        return True

    # Layer 2: auto-compact
    state.messages = compact_messages(state.messages, config)
    return True
```

有一个重要的工程细节是，自动压缩不是无限次重试；Claude Code 内部定义了熔断器，如果压缩连续失败超过 3 次，就停止重试。

```typescript
// 熔断器：连续自动压缩失败的最大次数
// BQ 2026-03-10: 1,279 个会话出现了 50+ 次连续失败（最高达 3,272 次），
// 每天在全球范围内浪费约 25 万次 API 调用。引入此熔断器后问题得到控制。
const MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3

// 熔断检查：如果连续失败次数已达上限，直接放弃本次压缩
// 避免在持续失败的场景下无意义地消耗 API 调用和用户等待时间
if (
  tracking?.consecutiveFailures !== undefined &&
  tracking.consecutiveFailures >= MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES
) {
  return { wasCompacted: false }
}

```

另外，要注意在任何涉及消息剪切的操作里，`tool_use` 和 `tool_result` 的关系都不应该被破坏；换言之，任何 `tool_use` 都应该有对应的 `tool_result` 在上下文中（哪怕是报错信息），反之亦然，这部分需要被特别处理。

compact 函数在哪里使用呢？在 Agent Loop 中，将本次的用户消息追加到 message 里之后，在循环的开头每次调用，视情况决定是否压缩：

```python
def run(
    user_message: str,
    state: AgentState,
    config: dict,
    system_prompt: str,
) -> Generator:
    # Append user turn in neutral format
    state.messages.append({"role": "user", "content": user_message})

    # Inject runtime metadata into config so tools (e.g. Agent) can access it
    config = {**config, "_system_prompt": system_prompt}

    while True:
        # Compact context if approaching window limit
        maybe_compact(state, config)
        ...
```
