---
title:       "编译原理笔记02：构造一个简单的编译器"
subtitle:    ""
description: " "
date:        2023-09-17T00:59:42+08:00
author: LiYixian
image:       ""
tags:        ["CS", "compiler"]
categories:  ["Tech" ]
URL: "/2023-09-17/compiler-principles-ch2/"
---

**Summary:**  

- 上下文无关文法（CFG）
	- 推导和语法树
- 语法制导翻译
	- 翻译模式
	- Yacc 编程
- 自顶向下预测分析
	- 设计实现预测分析器
- 简单词法分析
- 代码生成

### 语法定义

上下文无关文法（CFG）：描述源程序的语法结构  
CFG 的四个部分：  

- 终结符 terminal：不可被取代、不可拆分的基本符号（*e.g. **if, else***）  
- 非终结符 nonterminal（*e.g. expr, stmt*）
- 产生式 production 左部只有一个非终结符，右部是非终结符
- 唯一一个特定的非终结符：开始符号 start symbol

定义几个概念：  
- Σ：有穷字母表，其中元素（符号）构成符号串
	- 空字 ε：不含任何符号的序列
	- Σ*：符号串全体，包括空字
	- φ：空集{}，注意区分空集和空字
- 符号串子集的（笛卡尔）积，注意顺序
	- n 次积和 0 次积
	- 闭包 closure \\(V*\\) 和正则闭包 \\(V^+\\)  
- 终结符集合 \\(V_T\\)，非终结符集合 \\(V_N\\)，产生式集合 \\(P\\)，开始符号 \\(S\\)  

符号约定：  
- *expr, digit*  
- 终结符：数字、运算符、**黑体**
- 非终结符：*斜体*
- ｜= 或，候选式

#### 推导

推导 derivation：从 start symbol 开始，用 production 右部替换左部，反复替换得到最终的单词串  

语法分析树 parse tree：从根节点开始，每个节点应用 production 产生子节点  
- 叶节点从左到右构成树的输出 yield  
- 定义无歧义语法消除 ambiguity（同一个单词有多棵语法树）  
- 运算符结合律：左结合 +,-,\*,/；右结合 ^,=
- 运算符优先级
	- 结合优先级的表达式文法：expr, term, factor

### 语法制导翻译

确定每个语法结构如何翻译后，把翻译方法转换为语义规则/语义动作，附着在 production 上。  
或：一边解析 parse 字符串一边干别的事 *（构造语法树/直接生成中间代码/类型检查...）*，语法分析起支配作用  

*e.g.表达式 E 的后缀形式 Postfix (E)生成：*  
```
when E = E1 op E2:  
Postfix(E) = Postfix(E1 op E2) = Postfix(E1) Postfix(E2) op
```
#### 语法制导定义

syntax-directed definitions (SDD)：对 CFG 的推广  
- 每个文法符号关联一组属性  
- 每个 production 关联一组语义规则 semantic rule，这些规则用来计算该 production 中各个符号的属性值  

*e.g.后缀表达式的语法制导定义*  

![](/img/SDD_postfix.png)

文法符号的属性：  
1. 综合属性 synthesized attribute：节点综合属性由其子节点/自身属性决定，bottom-up 计算（后序遍历、深度优先）  
2. 继承属性 inherited attribute：节点属性由其父节点/自身/sibling 节点属性决定（终结符没有继承属性）

语法制导翻译的基本过程：  
1. 输入单词串，生成语法分析树
2. 节点 n 标记为 \\(X\\)，其属性为 \\(a\\)，写作 \\(X.a\\)
3. 利用 \\(X\\) production 的语义规则计算节点 n 的 \\(X.a\\) 的值
4. 注释语法分析树 annotated parse tree

#### 语法制导翻译模式

syntax-directed translation scheme (SDT)：在 production 中嵌入语义动作，计算文法符号的属性值  
语义动作在 production 中的位置就是在语法树中的位置，也就是动作执行的顺序  
考虑属性的依赖关系，确定嵌入位置。

```
rest -> + term {print('+')} rest
```
带语义动作的语法分析树：一边进行语法分析，一边从左至右执行语义动作  
或：后序遍历语法树，遍历到语义动作节点执行相应代码 *（属性计算/结果输出/...）*

#### Yacc 程序

yacc/bison 程序结构（\*. y，分三部分，\%\%分隔）  

```
/*P1: declarations 定义段*/
%{

/*
定义段一般分两种：
1. C语言编写的，包括头文件include、宏定义、全局变量定义、函数声明等  
2. 声明文法的终结符和非终结符  
常用的 Bison 标记声明有：%token %union %start %type %left %right %nonassoc 等。
- %token TOKEN1 TOKEN2 定义使用了哪些终结符
- %left % right %nonassoc 同上，表明了结合性，先定义的优先级低
*/

%}

%%

/*P2: grammar rules 规则段(rule & action)*/

A: a1 {语义动作1}
	|a2 {语义动作2}
	|...
	|an {语义动作n}
	|b //没有{...}时就使用缺省的语义动作
; //production 结束标记
// 语义动作一般在产生式右部分析完，归约动作进行前执行
// 动作中$1指右边第一个标记的值，$2表示右边第二个标记的值，依次类推；$$表示归约后的值(左边的值)

%%

/*P3: supporting C routines 用户辅助程序段(C函数)*/
// 为C代码，会被原样复制到C文件中，一般自定义一些函数

```

