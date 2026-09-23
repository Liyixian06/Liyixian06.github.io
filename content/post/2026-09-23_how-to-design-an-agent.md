---
layout:		 single
title:       "如何从头设计一个 Agent 系统"
subtitle:    ""
description: " "
date:        2026-09-23T02:51:40-04:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent"]
categories:  ["Tech" ]
URL: "2026/09/how-to-design-an-agent/"
math: False
---

**一、定义 Agent 在替谁完成什么任务**

首先回答的问题其实是，是否有必要做 agent？因为开放的系统意味着引入更多不确定性，和更多要为之兜底的组件。

考虑人类来做这个任务，流程是什么？先写一个很具体的 task loop，关键是把这个领域里真正的决策点找出来。

如果写完发现 loop 很开放，下一步动作很难提前写死，那就更适合 ReAct / Plan-Act；反之，则是一个有强业务流程、局部 agent 化的 workflow。

**二、决定哪些东西交给模型，哪些东西必须由 framework 控制**

一般来说，模型擅长：

- 理解模糊目标
- 语义判断
- 计划下一步
- 从非结构化数据里抽取信息
- 在多个方案间做 contextual decision
- 根据执行结果调整

Framework 应该控制：

- 权限
- 状态
- 持久化
- retry
- timeout
- concurrency
- idempotency
- transaction
- resource limit
- security boundary
- audit log

原则很简单，语义决策交给模型，机械保证交给代码。

**三、设计 Environment 和 Action Space**

Agent 能力很大程度上是由它能看到什么、能做什么决定的，需要首先定义这些东西，它们最终决定了 tool system 和 HITL。

**四、设计 State，任务需要记住什么**

Agent framework 里非常容易混淆的三个东西：Conversation state、Task state、Long-term memory，设计时有必要区分。

**五、决定 Agent Loop 形态**

决定具体的 ReAct / Plan-Act / workflow 结构；看任务确定性高不高、horizon 长不长，经常是 hybrid 模式。

```
Workflow
   ↓
某一步进入 Agent Loop
   ↓
ReAct / PlanAct
   ↓
回到 Workflow
```

**六、Human-in-the-Loop**

HITL 最好是基于 action risk classification，就是先找不可接受的错误，然后定义 intervention points（action 前、mid-task、action 后）；另外还要考虑给人类传递什么上下文。

**七、列出失败模式**

问：What might go wrong? 给每一个 failure 找 owner（模型/tool layer/context/runtime/人类），这样 framework 组件会自然出现。

**八、最后才决定需不需要 Skill、Memory、Subagent、MCP**

把这些东西都当成问题的答案，而不是默认组件，没有需求就别加。

- Memory：有跨任务信息需要保留吗？
- Skill：有重复出现的 SOP 吗？
- Subagent：有可以隔离、并行、独立验证的子任务吗？
- MCP：需要动态接第三方 capability 吗？
- Hook：是否需要 deterministic lifecycle interception？
- Plugin：是否希望第三方扩展 runtime？

这点可以学习 Pi 的哲学，不要提前构造一个完整 Agent Framework。



**Case：购物网站客服** *by GPT*

这个系统大概有几类任务：

- 纯问答：订单状态、退货政策、商品规格、优惠规则
- 信息搜索：帮用户找商品、筛选候选、比较
- 可逆操作：加入购物车、移出购物车、修改数量、保存 wishlist
- 有业务影响但还能补救的操作：申请退货、取消订单
- 高风险操作：退款、修改收货地址、支付、使用优惠券、替用户下单

这里马上能看出，不能把所有工具都平等暴露给模型。给它一个带权限层级的 action space，比如：

```
Level 0: read-only
- search_products
- get_product_detail
- get_order
- get_return_policy

Level 1: reversible
- add_to_cart
- remove_from_cart
- update_cart_quantity
- add_to_wishlist

Level 2: business side effect
- initiate_return
- cancel_order

Level 3: financial / identity sensitive
- issue_refund
- change_shipping_address
- place_order
```

