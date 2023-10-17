---
title:       "编译原理笔记04：语法分析"
subtitle:    ""
description: " "
date:        2023-10-17T16:26:29+08:00
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

## 语法分析器 parser/syntax analyzer 自动生成
