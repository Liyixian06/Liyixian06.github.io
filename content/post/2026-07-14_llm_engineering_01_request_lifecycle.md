---
layout:		 single
title:       "LLM 工程 01：一次完整的 AI 请求链路"
subtitle:    ""
description: " "
date:        2026-07-14T14:41:09+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "LLM engineering"]
categories:  ["Tech" ]
URL: "2026/07/llm-engineering-01/"
math: False
---

我们写 LLM 调用时，我们在写什么？最直截了当的想法，显然，是用户输入一个 prompt，调用 API request，LLM provider 返回响应，一个 demo 就跑起来了。AI 应用的首个版本通常是非常顺利的，但投入使用后则不然。几行代码的 chatbot 经常会遇到的问题包括但不限于：

- 多轮对话后的上下文太长，导致 token 超限，或者成本暴涨
- 单一 provider 如果故障，没有 fallback 时整个系统都会停摆
- 同一个请求执行了两次，落库、费用都重复做了两遍
- 模型只返回了一半 JSON，前端解析失败，后端只能看到不完整的 `{"status": "健康`
- AI 输出质量下降了，但是没有 tracing，不知道问题出在哪里
- ……

一次完整的 AI 请求，实际上是一条完整的跨越前后端多个模块的链路。接下来，我们 walkthrough 整个请求的生命周期，看看这种架构是如何在工程系统中实现的。

### 请求处理

用户消息（或来自其他服务的 API 调用）首先到达入口层：身份验证、速率限制、请求验证、租户/用户解析，以及路由到正确的对话/session。在 Claude Code 中，这就是 CLI/IDE 本身的处理过程；在企业助手中，它通常是位于应用程序后端前方的 API 网关（Kong、Envoy 或自定义的 FastAPI/Node 服务）。

### Orchestrator

Orchestrator 是 app layer 的核心——不是模型本身，而是围绕模型的代码。它负责：

- agent loop（应该再次调用 LLM、调用工具还是停止）
- turn-taking 和 step budgeting（最大 iteration、最大 token 数、timeout 时间）
- 决定由哪个 sub-agent 或 workflow 处理此请求（单次问答、多步骤任务或委托 sub-agent）

### 上下文组装

在任何 prompt 进入模型之前，都需要先组装出实际的输入。**这通常是整个系统中工程量最大的部分**，它需要从很多不同的地方组装：

- 对话状态管理
	- 规范的、持久化的对话记录（轮次、工具调用、工具结果、编辑/分支），通常使用数据库（Postgres、DynamoDB、Redis 用于缓存），session/线程 ID 为 key，而不仅仅是上下文窗口中的所有内容
- 记忆检索
	- 和 session 状态是分开存储的，通常是向量数据库或混合数据库（向量数据库+结构化键值表），查询依据是相关性而非时间
- RAG pipeline
	- 从外部知识库（文档、代码库、工单）中检索信息。它包含自身的sub-pipeline：重写 query、embedding、向量/关键词混合搜索、reranking、chunk selection 以及追溯 citation sources
- Prompt 管理/版本控制
	- system prompt、tool schemas 和 few-shot examples 不是硬编码字符串；成熟的系统会对它们进行版本控制（用 git 或在 LangSmith/Humanloop/内部工具等 prompt registry 中），进行 A/B 测试，并按 tenant 推广，以便在不全面部署的情况下进行迭代

上下文组装是要将上述所有内容，加上 token 预算，整合成连贯、有序的 prompt：系统指示、工具定义、检索到的上下文、相关记忆，以及（如果有必要，裁剪/总结后的）对话历史记录。这也是[上下文管理](https://liyixian06.github.io/2026/06/agent-05/)所在的地方：此处会主动做 token budgeting，为预期的输出保留空间。

*注意，Prompt 缓存是一项重要的设计约束，而不是事后考虑的因素——上下文组装的顺序通常是专门为了最大化缓存命中率而安排的（首先是静态 system prompt 和工具定义，最后是易失性检索内容），因为它对成本和延迟都有着实质性的影响。*

### LLM 网关

LLM 网关是非常重要的 AI 应用控制层，它将 app 和单个 provider 解耦。这一层所需要的有：

- 将来自不同 provider 的请求/响应规范化到内部 schema 中
- 重试（带退避机制）、超时处理、限流、熔断
- 模型路由/回退（例如，对于简单的问题，路由到更便宜/更快的模型；发生故障时回退到备用 provider）

有些时候，在没有一个完整的 AI platform layer 时，LLM 网关还会承担一部分下面的责任：

- 使用语义匹配或精确匹配缓存来避免冗余调用
- 请求/响应的 logging hooks
- 每个 tenant 的 rate limits 和预算上限

### Provider API

这部分可以理解为黑盒：我们发送消息、工具调用和参数，收到返回的文本/工具调用块。可能是同步返回或流式返回，可能经过 SSE、WebSocket 或普通 HTTP 响应体；除此之外，应用端不需要了解推理过程。

> 文本 delta 和工具调用进度通常会以接近实时的方式（SSE/WebSocket）重新流式传输到客户端，而不是使用缓冲，以便 UI 可以增量渲染。这要求应用层将模型流事件与工具执行事件（例如，“正在运行工具 X...”的说明）复用到一个面向客户端的流中。

### 响应解析

原始响应（通常是 SSE 流式传输的数据块）会被解析成结构化事件：文本 delta、工具调用块（带有参数，通常以部分 JSON 格式流式传输，需要增量验证）、stop reason、用量/成本数据。此层会在执行任何操作之前，根据 schema 验证工具调用参数，并将流式传输的片段重新组装成完整、格式良好的对象，还需要处理拒答和异常中断。

### 工具调用

如果解析后的响应包含工具调用，则由 orchestrator（而非模型）执行：查找工具实现，检查权限/沙箱环境，运行该工具（本地函数、MCP 服务器调用、子进程、API 调用），捕获结果或错误，并将其作为工具结果消息附加到 session 状态。然后循环返回上下文组装，以进行下一轮操作。此过程重复进行，直到模型返回最终答案或达到停止条件（最大 steps、超出预算、收到明确的“完成”信号）。

*工具执行是在沙箱中独立于 LLM 调用进行权限控制的，模型决定调用 `delete_file` 和应用程序实际允许调用是两个不同的信任边界。*

### Tracing

这部分包括了 logging、tracing、评估、cost tracking。这并非一个独立的步骤，而是围绕上述每一层进行集成：结构化 traces（通常基于 OpenTelemetry，或 LLM 专用工具如 LangSmith、Langfuse、Arize Phoenix）捕获发送的每个 prompt、每次工具调用、每个 token count 和延迟、每次请求的成本（模型 + tokens → 费用），以及离线/在线的评估 harness（总耗时、重试次数、429 次数、解析失败率等），它们将 traces 与 golden datasets 或 LLM-judges 进行比对，以获取 prompt 或模型更改前后的 regressions。
