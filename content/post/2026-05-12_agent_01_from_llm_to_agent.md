---
layout:		 single
title:       "Agent 01：从 LLM 到 Agent"
subtitle:    ""
description: " "
date:        2026-05-12T11:34:31+08:00
author: LiYixian
image:       ""
tags:        ["cs", "AI", "agent"]
categories:  ["Tech" ]
URL: "2026/05/agent-01/"
math: True
---

## Transformer

今天几乎所有主流大语言模型——GPT、Claude、Gemini、Qwen、DeepSeek——都建立在 Transformer 架构之上。理解 Transformer，本质上是在理解现代 AI 为什么能够出现。

在 Transformer 出现之前，自然语言处理领域的主流模型是 RNN 和 LSTM。它们按照时间顺序处理文本，一个词接一个词地读取句子。这种结构的问题很明显：无法高效并行计算，而且很难处理长距离依赖。比如一句很长的话，模型在读到结尾时，往往已经“忘了”开头的重要信息。

Transformer 的核心突破，在于它放弃了“顺序记忆”的思路，转而让每个词都能够直接关注句子中的其他词。这种机制叫 attention。2017 年 Google 发表论文《Attention Is All You Need》之后，整个 NLP 领域迅速转向 Transformer 架构，随后几年里，大模型时代真正开始形成。

很多人第一次接触 Transformer 时，会觉得它像一堆复杂公式和矩阵运算。但如果从整体结构去看，它其实可以这样概括：Transformer 是一个不断让 token 彼此交流、逐步更新内部语义表示，最终预测下一个 token 的系统。

整个流程大致如下：

文本  
→ tokenizer 切分  
→ token embedding  
→ 多层 attention 信息交互  
→ 多层 FFN 非线性加工  
→ 得到上下文化后的 hidden state  
→ 投影回词表空间得到 logits  
→ softmax  
→ 采样  
→ 输出下一个 token  

其中最关键的思想有两个：

第一，语言中的“意义”并不是固定的，而是依赖上下文动态变化的。

第二，模型不需要像人一样一步一步顺序阅读，而是可以让每个 token 同时关注其他 token，从而高效建立长距离关系。

Transformer 的革命性并不只是性能更好，而是它第一次提供了一种能够大规模学习语言结构、世界知识和推理模式的通用架构。后来的大模型能力，几乎都建立在这个基础之上。

### 从文本到 token

模型并不能直接理解文本。

对于人类来说，Cats chase mice 是一句自然语言。但对 Transformer 来说，它首先必须被转换成 token 序列，这个过程由 tokenizer 完成。

token 不一定等于单词。它可能是一个词、词的一部分、标点、空格。例如，unbelievable 可能被切成：

```text
["un", "believ", "able"]
```

中文也是一样，「人工智能」可能变成：

```text
["人工", "智能"]
```

或者：

```text
["人", "工", "智能"]
```

不同模型使用不同 tokenizer，因此 token 切分方式也会不同。

切分之后，每个 token 会被映射成一个整数 id：

```text
["Cats", " chase", " mice"]
↓
[4312, 9921, 18344]
```

到这里为止，还没有任何语义，模型只是把文本变成了数字。

#### Embedding

token id 本身没有意义，4312 和 18344 之间没有任何语义关系。因此，模型需要把 token 转换成向量，这个过程叫 embedding。

例如：

```text
4312
↓
[0.12, -0.88, 1.53, ...]
```

这个向量通常有几千维。GPT-3 的 hidden dimension 是 12288，现代模型往往更大。

embedding 的本质，是把词语映射到一个高维语义空间中；语义接近的词，在空间中通常也比较接近。例如：

* cat 接近 dog
* king 接近 queen
* python 接近 java

此处有著名的关系：

```text
king - man + woman ≈ queen
```

这意味着模型内部确实形成了某种语义几何结构。

不过，这时的 embedding 仍然是静态的，也就是说，“bank” 永远对应同一个向量。但现实语言里，一个词的含义高度依赖上下文，因此 Transformer 最核心的工作，是不断修改这些 embedding，使其逐渐融入上下文。

### Positional Encoding

attention 本身并不关心顺序。如果只看 attention，dog bites man 和 man bites dog 是一样的，因为它只看到 token 集合。所以 Transformer 必须额外加入位置信息。

最初 Transformer 使用的是 sinusoidal positional encoding，本质上是给不同位置生成不同周期的正弦波。现代 GPT 更常使用 RoPE（Rotary Position Embedding），它能更自然地表示相对位置关系，并更适合长上下文。

加入 position embedding 后：

```text
token embedding + position embedding
```

模型才真正知道谁在前，谁在后。

### Attention

#### Self-Attention

Transformer 最大的革命是 attention，它的本质是让每个 token 与其他 token 建立联系，并决定应该从谁那里获取信息。传统 RNN/LSTM 必须按顺序处理：

