---
layout: 	 single
title:       "计算机体系结构09：Virtual Memory"
subtitle:    ""
description: " "
date:        2023-11-13T22:38:33+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer architecture"]
categories:  ["Tech" ]
URL: "2023/11/computer-architecture-ch9/"
math: False
---

### Computer System

![](/img/computer_system.png)

- CPUs and memories  
	- connected by memory bus
- I/O peripherals: storage, input, display, network...  
	- Connected by system bus (which is connected to memory bus)
- Operating System
	- abstraction：给计算机硬件资源提供软件接口 (*e.g.* threads, files, etc.)，简化 application 编程
	- isolation：虚拟化，给每个 process private CPU/memory/IO（用到的不是整个计算机，看到的是整个计算机）  
		> To virtualize a resource is to make a finite amount of a resource act like a very large/infinite amount.  
		
		- 可以虚拟化处理器 (multitasking, context switch)/DRAM（虚拟内存）/整台计算机和 OS（虚拟机）  
### Virtual Memory

不同进程和 OS 共享内存；目标是**让所有的 application 都以为自己使用的是全部内存**  

solution: 
- 把 memory 当作 cache 处理，overflowed blocks 放在硬盘上的 swap space  
- 增加一层 indirection (address translation)  

上层看到的是整个地址空间，下层 OS 将其翻译成真正的物理地址  
logically: translation performed **before** every inst fetch/load/store  
physically: hardware acceleration removes translation overhead  

以 page 为单位使用，unmapped VAs 放在硬盘上  
inter-process communication: 将一些物理页 map 到多个虚拟地址空间  
-> 更详细的实现细节见 [操作系统笔记：Memory Management](https://liyixian06.github.io/2023/10/operating-system-4.0/)  

![](/img/virtual_memory.png)

如果试图 execute data/write read-only data/read unmapped data -> segmentation fault  
#### TLB

TLB 放在 CPU 中，缓存近期访问的页表项；做 addr translation 时首先检查 TLB，miss 时才去看页表  

cache 是用物理地址编址的：  
- 如果用虚拟地址编址，在 context switch 时就必须全 flush 掉
- 可以在 cache 处实现 inter-process communication

TLB 从定义上就是 virtual 的（用 VA indexed and tagged）  
- context switch 时必须 flush，上一个进程的 mapping 对下一个进程无意义  
- 或者在 x 86 中 extend 了一个 process identifier

因为 cache 是 PA 编址，还增加了至少一个 cycle 用来做 addr translation  
-> parallel TLB & cache access  
因为 cache access 分两步：index 找到组、tag 比对，而前者可以和 translation 并行执行  
在 translation 之前就可以拿到 index 找到所在的 cache 组，**与此同时**进行 VA->PA 转换；转换完成后，根据得到的 tag 在组里比对。  
前提是 VPN 和 index 不能 overlap -> (cache size) / (associativity) ≤ page size  
-> index bits 实际上限制的是 cache capacity；但可以增加 associativity 弥补  

![](/img/parallel_TLB_cache_access.png)

在 organization 上 TLB 类似 cache：  
- capacity, associativity
	- 至少要 cover 掉 cache 中的所有数据
- block size：一个物理页对应几个相连的虚拟页

TLB miss 时，需要去看页表：  
基于硬件（比较流行）：页表 root 在 hardware register 里，直接 stall pipeline 去查找（类似 data hazard），不需要 OS call  
基于软件：TLB miss 就发送中断给 OS，后者执行中断程序，flush pipeline，更新 TLB  

bref. 访问一个虚拟地址的流程如下：  

![](/img/访问虚拟地址的流程.png)