然后 framework 规定：

```
L0: agent 可以直接做
L1: 默认直接做，但必须展示结果
L2: 需要满足业务条件，必要时确认
L3: 必须用户明确确认，甚至走额外认证
```

一定要明确，权限是 runtime 的事情，不是 prompt 的事情。

接下来设计 agent 的核心状态，至少分成四种，不能把所有内容都塞进聊天记录里：

```python
class CustomerServiceState:
    conversation # 用户和 agent 的自然语言对话
    user_context # 当前登录用户、会员等级、默认地址、已有订单等
    task_state # 这一轮到底在做什么
    action_history # agent 已经执行了哪些有副作用操作
```

注意这里的状态不能只存在 prompt 里，要独立持久化。

然后看 agent loop，这个系统不要做成纯 ReAct，因为购物客服其实有很强的 workflow 成分，应该做 hybrid。

最外层：

```
User message
    ↓
Intent / goal detection
    ↓
Route to domain workflow
    ↓
Inside workflow:
    model reasons + uses tools
    ↓
Validate action
    ↓
Execute
    ↓
Observe result
    ↓
Continue / ask user / finish
```

例如退货：

```
identify order
→ identify item
→ check eligibility
→ collect reason
→ determine return options
→ confirm
→ initiate return
→ return label / pickup info
```

这个流程基本是业务定义好的，没必要让 LLM 每次从头思考下一步是不是应该检查退货资格，framework 应该知道。

但在某些节点，模型负责语义判断。比如用户说“右边声音断断续续，有时候完全没声”，模型可以映射成 `reason = defective`，换言之，workflow 决定大结构，LLM 处理模糊语义和局部决策。

商品搜索则完全不一样，比如用户说想买个一百刀以内的机械键盘，别太吵，主要写代码，这就更像 agentic search：

```
extract constraints
→ search
→ inspect candidates
→ refine
→ maybe search reviews/specs
→ rank
→ explain
```

模型自主空间可以大很多，这类任务用 ReAct 就比较自然。
所以同一个客服 agent 内部，可能有不同的 loop：

```
FAQ              → retrieval + answer
product search   → ReAct
return           → state machine
cancel order     → workflow
cart operation   → direct tool use
complaint        → conversation + escalation
```

这也是设计 agent system 很重要的一点，不要执着于只有一个 universal agent loop。

再说 tool layer，要求每个 tool 有比普通 function schema 更多的 metadata，因为这些 metadata 和业务逻辑高度绑定，它们最终会决定 runtime 行为。

```python
Tool(
    name="initiate_return",
    schema=...,
    risk="medium",
    reversible=False,
    idempotent=True,
    requires_auth=True,
    requires_confirmation=True,
    timeout=10,
)
```

这里还会有一个关键概念 business invariants，比如不能退超过 30 天的商品，不能取消已发货订单等，这些东西不能让 LLM 判断，应该写成代码：

```
assert order.user_id == current_user.id
assert item.return_status == "eligible"
assert refund_amount <= payment.amount
```

这一层在 agent 系统里特别重要，它决定了 agent 可以犯认知错误，但不能突破业务边界。比如模型误以为一个商品能退，没关系，它调用 `initiate_return` 后，后端会返回 `RETURN_WINDOW_EXPIRED`，然后 agent 再解释给用户，这就是一个健康的 agent architecture。

当然随之而来的还有失败恢复，这部分更多的是后端工程，就不展开了。

还有一个特殊组件 escalation，客服 agent 必须知道什么时候别再 agent 了，比如用户强烈投诉、账户安全问题、疑似欺诈、退款 dispute，就 `handoff_to_human`，而且 handoff 的时候不能把客服重新丢回零上下文，应该自动生成类似于：

```
User issue:
- Order #123
- Headphones defective
- Return window expired by 3 days
- User requests exception
- Agent already checked standard return policy
```

然后把 execution history 一起交过去，这才是有用的人工转接。
