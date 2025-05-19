---
layout: 	 single
title:       "编译原理笔记10：代码优化"
subtitle:    ""
description: " "
date:        2023-12-19T14:21:30+08:00
author: LiYixian
image:       ""
tags:        ["CS", "compiler"]
categories:  ["Tech" ]
URL: "2023/12/compiler-principles-ch10"
math: False
---

**Summary:**
- 优化种类
- 循环

优化编译器：控制流分析 -> 数据流分析 -> 代码变换  
与目的机器无关  

### 优化种类

局部优化（*i.e.* 基本块内优化）、全局优化

1. 消去公共子表达式  
2. 复制传播：对单次赋值 `f:=g`，在随后语句中用 `g` 替换 `f`  
![](/img/复制传播.png)

3. 无用代码删除
	- 没有被引用的值
	- 无法到达的基本块
	- 没有意义的计算（加 0、乘 1）
4. 循环优化
	1. 代码外提 code motion：表达式计算与循环次数无关时，提到循环入口前
		- `while(i<=limit-2) -> t = limit - 2; while(i<t)`
	2. 删除归纳变量 induction-variable elimination
	3. 强度削弱 strength reduction：同步改变的归纳变量  
	![](/img/强度削弱.png)
5. 常数传播、常数合并

### 循环

如果从流图的开始节点到节点 n 的所有路径都经过 d，称 d 支配 (dom) n  

循环的判定：  
- 唯一入口点 header 支配循环里所有节点
- 至少有一条路径返回 header
- 找到回边 back edge（被支配者指向支配者）
	- 自然循环 natural loop：有回边 n->d，它对应的自然循环即 d 及不经过 d 可到达 n 的节点集合，d 为 header  

*e.g.* 下图中 10->7 的自然循环：7、8、10

![](/img/自然循环.png)

两个循环如果 header 不同，则或者不相交、或者嵌套  
-> inner loop 内层循环：不包含其他循环的循环
