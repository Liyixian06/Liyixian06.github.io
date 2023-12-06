---
title:       "编译原理笔记08：中间代码生成"
subtitle:    ""
description: " "
date:        2023-12-06T20:31:01+08:00
author: LiYixian
image:       ""
tags:        ["CS", "compiler"]
categories:  ["Tech" ]
URL: "2023/12/compiler-principles-ch8"
math: False
---

**Summary:**
- 三地址码
- 语句翻译：声明、赋值、布尔表达式、控制流
- BackPatching
### 三地址码

一般形式：`x:=y op z`（注意赋值符号是 `:=`）  
三地址码的实现：  
利用属性 `E.place` 保存值，`E.code` 计算 E 的三地址码  
newtemp 生成临时变量名，gen 输出一条三地址码指令  

- 四元组 `op, arg1, arg2, result`
	- `c=a+b -> +, a, b, c`
	- `x:=y -> :=,y,,x`
	- `goto label -> goto,,,label`
	- `if x rel y goto label -> rel,x,y,label`
- 三元组 `op, arg1, arg2`
	- 避免把临时变量也存入符号表
	- `arg1, arg2` 可以是其他三地址码的序号
	- `x[i] -> []=,x,i`

![](/img/三地址码.png)

间接三元组：使用一个间接码表记录运算顺序，便于代码优化  
-> 不必每次插入/删除/重排序代码都要重新计算下标  

![](/img/间接三元组.png)

### 语句翻译

*e.g.*  

![](/img/中间代码生成示例.png)
#### 声明语句

符号表栈处理作用域；  
为 record 类型创建独立的符号表
#### 赋值语句

在符号表中查找 identifier  

1. 临时名字的重用  

临时变量数 = 表达式中运算符数，而且临时变量保存的中间计算结果只用一次，空间占用过多  
如何重用临时变量保存不同的中间结果？  
-> 分析变量的生存周期（不同临时名字生存周期可能会嵌套，但不会交叉）  
用栈实现，子节点临时变量出栈、归还临时名字池；parent 从池中分配临时名字、压栈  

2. 数组元素寻址

起始地址 `base` + 下标 `i` \*数组元素大小 `w`  
*e.g.* `addr(A[i]) = base + i*w`  
-> k 维数组的寻址：寻 k 次  
假设按行存放，那么 `addr(A[i1][i2]...[ik]) = base + i1*w1 + i2*w2 + ... + ik*wk`

数组引用的翻译：文法和地址计算相关联  
核心是确定数组引用的地址  

3. 类型转换  

编译器要自动完成 widening & narrowing 的隐式转换  
#### 布尔表达式  

控制流语句：继承属性 true/false 分别代表表达式为真/假时跳转到的位置，根据上下文指向不同的地方  

短路求值，通过跳转指令实现控制流，逻辑运算符本身不出现  
*e.g.* `E1 or E2`，`E1=false` 才对 `E2` 求值  
-> 注意副作用问题：函数调用
#### 控制流语句

- if (-else)
- while
- switch-case
### BackPatching

生成跳转指令时，其跳转目标代码还没有生成 -> 跳转到哪里？  
backpatching：记录跳转指令的标号，但不生成跳转目标，将标号记录到综合属性 falselist 中；跳转目标代码生成完毕后，把 falselist 中所有指令的目标都填上这个值。  

break & continue 的代码与外围语句相关，需要知道 while 的条件和结束位置  
