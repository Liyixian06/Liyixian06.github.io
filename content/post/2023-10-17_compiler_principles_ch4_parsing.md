---
title:       "编译原理笔记04：语法分析"
subtitle:    ""
description: " "
date:        2023-10-24T16:26:29+08:00
author: LiYixian
image:       ""
tags:        ["CS", "compiler"]
categories:  ["Tech" ]
URL: "2023/10/compiler-principles-ch4"
math: True
---

**Summary**：

- 上下文无关文法
- 语法分析
	- 自顶向下
	- 自底向上
- 语法分析器生成

## 上下文无关文法

正则表达式的能力不足 -> [ch2 CFG](https://liyixian06.github.io/2023/09/compiler-principles-ch2/)

凡是正则表达式能表示的语言，都能用 CFG 表示：可以机械地由 NFA 变换而得，NFA 字母表视为 terminal 集合  

推导：最左推导（每次替换最左边的 non-terminal）、最右推导（规范推导）  
写出分析树 parse tree  
二义性：不止一种最左/右推导  

句型 sentential form、句子 sentence、语言

### 消除二义性 eliminating ambiguity  

不存在一个算法，能在有限步骤内确切地判定任给的一个 CFG 是否为二义性文法；二义性的消除也没有规律可循，但是可以总结出一些较为通用的手段。

1. 改写为非二义文法
- 划分优先级和结合性
	- 引入一个新的 non-terminal，增加一个子结构并提高一级优先级（优先级的判断）；
	- 递归 non-terminal 在 terminal 左边，运算具有左结合性，否则具有右结合性。

*e.g. E → E+E|E\*E|(E)|-E|id*  
- 优先级从低到高：[+], [\*], [(),-, id]
- 结合性：左结合 [+,\*]，右结合[-]，无结合[id]
- non-terminal 与运算：
	- `E:+` E production 左递归
	- `T:*` T production 左递归
	- `F:(),-,id` F production 右递归
```
E -> E+T | T
T -> E*F | F
F -> (F) | -F | id
```
*e.g. dangling else 问题：then 的个数多于 else，后者不知道和哪个 then 结合*  
就近匹配，规定 else 和最近的 then 匹配（右结合）  

缺点：引入更多 non-terminal 使得 parse tree 更深、更难理解  

2. 为文法符号规定优先级和结合性
yacc 采用的就是这种方式：  
```
%left '+''*'
%right '-'
```

3. 修改语言的语法（表现形式被改变）
- 明确给出结束标志
- 给表达式加括号

## 语言和文法

词法分析和语法分析的分离  
1. 正规语法是 CFG 的特例
2. 用正则表达式定义词法的若干好处（简单、简洁、高效）
3. 软件工程上的好处（模块、可移植）

CFG 的表达能力还是不足 -> 非上下文无关文法  

## 语法分析

### 自顶向下

#### 预处理：消除左递归、提取左因子

左递归 left recursion：存在 non-terminal \\(A\\) s.t. \\(A\rightarrow^{+}A\alpha\\)，其中 \\(\alpha\\) 是文法符号串  
top-down 分析无法处理左递归，会陷入无限循环  
左递归分为两种：直接、间接  
1. 直接左递归 immediate left recursion  
文法中存在 \\(A\rightarrow A\alpha|\beta\\)，其中文法符号串 \\(\beta\\) 不以 \\(A\\) 开头  
消除：写成 \\(A\rightarrow \beta A', A'\rightarrow\alpha A'|\epsilon\\)   
2. 间接左递归  
形如 \\(S\rightarrow Aa|b, A\rightarrow Sd|\epsilon\\)   
先变换成直接左递归 \\(S\rightarrow Aa|b, A\rightarrow Aad|bd|\epsilon\\)   
再消除左递归 \\(S\rightarrow Aa|b, A\rightarrow bdA'|A', A'\rightarrow adA'|\epsilon\\)   

提取左因子 left factoring：\\(A\rightarrow\alpha\beta_{1}|\alpha\beta_{2}\\)，不知道用哪个来替换  
提取最长公共前缀 \\(A\rightarrow\alpha A', A'\rightarrow\beta_{1}|\beta_{2}\\)  
*e.g. hanging else*

#### LL (1) 文法和递归下降的预测分析

L-left to right; L-leftmost derivation  
LL (1) 文法的性质：不是二义的、没有左公共因子、不含左递归  

通过向前看一个符号确定 production，消除回溯。  
*e.g.* 当前句型是 xAb，输入是 xa…，那么要选择 production \\(A\rightarrow\alpha\\) 的必要条件是：  
- \\(\alpha\rightarrow a\dots\\)
- \\(\alpha\rightarrow\epsilon\\)，且 \\(\beta\\) 以 a 开头，即在某个句型中 a 跟在 A 之后  

定义函数：

1. \\(FIRST(\alpha)\\)
- 定义：\\(\alpha\\) 推出的非空串中首 terminal、以及 \\(\alpha\\) 推出空串时的 \\(\epsilon\\) 组成的集合（只能包含终结符和 \\(\epsilon\\)）
	- 形式化定义： \\(FIRST(\alpha)=\\{\alpha|\alpha\rightarrow*\alpha\dots,\alpha\in V_{T}\\}\cup\\{\epsilon|\alpha\rightarrow*\epsilon\\}\\)
- 意义：下一个输入符号 a，若 \\(a\in FIRST(\alpha)\\)，选择 production \\(A\rightarrow\alpha\\)
- 计算方法：
	-  X 是 terminal，\\(FIRST(X)=\{X\}\\)
	- X 是 non-terminal，且 \\(X\rightarrow Y_{1}Y_{2}\dots Y_{k}\\)
		- 如果 \\(\alpha\in FIRST(Y_{i})\\) ，且 \\(\epsilon\\) 在 \\(FIRST (Y_{1}),\dots,FIRST(Y_{i-1})\\) 中，则加入 \\(\alpha\\) 
		- 如果 \\(\epsilon\\) 在 \\(FIRST (Y_{1}),\dots,FIRST(Y_{k})\\) 中，则加入 \\(\epsilon\\)
	- X 是 non-terminal，且 \\(X\rightarrow\epsilon\\)，则加入 \\(\epsilon\\)

2. \\(FOLLOW(A)\\)
- 定义：**可能**在某些句型中紧跟在 A 右边的终结符的集合
	- 形式化定义：\\(FOLLOW(A)=\\{\alpha|S\rightarrow*\dots A\alpha\dots,\alpha\in V_{T}\\}\cup\\{S\rightarrow*\dots A\\}\\)
- 意义：下一个输入符号 b， \\(A\rightarrow\alpha\\) 且 \\(\alpha\rightarrow\epsilon\\) 时，若 \\(b\in FOLLOW(A)\\)，可以选择 \\(A\rightarrow\alpha\\)
- 计算方法：
	- 将右端结束标记 $ 加入 \\(FOLLOW(S)\\)
	- 按下述两个规则迭代，直到所有的 \\(FOLLOW\\) 集合都不再增长：
		- 若 \\(A\rightarrow\alpha B\beta\\)，则将 \\(FIRST(\beta)\\) 中所有非 \\(\epsilon\\) 的 terminal 加入 \\(FOLLOW(B)\\)
		- 若 \\(A\rightarrow\alpha B\\) 或（\\(A\rightarrow\alpha B\beta\\) 且 \\(\epsilon\in FIRST(\beta)\\)），则将 \\(FOLLOW(A)\\) 中所有符号都加入 \\(FOLLOW(B)\\)

LL (1) 文法的定义：任何两个 production \\(A\rightarrow\alpha|\beta\\) 都满足下列条件：  
1. \\(FIRST (\alpha)\cap FIRST (\beta)=\emptyset\\)
2. 若 \\(\beta\rightarrow*\epsilon\\) ，则 \\(FIRST (\alpha)\cap FOLLOW (A)=\emptyset\\)；反之亦然  

#### 非递归的预测分析表

列是 non-terminal，行是 terminal 或结束标记 $，每个格子 \\(M[A,a]\\) 是 non-terminal->terminal 的 production \\(A\rightarrow\alpha\\)（即当前输入是 a 时，采用该 production）  

对每个 production \\(A\rightarrow\alpha\\)：  
- 对 \\(FIRST(\alpha)\\) 中的每个 terminal a，将 \\(A\rightarrow\alpha\\) 加入 \\(M[A,a]\\) 中
- 如果 \\(\epsilon\\) 在 \\(FIRST(\alpha)\\)，则对于 \\(FOLLOW(A)\\) 中的每个符号 b，将 \\(A\rightarrow\alpha\\) 也加入 \\(M[A,b]\\) 中
- 其他没有定义的条目都是 error  

采用一个符号栈保存分析时的处理过程：  
- 初始化，栈中仅包含开始符号 S
- 如果 top 元素是 terminal，和输入匹配
- 如果 top 是 non-terminal，使用预测分析表选择 production，在栈顶用右部替换左部，将右部按**倒序** push 入栈

分析表驱动的预测分析器的模型如：  

![](/img/分析表驱动的预测分析器模型.png)

*e.g.* 输入：id+id\*id  

![](/img/预测分析表例子01.png)
![](/img/预测分析表例子02.png)

什么时候报错？  
- 栈顶的 terminal 和下一个输入符号不匹配；
- 栈顶是 non-terminal A，输入符号 a，而 \\(M[A,a]\\) 为空。  

错误恢复：采用 panic mode，抛弃输入记号，直到其属于某个指定的同步记号 synchronizing tokens 集合为止。

总而言之，自顶向下语法分析的步骤大概如：  

> 1. 消除文法的二义性
> 2. 消除左递归，提取左公共因子
> 3. 计算 FIRST 集和 FOLLOW 集
> 4. 进行分析（递归下降/预测分析表）

### 自底向上

bottom-up 的移入-规约 shift-reduce 分析：从串 w 开始规约到开始符号 S  
reduction 步骤：一个与 production 右部匹配的子串替换为左部符号  
是最右推导的逆过程，比 top-down 方法更一般化  

问题：什么时候规约（规约哪些字符串）？规约到哪个 non-terminal？  

把输入**从左到右**扫描，反向构造出一个最右推导。  
句柄 handle：最右句型中和某个 production 匹配的子串，对它的规约代表了该最右句型的最右推导的最后一步。  
即：若 \\(S\rightarrow\alpha A\omega\rightarrow\alpha\beta\omega\\)，那么紧跟在 \\(\alpha\\) 之后的 \\(\beta\\) 是 \\(A\rightarrow\beta\\) 的一个 handle  
在最右句型中，handle 右边仅含 terminal（尚未处理的输入串）  
*e.g.输入 id\*id*  

![](/img/规约例子.png)

#### 移入-规约

也采用一个栈保存规约/扫描移入的符号：  
- 栈中符号从底向上和待扫描的符号组成一个最右句型
- 开始：栈中只包含 $，输入为 \\(\omega\\$\\)
- 结束：栈中为 S$，输入为 $
- 分析过程中不断移入符号，并在识别到 handle 时进行规约
	- handle 被识别时总在栈顶

分析动作：  
- 移入 shift：将下一个输入符号移入栈顶
- 规约 reduce：弹出 handle，规约为相应的 non-terminal，入栈
- 接受 accept：分析成功完成
- 报错 error

*e.g.*  

![](/img/移入-规约parser处理例子.png)

移入-规约冲突：即使知道了栈中所有内容，以及接下来 k 个输入符号，仍然不知道是该移入还是规约/该按照哪个 production 规约  
栈顶形成不同的 handle，或 handle 是不止一个 production 的右部  

如何快速识别栈顶是否形成 handle？引入状态。
#### LR 语法分析

LR (k)：L-left to right; R-rightmost derivation in reverse; k 最多向前看 k 个符号  
只考虑 k<=1 的情况  
最通用的无回溯移入-规约分析技术  

**基本思想：** 用状态刻画栈中内容，每个状态都对应一个文法符号（初始状态 \\(s_{0}\\) 除外），根据栈顶状态判断是否形成 handle  
将符号写作状态的意义是？  
通过类似于有限状态机的输入-动作（移入/规约）机制，进行语法分析。  

构建 LR 语法分析表，两个部分：  
- 动作 ACTION：两个参数状态 \\(s_{m}\\) 和 terminal \\(a_{i}\\)，\\(ACTION[s_{m},a_{i}]\\) 表示在该状态下面对输入符号 \\(a_{i}\\) 应该采取的动作。
	- 移入 \\(s\\)：执行移入动作，将输入 \\(a_{i}\\) 对应的状态 \\(s\\) 入栈
	- 规约 \\(A\rightarrow\beta\\)：将栈顶的 \\(\beta\\) 规约为 A，弹出 \\(r=\mid\beta\mid\\) 个状态，压入状态 \\(s=GOTO[s_{m-r},A]\\)
	- 接受、报错
- 转向 GOTO：两个参数状态  \\(s_{m}\\) 和 non-terminal A，\\(GOTO[s_{m},A]\\) 表示在该状态下当前栈顶 handle 规约为 A 后应该转向哪个状态。

LR 语法分析器的结构 configuration 包括栈中内容 \\(s_{0}s_{1}\dots s_{m}\\) 和余下输入 \\(a_{i}a_{i+1}\dots a_{n}\\$\\)，语法分析器查询条目 \\(ACTION[s_{m},a_{i}]\\) （栈顶状态，第一个输入符号）确定下一步动作。

*e.g.* 

![](/img/LR分析表例子.png)  
注：表中 \\(s_{i}\\) 表示移入，\\(r_{j}\\) 表示按第 j 号 production 规约，acc 表示接受。  

![](/img/LR分析过程例子.png)  

对处理过程的说明：  

移入如 4-5 步，栈内状态\[0 2\]，符号 T，输入 \*id+id\$，那么：  
- 查询 \\(ACTION[2,*]=s_{7}\\)
- 压入状态 7  

规约如 2-3 步，栈内状态\[0 5\]，符号 id，输入 \*id+id\$，那么：  
1. 查询 \\(ACTION[5,*]=r_{6}\\) 规约
2. 按 \\(r_{6}\\) 执行规约 \\(F\rightarrow id\\)：
	- 将 id 规约为 F
	- 弹出 1 个状态 5
	- 查询 \\(GOTO[0,F]=3\\)  
	- 压入状态 3

如何构造 LR 分析表？  
#### LR 分析表

活前缀 viable prefix：不超过最右 handle 右端的前缀  

> viable: something that is viable is capable of doing what it is intended to do.

形式化定义：规范句型 \\(\gamma\beta\omega\\)，\\(\beta\\) 为 handle，\\(\gamma\beta\\) 的任何前缀（包括 \\(\epsilon\\) 和其自身）都是活前缀，\\(\omega\\) 仅包含 terminal，即输入缓冲区中剩下的符号串  
在 LR 语法分析中，活前缀就是从栈底到栈顶的所有文法符号连接形成的串。  

LR 分析表的转移函数 GOTO 本质上是识别活前缀的 DFA。  
在 LR (1) 方法中，要看到 production 右部推出的整个 terminal 串，才会确定用这个 production 规约。  

## 语法分析器 parser/syntax analyzer 自动生成
