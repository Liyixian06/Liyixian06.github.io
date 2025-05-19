---
layout: 	 single
title:       "计算机体系结构笔记01：Performance"
subtitle:    ""
description: "  "
date:        2023-08-28T15:36:54+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer architecture"]
categories:  ["Tech" ]
URL: "2023/08/computer-architecture-ch1/"
math: true
---

### Metrics

- latency (execution time)：执行一项固定任务的时间
- throughput (bandwidth)：单位时间执行的任务
  - 利用并行增加 throughput, not latency
  - 二者通常是冲突的

### CPU Performance

performance 计算公式：  

- latency = seconds/program = 下列三者的乘积：
  - inst/program 指令数
  - cycles/inst (CPI) 主要研究的是这个 (caches, parallelism)
  - seconds/cycle (clock period)

IPC = 1/CPI  
直观（越大越好），所以比较常用  
CPI 计算：\\(CPI=\sum\limits_{inst} frequencies*costs\\)  
CPI = (CPU time\*clock frequency)/dynamic inst count  
CPI breakdown (CPU, mem, etc.) 比较有用，可以知道性能问题出现在哪里  
frequency 作为衡量性能的 metrics，1 Ghz = 1 cycle/nenosecond  

**注意：性能指标不能孤立看待。**

### Comparing Performance

- speedup of A over B
- A is x% faster than B
- 注意 increase 和 decrease 的百分比不一样（分母不一样）

*e.g.* A runs for 200 cycles, B runs for 350 cycles  
% increase = (350-200)/200 = 75%  
% decrease = (350-200)/350 = 42.3%  

mean (average) performance：区分算术平均、调和平均  
-> add latencies, but not throughputs  
*throughputs 本来就是一个平均分布程度的指标（类似于速度），要衡量总体平均分布程度不能单纯相加（分母不同），必须把分母调成平均值。*  

### Benchmarks

performance 什么也不是，必须和 workload（我们关心什么样的任务）相联系  
benchmark 是 standard workloads，代表实际运行的程序  

### Performance Laws

1. Amdahl's Law：提升系统一个部分的性能对整个系统有多大影响  

$$
\frac{1}{(1-P)+\frac{P}{S}}
$$

P = 优化部分所占的比例  
S = speedup  

Amdahl's Law for Parallelization  
P = 并行部分的比例，S->N = threads  

2. Little's Law：适用于任何非抢占的 queuing system  

$$
L=\lambda W
$$

L = 系统中的物体数量  
\\(\lambda\\) = 平均到达时间（假定平均到达时间=平均离开时间）  
W = 平均等待时间  

描述了如何满足性能要求，*i.e.* 高 throughput（\\(\lambda\\)）需要低 latency (small W) / 并行的 service requests (large L)  
以及其他计算机性能问题：cache miss, network requests, etc.
