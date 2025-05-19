---
layout: 	 single
title:       "编译原理笔记06：类型检查"
subtitle:    ""
description: " "
date:        2023-11-21T14:51:19+08:00
author: LiYixian
image:       ""
tags:        ["CS", "compiler"]
categories:  ["Tech" ]
URL: "2023/11/compiler-principles-ch6"
math: False
---

**Summary**:  
- 类型系统
- 类型表达式的等价

静态检查 static checking：  
1. 类型检查（type check）
	- 操作对象必须与操作符匹配，*i.e.* 函数名不能相加
2. 控制流检查（flow-of-control check）
	- break 必须退出 while、for、switch…
3. 唯一性检查（uniqueness check）
	- 对象（变量、标号…）定义必须唯一
4. 名字关联检查（name-related check）
	- 相同名字在不同位置

### 类型系统

将类型赋予语法结构的规则；每个表达式都有一个关联的类型  
基本类型（语言内部支持类型）、结构类型（组合基本类型构成新类型）

type expression 类型表达式，表示语言结构的类型  
- 基本类型
- 类型名
- 类型构造符
	- 数组：`int A[10] -> array({0,...,9}, integer)`
	- 笛卡尔积
	- 记录（和笛卡尔积的区别是记录的域有名字）：`record((address×integer) × (lexeme×array({0, …, 15}, char)))`
	- 指针：`row* p -> pointer(row)`
	- 函数（定义域类型到值域类型的映射）：`int* f(char a, char b) -> (char x char)->pointer(integer)`

类型表达式可以保存在树里，判定类型是否等价时比较两棵树 -> 效率不高  

类型检查：表达式、语句、函数
### 类型表达式的等价

1. 结构等价  
	- 类型表达式的图表示是否相同
		- 基本类型、子表达式的类型构造符相同
	- 编码类型表达式：用二进制码表示类型和构造符
		- 基本类型编码 + 构造符编码前缀
		- 不同类型可能表示为相同的二进制串（数组界限、函数参数）
2. 名字等价
	- 不展开，名字不相同类型就不同
		- *i.e.* type link = \*cell，但 link 和 \*cell 类型不同
	- 回路问题：结构体不用结构等价，避免在“struct 内部有 struct 类型指针成员”时树中出现回路