```text
I → love → AI
```

而 Transformer 可以让每个 token 同时关注所有 token，这就是 self-attention。

每个 token 会生成三个向量：

* Query（我想找什么）
* Key（我是什么信息）
* Value（我携带什么内容）

当模型处理某个 token 时，它会拿自己的 Query 去和其他 token 的 Key 做相似度计算。相似度越高，就说明它应该更多关注那个 token。

假设句子 Cats chase mice，模型现在处理 chase，它会拿 Q_chase 分别与 K_cats / K_chase / K_mice 计算相似度。

本质上是点积：
$$
score(Q,K)=QK^T
$$

如果 score(chase, mice) 更高，说明“chase” 应该更多关注 “mice”。

随后，attention 会通过 softmax 把这些分数转换成概率：

```text
cats: 0.3
mice: 0.7
```

最后用这些权重对 Value 做加权求和。

于是：

```text
new_chase =
0.3 * V_cats +
0.7 * V_mice
```

这意味着 “chase” 的表示已经吸收了上下文信息，它不再只是抽象的“追逐”，而是“猫追老鼠”里的追逐。

#### Contextual Embedding

这是 Transformer 最重要的思想之一。经过 attention 后，token embedding 不再固定，同一个词在不同上下文中会形成不同内部表示。

例如：I deposited money in the bank，这里 bank 会更多关注 deposited/money，于是它的表示会偏向“银行”。  
而 The boat reached the bank 这里，bank 会更多关注 boat/reached，于是它会偏向“河岸”。

这叫 contextual embedding。现代 LLM 的强大能力，很大程度上来自这种动态语义表示。

#### Multi-Head Attention

Transformer 并不会只做一次 attention，而是同时做很多组 attention。

假设 embedding 维度 d_model = 4096，如果只有一个 attention，所有关系都必须塞进一个 attention 空间，这会很拥挤。

于是 Transformer 把 embedding 投影到多个不同子空间，比如 32 个 head，每个 head 128 维，即 4096 = 32 × 128。

这里最关键的是，每个 head 有自己独立的参数矩阵。

head 1：\\(Q_1 = XW_1^Q\\)  
head 2：\\(Q_2 = XW_2^Q\\)

K/V 也一样。也就是说，同一个 token embedding，会被不同 head 用不同方式理解，这是核心。

不同 head 因为初始化不同，会慢慢走向不同 specialization（专门化），如专门学习主谓关系、代词指代、长距离依赖、代码括号匹配等。这些能力并不是人为设计的，而是在训练过程中，为了降低 loss 自发形成的。

最后，所有 head 的输出 concat（拼接）：

$$
MultiHead(Q,K,V)=Concat(head1,...,headh)W^O
$$
模型同时获得所有 head 学习到的专门知识，然后再经过 FFN，FFN 会进一步组合这些关系，形成更高层抽象。

不是所有的 head 都是有用的，很多 head 可以删掉，但某些关键 head 一删会使得性能暴跌。比如，一些 induction head 会学习前面出现过的模式，类似于 in-context learning（ICL）：

```text
Translate:

cat -> 猫
dog -> 狗
bird ->
```

模型会输出“鸟”，这里没有训练，模型只是从上下文里推断了当前任务模式，这可能是 Transformer 出现 few-shot learning 的基础。

#### Causal Mask

GPT 的任务是根据前面的 token，预测下一个 token，因此模型在预测时不能偷看未来。例如：

```text
I went to the ___
```

模型不能提前看到 store，所以 attention 会加入 causal mask，未来位置的 attention score 会被强制屏蔽，当前 token 只能看到左边。  
这也是 GPT 被称为 autoregressive model（自回归模型）的原因。

### FFN

attention 负责 token 之间的信息交流。但 attention 本身更像信息聚合，它负责“我该关注谁”，真正把这些信息加工成高级抽象的是 FFN（Feed Forward Network）。

假设一句话，The cat sat on the mat，经过 attention 后，“sat” 这个 token 已经拿到了cat 的信息、mat 的信息、句法关系、上下文关系。现在 “sat” 已经知道有一只猫坐在垫子上，但 attention 到这里为止，其实只是把相关信息搬了过来，而如何把这些信息组合成更高级概念，是 FFN 做的。

attention 像查资料，FFN 像大脑内部加工，这是理解 FFN 最重要的直觉。Transformer block 中，attention 负责 token 之间交流，FFN 负责每个 token 自己思考。

注意，FFN 是 independently applied 的，也就是说每个 token 单独过一遍同一个小神经网络。比如，当前 token embedding 是4096 维，FFN 会 4096→16384→4096，这本质上是：

Linear  
→ 激活函数  
→ Linear

比如，

$$
FFN(x)=W2σ(W1x+b1)+b2
$$

