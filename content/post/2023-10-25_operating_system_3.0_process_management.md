---
title:       "操作系统笔记01：进程管理"
subtitle:    ""
description: " "
date:        2023-10-25T20:24:32+08:00
author: LiYixian
image:       ""
tags:        ["CS", "operating system"]
categories:  ["Tech" ]
URL: "2023/10/operating-system-3.0/"
math: False
---

计算资源的共享共用：提交给 OS 的任务交替运行  
Cocurrent 并发 *VS* Parallel 并行  

两个问题：如何保存/恢复一个程序的执行过程？如何知道一个程序要触发“慢操作”？  
保存/恢复一个程序的执行过程：处理器的状态来自寄存器，程序的状态来自内存变量；后者不被破坏时，只要保存/恢复程序执行过程的全部寄存器（context）。  

什么是 process 进程？  

> Process is the procedure of program software running, it contains input, output, program and status.

程序运行过程中用到的数据、指令等 private 信息，和每个运行程序都需要保存的寄存器组及其他 public 信息，合并封装成一个 process。  
process model：cocurrent, scheduling, communication, memory protection and management  
user -> program & data -> process -> instruction sequence  
Process *VS* Program：前者是动态、暂时的  

### 进程的数据结构设计

进程控制块 Process Control Block (PCB, also named process descriptor) is maintained by OS kernel  
所有进程的 PCBs 存储在一块特定的内存区域 PCB table/list，不同状态的进程存在不同的 tables 里，table 大小决定了并发度  

程序触发“慢操作”（*e.g.用户输入*）时，避免处理器等待，进行进程切换/上下文切换：暂停当前运行进程（运行状态->其他状态），调度另一个进程从就绪状态->运行状态  
切换钱保存 context，切换后恢复 context  

如何知道一个程序触发了“慢操作”？  
捕获进入“慢操作”的状态，将这个时间窗口交给其他需要执行“快操作”的任务

### 进程管理

how to trap program execution：强制 developer 使用封装好的“慢操作”库  

-> 插叙：特权级  
ring 3: applications; ring 1&2: OS Services; ring 0: OS Kernel  （linux/uCore 只用 ring 0 and ring 3）  
避免用户攻击/修改操作系统，普通程序只有用户权限，需要进入特权态才能执行特权指令、访问特权数据等  
调用 `printf()` 时会触发系统切换到内核态，调用 `write()`  

process states  
basic: running, ready, blocked (waiting for external event)  
other: new, exit, suspend (running image swapped to hard disk)  
引入优先级，有高优先级等待（系统认为会很快 ready）的进程需要更多内存时，低优先级的 ready process 会被换到外存（进程挂起）  
suspend, activate  
挂起相关的新状态：blocked-suspend, ready-suspend  

总之，process 的设计目标：  
- 全部寄存器组成 context，通过保存/恢复 context，实现进程无感知切换；
- 通过封装“触发慢操作”的函数，并进行指令权限限定，让 process 感知到运行/等待状态的切换；
- 监控 hardware event，驱动 process state machine 的变化，对多个 process 正确分类和处理。

### 进程调度算法

调度程序：挑选 ready process 的内核函数  
问题：根据什么原则挑选 process（如何调度）？什么时候调度？  

调度时机：process 从 running 切换到 blocked；process 被终结了  
非抢占（当前 process 主动放弃 CPU 时）/可抢占（process 时间片用完；进程从 blocked 切换到 ready）  
-> 主动放弃：调用表示不再执行/需要长时间响应/其他系统认为可以打断的 API  
-> 抢占 CPU：利用任何 process 被打断的机会（中断/异常）  

调度目标是什么？  
- 每个 process 平等共享 CPU 资源
- policy enforcement
- balance: keep all parts of system busy

如何评估调度算法的好坏？  
- CPU 利用率
- 吞吐量：高吞吐和低延迟是冲突的
- 周转时间：process 从初始化到结束的总时间，包括等待
- 等待时间：process 在 ready 队列的总时间
- 响应时间：提交请求到产生响应

#### batch system  

无交互，计算机自动运行；最大化吞吐量、减少周转时间、CPU 利用率  

- first-come first-served (FCFS)
	- 平均等待时间波动较大（短 process 可能排在长 process 后面）
- shortest job first (SJF)
	- 有最优平均周转时间
	- 连续的短 process 可能导致长 process 无法获得 CPU
	- 需要预知未来：如何预估执行时间？
- shortest remaining time first
	- SJF 的可抢占改进
- Highest Response Ratio Next (HRRN)
	- response ratio = (waiting time + service time)/service time
	- 折中了 FCFS 和 SJF，照顾了短 process，长 process 也不会一直等待  
- three-level scheduling  

#### interactive system

与用户交互；响应时间、proportionality（用户期待）  

- Round-Robin 时间片轮转 (RR)
	- 时间片：分配资源的基本时间单元
	- 时间片结束时，按 FCFS 切换到下一个 ready process
	- 对每个 process，隔 n-1 个时间片执行一个时间片
	- 时间片过大，极限情况退化成 FCFS；过小，产生过多 context 切换开销；一般维持切换 context 开销 < 1%
- Multiple Queue (MQ)
	- 划分 ready 队列，每个队列有自己的调度策略（*e.g.前台 RR，后台 FCFS*）
	- 队列间调度：固定优先级/RR
- Multi-level Feedback Queue (MLFQ)
	- 动态改变 process 的优先级：I/O 密集型停留在高优先级，CPU 密集优先级下降很快
	- process 在当前时间片结束时没有完成，下降一个优先级
- Priority scheduling
	- 静态优先级（依据：process 类型、资源需求、用户要求）
	- 动态优先级

**Real-time system**  
在指定时间内完成任务；避免丢失数据、prodictability  