*e.g.简单表达式计算*  

### 语法分析

自顶向下 top-down：从 start symbol 开始，不断进行推导，直到推导所得的符号串与输入串相同为止。  

预备概念：LL (1) 文法是什么？  
第一个 L：left to right，从左向右扫描输入的 token 序列；  
第二个 L：leftmost derivation，分析时从文法最左边开始进行推导；  
(1)：只需要向右看一个符号就可以决定推导方向。  

**LL (1)是如何解析 token 序列的？**  
1. 用 parsing queue 的第一个元素和 input 的第一个 token 匹配；
2. 如果第一个元素是非终结符（可以继续迭代），就找到对应的 production 并替换，回到步骤 1，若找不到这样的 production，报错；
3. 如果第一个元素是终结符（无法继续迭代），则和 input 的第一个 token 匹配，二者都消去，回到步骤 1，若匹配不上，报错；
4. parsing queue 和 input 都为空时，匹配成功，结束。

预备工作：消除文法的二义性，消除左递归，提取左公共因子，计算 FIRST 集合和 FOLLOW 集合，判断文法是否为 LL (1)型文法；如果是，就可以用下面 LL (1)型文法的两个具体实现进行分析。  

一些额外问题：  
1. 如何消除左递归？  
改写文法  
```
A -> Aa|b 改写为  
A -> bR; R -> aR|ε
```
2. 如何判断文法是否是 LL (1)型？  
#### 递归下降分析

1. 对节点选择一个 production，利用右部构造子节点；继续选择下一个没有扩展的子节点，迭代
2. 扫描，与当前输入单词逐个比较，不匹配就回溯

#### 预测分析 predictive parsing

递归下降的问题：回溯花费的时间过多，可能会组合爆炸  
-> 如何在每步都确定唯一可能的候选式？  
根据下一个输入单词（超前单词）选择  

1. production 选择
	1. 对所有 production 构造 FIRST 集，和当前第一个 token 比对，有匹配就可以替换；
	2. 如果有冲突（FIRST 交集），则预测分析不适用；
	3. 若当前非终结符可以被替换为空（即存在 S->ε），且替换后 parsing queue 的下一个**终结符**（构造 FOLLOW 集）可以和当前第一个 token 匹配，就可以替换。
2. production 的使用
	1. 对非终结符，调用对应的递归函数；
	2. 对终结符，和当前第一个 token 比较，若匹配就继续读，否则报错。

问题：如何[构造 FIRST 集和 FOLLOW 集](https://blog.csdn.net/x1Nge/article/details/106139697)？  
A->a, A->b, FIRST (a) 和 FIRST (b) 不能有交集  
参考资料：[你知道LL(1)吗](https://zhuanlan.zhihu.com/p/122571100)

结合翻译模式：将语义动作复制到预测分析器里  
位置：语义动作位于语法符号 X 之后，就将其紧接在处理 X 的代码之后；如果位于 production 开始，就复制到函数最前面  

### 词法分析

语法分析是主体，词法分析器作为前者的调用接口，调用一次返回一个 token  
平凡算法：根据下一字符判断进入哪个 token 的识别  

- 去除空白和注释
- 常量
- 标识符、关键字识别
	- <id, 符号表项指针>
	- 关键字 keyword、保留字 reserved
	- 运算符，每个独自作为一类单词
#### 符号表

字典保存单词的实例和索引 token  

```
insert(s,t) 单词t的实例s（字符串）插入符号表，返回t
t 可以是 id 或关键字（if,else）
lookup(s) 查找字符串s对应的表中索引
```

一种实现方式：指针指向符号串存储的位置（紧凑存储）  
带符号表功能的词法分析器：先查询 lexbuf 是否已经在符号表里，没有再插入  

### 代码生成

语法符号的属性 - 汇编代码  
上层语法结构的代码 - 下层语法结构的代码，再拼接一些汇编指令  

```
expr -> expr1 + term {
	expr.addr = newtemp;
	expr.code = expr1.code || term.code ||
				"MOV EAX, expr1.addr
				MOV EBX, term.addr
				ADD EAX, EBX
				MOV expr.addr, EAX"
}

stmt -> id := expr 赋值
{stmt.code = expr.code ||
	"MOV EAX, expr.addr
	MOV id.addr, EAX"}

stmt -> if(expr) stmt1 { 控制流
	out = newlabel;
	stmt.code = expr.code || 'jz' out || stmt1.code || out
}

stmt -> while(expr) stmt1 {
	test = newlabel; out = newlabel;
	stmt.code := test || expr.code || 'jz' out ||
	stmt1.code || 'jmp' test || out
}

```

翻译模式：  

```
stmt -> if
	expr {out:=newlabel; print('jz', out);}
	then
	stmt1 {print(out);}

stmt -> while {test:=newlabel, print(test)}
	expr {out:=newlabel; print('jz', out);}
	then
	stmt1 {print('jmp', test); print(out);}

```