这里第一层把维度扩大，第二层再压回去。  
为什么要扩大？因为高维空间里更容易表达复杂特征组合。原始 embedding 可能编码了猫、坐、垫子，FFN 可能会在高维空间里激活动物行为、空间关系、动作完成、主谓结构等更抽象特征。

attention 本身其实很线性，如果没有 FFN，整个 Transformer 表达能力会弱很多。因为，attention 更像加权平均，而 FFN 提供非线性能力，没有非线性，深度网络能力会大幅下降。  
这和普通神经网络本质是一样的，线性层叠加线性层，最后还是线性。必须有激活函数 ReLU / GELU / SwiGLU，模型才能表达复杂函数。

所以，FFN 某种意义上是Transformer 的计算核心。

例如，The movie was surprisingly good，attention 会让 good 知道前面有 surprisingly，但 FFN 会进一步形成“超出预期的正面评价”这种抽象语义。

很多研究甚至认为大量知识其实储存在 FFN 中，attention 更像动态检索系统。Transformer 本质上特别像一个不断迭代 refinement 的系统，attention 不断交换信息，FFN 不断重写内部表示，最后整个 hidden state 逐渐收敛成足够预测下一个 token 的状态。

### Residual 与 LayerNorm

Transformer 往往有几十甚至上百层，如果每层都完全覆盖前一层表示，训练会非常不稳定。因此，Transformer 使用 Residual Connection，形式是 \\(x_{new}=x_{old}+f(x)\\)，也就是说，模型不会“重写”表示，而是逐步修正，这非常像不断 refinement（精炼）。

这个思想非常重要，因为 LLM 推理很多时候不是一步完成，而是语义状态不断迭代收敛。这也是为什么更深的模型通常更聪明，因为它有更多轮“内部思考”，虽然这种“思考”不是人类意义上的。

与此同时，LayerNorm 会对数值进行归一化，避免梯度爆炸或消失。

这些结构虽然不像 attention 那样耀眼，但对大模型训练至关重要。

### 多层堆叠

一个 Transformer block 包括：

Attention  
→ Residual  
→ Norm  
→ FFN  
→ Residual  
→ Norm

然后不断重复。  
随着层数增加，token 的内部表示越来越抽象。通常会出现这样的趋势：

* 低层：词法、句法
* 中层：语义关系
* 高层：推理状态、任务目标

最终，token 不再只是单词，而是当前整个上下文状态的高维表示。

### 输出层

经过所有 Transformer layers 后，模型会得到最后一个 token 的 hidden state。例如，Cats chase mice 的最后一个 token 已经不是单纯的 mice 词义了，而是已经融合了整个句子的语义信息。  
（我们通常只关心最后一个位置，因为前面的预测已经知道了，这也是为什么训练时是并行的，生成时是串行的）

接下来，模型需要回答：后面最可能出现什么 token？

此处，模型需要给词表里每个 token 打一个分，hidden state 需要从语义空间投影回词表空间。因此，假如 hidden state 的维度 4096，即 \\(h_{mice}∈R^{4096}\\)，就会有一个巨大的矩阵：

$$
W_{vocab}\in\mathbb{R}^{4096\times 128000}
$$

可以把它理解成每个 token 在语义空间中的方向，矩阵里的每一列对应一个 token 的输出向量。然后，hidden state 会和这些列向量做点积，本质上是在问，当前语义状态与哪个 token 最匹配。

此处有一个工程细节：很多 GPT 模型的输入 embedding matrix 和输出 projection matrix 是共享的，叫 weight tying，也就是说，token 的输入语义空间和输出语义空间是同一个空间。  
这其实很优雅，因为输入时：token → 语义向量，输出时：语义向量 → token，像一个编码/解码过程。可以把整个 GPT 想成：

token  
→ 进入语义空间  
→ 在 Transformer 里不断变换  
→ 再投影回 token 空间

整个过程本质上都是高维向量空间里的几何运算。

hidden state 和这个投影矩阵相乘之后的计算结果叫 logits，是 128000 个数，可以理解为每个 token 的原始分数：

```text
cheese: 8.2
quickly: 1.3
banana: -5.7
```

随后 softmax 会把 logits 转成概率：

```text
cheese: 70%  
quickly: 20%  
banana: 0.00001%
```

模型再从中采样一个 token，这就是 next-token prediction。

在 softmax 之前，有一个参数 temperature，即 \\(P(x_i)=softmax(zi/T)\\) 中的 T，它是用来控制输出结果的稳定性的，默认 T=1 时不做任何改变，原始分布直接 softmax，更低的 temperature 更保守，更高的 temperature 更发散。  
比如“The weather is \_\_\_”，temperature=0 时几乎固定会选择 nice，temperature=1.5 时可能会选择 melancholic / chaotic / radioactive，因为它会更愿意采样低概率 token。一般来说，会限制 temperature 不高于 2，为了防止模型输出跑得太偏。

