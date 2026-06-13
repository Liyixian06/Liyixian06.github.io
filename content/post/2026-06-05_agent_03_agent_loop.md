---
layout:		 single
title:       "Agent 03：一个简单实现（1）Agent Loop"
subtitle:    ""
description: "从 agent loop 到 event stream"
date:        2026-06-05T17:01:12+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent", "claude code"]
categories:  ["Tech" ]
URL: "2026/06/agent-03/"
math: False
---

在[上一章](https://liyixian06.github.io/2026/05/agent-02/)内容中，粗糙地讲述了一个 Agent 系统的大概架构，但仍然停留在理论层面，较为抽象，从这一章开始，我们来简单地实现一个类似 Claude Code 架构的 coding agent，Nano Claude Code。

这个系统约 7k 行代码，主要包含的部分有：

- 多 provider 适配、系统提示词、配置持久化
- 工具调用
- 上下文压缩、记忆
- 子代理
- Skill
- MCP

> 代码主要来自于 [CheetahClaws(v3.01)](https://github.com/SafeRL-Lab/cheetahclaws/tree/main)，同时也结合了一部分 [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 和 Claude Code 本身，以及 [Claude Harness](https://claude-harness.dev/zh) 的文章；由于 Claude Code 是 TypeScript 写的，下面的代码中可能会混用 Python 和 TypeScript，意会即可。
### One Loop Is All You Need

在 [ReAct](https://liyixian06.github.io/2026/05/agent-02/#react) 一节中已经讲过，LLM 将思考和行动交替进行，循环 Thought -> Action -> Observation……。具体而言，在用户输入初始消息后，agent 系统就会进入这个循环，其中 action 即调用工具，observation 即将工具调用的结果追加到上下文中，直到 LLM 不再调用工具，循环停止。

用户输入一定会作为第一条消息：

```python
messages.append({"role": "user", "content": query})
```

将初始消息作为参数放进 loop，开始循环：

```python
def agent_run(messages):
    while True:
        # 1) 发送：系统提示 + 对话历史 + 工具定义
        # 注意，这个循环中每一次给 LLM 发送询问，对它来说都是全新的
        response = llm_stream_or_call(
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )

        # 2) 取出完整的 LLM 响应（文本 + tool_calls）追加到消息中
        assistant_turn = response.assistant_turn
        messages.append(assistant_turn)

        # 3) 如果没有工具调用，结束
        if not assistant_turn.tool_calls:
            return assistant_turn

        # 4) 如果有工具调用，逐个执行工具，把执行结果追加到消息中
        tool_results = []
        for call in assistant_turn.tool_calls:
            output = TOOL_HANDLERS[call.name](**call.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": output,
            })

        messages.append({"role": "user", "content": tool_results})
```

具体实现上各个 agent 会有一些区别，但是大同小异。这就是整个系统的主循环，其他所有机制都是在这上面叠加的。

### 事件流 Event Stream

对于 Claude Code 这一类 Agent CLI，一个重要的工程设计是把上面的 agent loop 变成了事件流（event stream），换言之，把内部发生的所有事情实时暴露出来。  

```python
# 原来的版本
result = agent_run(...)
print(result)

# 事件流
for event in run(...):
    handle(event)
```

也就是说，run(...) 是一个生成器（generator），它不再最后返回一个 result，而是把所有重要动作（思考、文本输出、工具调用等）包装成事件 yield 出去，交给上层的 UI 消费者去处理。

```text
Agent
 ├─ yield ThinkingChunk
 ├─ yield TextChunk
 ├─ yield ToolStart
 ├─ yield ToolEnd
 ├─ yield PermissionRequest
 ├─ yield TurnDone
 └─ ...
```

> 生成器机制中，函数执行到一半，暂停，把控制权交给调用方，调用方决定什么时候继续；具体可以看[廖雪峰对生成器的说明](https://liaoxuefeng.com/books/python/advanced/generator/index.html)。

为什么要这么做？因为我们最开始写的那个循环对批量 API 调用来说没问题，但对于交互式的终端 UI，想要执行以下操作时，这种方式就行不通了：

- 观察模型思考过程中的 token stream
- 实时观看工具调用执行过程
- 在执行 destructive 的操作之前（比如 Edit / Write），先请求用户 permission
- 取消一次工具调用
- 观察 sub-agent 在嵌套任务里执行了什么操作

这里的 insight 在于，在 agent loop 过程中可能会有多个 stakeholders 要在不同的层级、不同的时间出于不同的目的使用其输出；只在最后 return 值是没有帮助的。

> 除此之外，交互体验也很重要，事件流可以直接一边输出一边打印，用户能够实时看到进度，否则长答案可能会把终端卡住很长时间。

事件流版本的 agent 循环如下：

```python
def run(user_message: str) -> Generator:
    """
    Multi-turn agent loop (generator).
    Yields: TextChunk | ThinkingChunk | ToolStart | ToolEnd |
            PermissionRequest | TurnDone
    """
    # 将用户输入追加到消息中
    messages.append({"role": "user", "content": user_message})

    while True:
        # Stream from provider
        # 这里可以看出，整个系统其实是多层生成器的嵌套
        for event in streamLLM(...):
        	# 实时向外发送事件
            if isinstance(event, (TextChunk, ThinkingChunk)):
                yield event
            # 最后会收到完整回复
            elif isinstance(event, AssistantTurn):
                assistant_turn = event

        # 将 LLM 的完整回复追加到消息中
        messages.append({
            "role":       "assistant",
            "content":    assistant_turn.text,
            "tool_calls": assistant_turn.tool_calls,
        })
		# 这一轮对话结束
        yield TurnDone()
		# 如果没有工具调用，结束
        if not assistant_turn.tool_calls:
            break

        # 如果有工具调用，逐个执行工具，把执行结果追加到消息中
        for tc in assistant_turn.tool_calls:
            yield ToolStart(tc)
            req = PermissionRequest(tc)
            yield req
            if req:
				result = execute_tool(tc)
            yield ToolEnd(tc, result)

            messages.append({
                "role":       "tool", # 也可以伪装成user消息
                "content":    result,
            })
```

这里的核心机制就是 `yield` 暂停，将控制权交给消费者；消费者可以处理该事件（渲染文本、显示 spinner、log trace），然后用 `next()` 让生成器继续运行。  
消费者包括最外层的 REPL、TUI、Web UI、VSCode 插件等，这样同一个 agent 内核可以挂很多不同前端，而不需要修改核心逻辑。

#### REPL

上层消费者如何使用 agent loop yield 出来的这些事件？

介绍一个概念 REPL（Read-Eval-Print Loop），这个词最早来自 Lisp、Python 解释器，可以让用户输入代码片段，并立即获得代码的执行结果。比如，我们打开 Python：

```python
>>> x = 10
>>> x * 2
20
```

这背后是一个循环：

```python
while True:
    user_input = read()
    result = eval(user_input)
    print(result)
```

这就是 REPL。但在 agent 系统中，REPL 并不长这样，因为正如我们前面介绍的，agent loop 不是一个同步函数，它会持续生产事件，并暂停下来等待消费者处理。因此，这里的 REPL 结构上是一个和 agent loop 非常相似的 `for await...of` 循环，带有一个分发机制：

```typescript
async function REPL(userInput: string) {
  const stream = agentLoop(buildMessages(userInput), allTools);

  for await (const event of stream) {
    switch (event.type) {
      case 'TextChunk':
        process.stdout.write(event.text);      // 终端输出
        break;

      case 'ThinkingChunk':
        if (verbose) renderThinking(event.text); // 选择性展示
        break;

      case 'ToolStart':
        renderToolCall(event.name, event.input); // 输出 "Running bash..."
        startSpinner();
        break;

      case 'ToolEnd':
        stopSpinner();
        renderToolResult(event.result);
        break;

      case 'PermissionRequest':
        const approved = await promptUser(event.description);
        // This is the magic: the generator is paused waiting for this
        stream.next(approved);  // 把结果给 agentloop，让它继续执行
        break;

      case 'TurnDone':
        renderPrompt();
        break;
    }
  }
}
```

可以看到，agent loop 只管抛出事件，REPL 负责一切处理，包括打印和请求工具权限等。终端/Web GUI 等 UI 都是相同的消费者，它们只是处理事件的方式不同；而 agent loop 完全不知道自己运行在哪里，是在和终端还是 GUI 通信，这就是 UI 解耦的优势所在，类比传统项目的前后端分离。

#### Permission

权限请求是一个双向的 yield 操作，生成器会暂停，并等待消费者带着值恢复它：

```python
# agent loop 内部
req = PermissionRequest(
    tool="Bash",
    command="rm -rf build"
)
yield req

if req.granted: 
	result = execute_tool(tc)

# REPL 内部
for event in run(...):
    if isinstance(event, PermissionRequest):
        event.granted = ask_permission_interactive(event.description)
```

当 REPL 收到 `PermissionRequest` 事件时，它会暂停，向用户显示 `[y/N]` 提示，等待用户输入，然后调用 `stream.next()` 。生成器会恢复运行，然后根据获得的 permission 继续执行或中止，整个过程不使用线程、回调函数或者外部状态。

这在架构上很重要，permission 并不是一个全局的 flag，而是控制流里的一级暂停点，响应会通过生成器 protocol 返回；换言之，所有状态都存在 `req` 对象中，我们可以从生成器这一来一回的 call-return 结构里直接获得 permission，不需要额外的变量。

#### Sub-Agent 的事件传播

Sub-Agent 是非常能体现事件流价值的另一个地方。当调用 agent 工具，为子任务生成 subagent 时，它也需要执行一模一样的 agent loop，最朴素的实现就是将 agent 工具函数直接转发到 run 循环上：

```python
def execute_agent_tool(task):
    result = run(task)
    return result
```

但这样有个很大的问题，subagent 运行期间发生的事情都没有暴露出来，主 agent 只能看到最终的结果。在事件流中，我们可以递归地把 subagent 产生的事件一路冒泡到最上层：

```typescript
// 主 agent loop 中的工具调用
async function* executeTool(call: ToolCall): AsyncGenerator<AgentEvent> {
  if (call.name === 'Agent') {
  	yield { type: 'ToolStart', name: 'Agent' };
    // Sub-agent is also a generator; yield* flattens its events into our stream
    const result = yield* agentLoop(
      buildSubtaskMessages(call.input),
      call.input.tools
    );
    yield { type: 'ToolEnd', name: 'Agent', result };
  } else {
    // ...
  }
}
```

`yield*`（Python 中写作 `yield from`）是关键，它可以消费子生成器的事件；subagent 内部生成的任何事件，都能通过 `yield*` 向上传递给主 agent，从而传递给 REPL。对于深度嵌套的 agent，`yield*` 链可以递归地处理这种情况，无需额外代码，这是生成器优于回调函数或者 promise 机制的重要原因之一。

如果 REPL 可以收到所有的 agent 事件，它怎么区分主 agent 和 subagent？  
Claude Code 的做法是给所有消息打标签，使用一个字段 `parent_tool_use_id`，如果是主 agent，这个字段为空，如果是 subagent，就是创建它的那个 tool 的 ID；因此，事件流实际上是被摊平的一条线，不是一棵树，树是根据 `parent_tool_use_id` 构建出来的。

> 有一个设计 tradeoff：一旦 flatten 事件流，就不能做真正的子树 cancellation 或子树隔离，除非 tool runtime 支持 scoped cancellation tokens。

#### 观测、中断和取消

这几个东西都是事件流天然附带的，就一并介绍了。

事件流天然带有 observability，因为每个动作都会作为事件抛出，只要封装生成器，就可以非常容易地记录：

```typescript
async function* withTracing(
  inner: AsyncGenerator<AgentEvent>
): AsyncGenerator<AgentEvent> {
  for await (const event of inner) {
    telemetry.record(event);    // log to OpenTelemetry, Sentry, whatever
    yield event;                // 原样抛出
  }
}

const traced = withTracing(agentLoop(...));
```

而且因为我们已经有了 `parent_tool_use_id` 字段，把它用在 tracing 里，就可以知道这些事件之间的结构关系是什么样的。

由于生成器在每次 `yield` 时都会暂停，因此消费者拿到控制权后可以停止调用 `next()` ，而改为调用生成器的 `return()`，直接截断接下来的内容，生成器自然挂起的地方就是自然取消的 checkpoint。

```typescript
// 用户按了 Ctrl+C
process.on('SIGINT', () => {
  activeStream.return(undefined);  // 生成器收到 GeneratorReturn, 清理现场
});
// 当然，实际上还要复杂得多，每种异常退出都需要做必要的清理，返回 reason，Claude Code 有十几种退出原因
```

中断（Interruption）和取消（Cancellation）很像，但并不一样，前者指的是允许用户在响应过程中插入新的指令。这个功能是通过在每次 `yield` 语句处检查一个 flag 来实现的。由于生成器在每个 chunk 和每次工具调用之间都会 yield，因此延迟可以非常低。

> 这种方式只在 yield 的边界有效，如果是工具执行中的 runtime，生成器也拿不到权限；所以 agent 系统通常会在工具执行中也加一个 cancel token，工具自己定期检查一下是否要取消执行。

### 会话对象 State

主循环 `while(True)` 中，怎么把上一轮发生的事情传递给下一轮？  
Claude Code 把所有要传递的 runtime state 全都打包放到一个 `State` 对象中，每轮循环开始时读出来，结束时修改 state 写回。

最简单的 state 其实就是 messages，也就是给 LLM 传递的上下文，但我们很快就能发现，有很多东西不应该写进 messages。

```python
class AgentState:
"""Mutable session state. messages use the neutral provider-independent format."""
	messages: list = field(default_factory=list)
	total_input_tokens: int = 0
	total_output_tokens: int = 0
	turn_count: int = 0
```

比如这里的 `total_input_tokens`，这是 runtime 关心的，不是 LLM 关心的，我们不会把这个塞给模型。按照这个逻辑，可以把 state 里的信息划分成几个类别：

- 对话历史，给 LLM 使用，如 messages
- 执行环境，即 runtime config，在每次 query 中都不变，如 model 和 mcp 信息
- 循环状态，如 `turn_count` 和 `transition`（继续执行下一轮的原因，这样无需查看 messages 就知道这条路径在做什么）
- 日志，如追踪当前 query 嵌套深度的 `depth`

另外，有 subagent 的系统还会遇到一个问题，哪些状态是共享的、哪些是隔离的；一般来说，subagent 的 messages 都是全新的，配置都是共享主 agent 的。还有另外一些共享内容能提高 prompt 缓存的效率，就不在这里展开了。

### 架构原则

我问 Claude ：如果今天让你从零开始设计 Claude Code，在这种事件驱动的设计中，你会认为哪些架构原则是最重要的？

Claude Code 的回答是：

- 事件 identity 优于改变状态。Agent 中的每一次 meaningful transition 都是一个有 type 和 payload 的事件，而不是改变共享状态。这使得系统易于调试，可以从事件日志中复现对话，这也是实现 undo 或「回滚到此工具运行之前」的方式。
- Agent loop 必须与 UI 无关。Loop 不应知道或关心它是在终端、Web UI、CI pipeline 还是测试框架中运行，这意味着事件必须是可序列化的（JSON-safe），并且只有消费者需要知道渲染情况。
- 权限控制和 human-in-the-loop 是首要原则。生成器的双向 `yield` / `next` 机制使这一点非常自然；在任何其他设计模式（回调、Promise、事件发射器）中，为了暂停并等待用户响应，最终都会出现尴尬的外部状态，或者没完没了的回调。
- Composability 优于配置。Tracing、取消、限流、开销预算，这些都应该是生成器封装，而不是 agent loop 的参数，每个关注点都是独立的。添加 `withBudget(maxTokens)(agentLoop(...))` 比直接修改 `agentLoop` 以添加一个 budget 参数要优雅得多。

> The generator design pays a real complexity cost — you need to understand async iteration, bidirectional yield, and generator delegation. But for an agent that needs to stream output, ask for permission before destructive operations, support cancellation, run sub-agents, and work in both a terminal and a GUI — all the alternatives are worse. The complexity is inherent in the problem; generators just give it a clean shape.