## LLM 的能力边界

LLM 是一个很好的单步推理机，但现实中几乎所有有价值的任务都是多步骤、有状态、需要与外部世界交互的。Agent 的出现，是在解决 LLM 本身能力边界的问题，也就是如何让模型真正完成复杂任务。

LLM 所做的是在文本空间里生成最合理的 continuation，它天然存在几个巨大的限制：

- 知识是静态的：LLM 的训练数据有截止，Agent 通过 RAG 和实时搜索让知识变成动态实时的。
- 推理无法变成行动：LLM 无法直接和外部世界交互，知道怎么写代码和代码跑起来之间有一道墙，工具调用打通了这道墙，也就是让模型输出结构化 JSON action，外部系统再执行。
- 任务需要迭代：LLM 擅长短链推理，但对于复杂任务，人类自己也要做很多轮尝试-观察-调整，Agent 的 Agentic Loop 就是把这个循环自动化。
- 没有长期记忆：LLM 不能真的记住东西，于是 memory 系统开始出现，上下文窗口是工作记忆，向量数据库是长期记忆，两者配合让 Agent 能跨会话积累状态。
- 缺乏稳定性：LLM 是一个概率生成器，让它去控制确定性系统是很危险的，于是产生了 verifier 等约束机制。

理论上说，Agent 是在把 LLM 外部化：Transformer 本身只有上下文和 token 生成，Agent 所做的事情是把长期记忆、工具、行动、搜索、规划等全部外挂到模型外面，于是 LLM 开始像 CPU，而 Agent 更接近于操作系统。

> 很多工程手段都是为了补齐模型能力的短板而存在的。比如说之前模型输入窗口比较小，工具调用比较笨，所以衍生出了多 Agent 架构来搞定复杂任务，但是随着模型能力的提升和上下文窗口的扩展，多 Agent 的弊端又反而成为了阻碍，主流又开始往单 Agent 转向。后续模型或许会吃掉越来越多的工程动作，当然在当下很长一段时间内，能否把工程做出差异化仍然是非常重要的事情。

## Agent 的缺陷与未来

目前 Agent 的发展还远远没有成熟，可以把目前受到的限制和相对应的发展方向分成几个层面：

- 模型层面
	- LLM 不稳定，导致错误级联（error compounding）。虽然其单次的幻觉概率可能只有 5%，但经过 20 步 Agentic Loop 后，累积失败概率可能高达 65%，每一步的小错都可能在后续步骤被放大。
		- 当前的一个流行方向是 self-reflection，让模型能识别自己的中间结果是否合理，在失败时主动回退，但自己 critique 自己也经常有虚假修正、甚至自我强化 hallucination 的问题。
	- 缺乏真实世界模型：语言世界毕竟不是现实世界，LLM 的空间感、时间感、对现实约束的理解都比较弱，没有真正的 environment grounding。
		- Anthropic、OpenAI 等在探索让 Agent 直接操控计算机界面（鼠标、键盘、截图），突破只能调用 API 的限制，例如 Browser Agent、Computer Use。
	- 长期 consistency 很难，因为 LLM 没有真正的 persistent cognition，其长期记忆还是外挂的检索系统，它每一步其实都在重新根据上下文生成。
- 工程层面
	- 工程成本和延迟：一个自主 Agent 完成一个任务可能需要调用 LLM 十几到几十次，加上工具调用的网络延迟，总耗时和费用是单次推理的数十倍。
	- 可观测性差，Agent 在做什么、为什么做这个决定、哪一步出错了，目前都很难追踪和调试，这是工程落地最大的障碍之一。
	- 安全问题比单纯的 LLM 严重得多，当 Agent 有权限执行代码、操作文件、调用 API 时，提示词注入攻击变得非常危险，恶意内容可以伪装成工具返回结果，诱导 Agent 做出有害操作。
		- 当前最务实的安全策略是人在环路（Human-in-the-loop），不是让 Agent 完全自主，而是在关键节点主动暂停、请求人类确认。
- 任务设计
	- 很多 Agent 项目失败不是因为模型不够好或工程不够稳定，而是任务本身就不适合 Agent，比如需要精确数值计算、强一致性事务、或者任务边界本身就定义不清；知道什么任务适合 Agent 和知道 Agent 怎么工作同样重要。

真正的 Autonomous Agent 其实还不存在，现在绝大多数 Agent 更偏向于 Human-supervised workflow systems，真正 autonomous 的长期目标、自主纠错、自主学习、环境建模、长期规划等，现在都还很弱。尽管如此，Agent 第一次让 AI 从回答问题变成了执行任务，虽然尚不稳定，但潜力是毋庸置疑的。
