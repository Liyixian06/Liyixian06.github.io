---
title:       "操作系统笔记03：进程间通信"
subtitle:    ""
description: " "
date:        2023-10-30T23:04:16+08:00
author: LiYixian
image:       ""
tags:        ["CS", "operating system"]
categories:  ["Tech" ]
URL: "2023/10/operating-system-5.0/"
math: False
---

IPC (Inter Process Communication) 的同步问题 *e.g. 买面包*  
（这里只考虑单处理器，不考虑多核）  
临界区 critical section：空闲则入、忙则等待、有限等待、让权等待（optional）  

```
entry section
	critical section
exit section
	remainder section
```

Peterson, Dekkers 算法  

**lock 的问题在于检查 flag 和赋值之间的调度行为。**  
-> 保证调度不发生：把 flag 和赋值合并在一起（在一个调度周期内完成），使其不会被中断打断  
Test and Set Lock (TSL) solution - spinlock，如果锁被释放，TS 指令读取 value=0 并将值设为 1（锁被设置为忙并需要等待完成）；如果锁正忙，TS 指令读取 value=1 并将值设为 1（循环）  
这样无论有多少个线程，只有一个线程可以读到 value=0，然后继续执行  

-> 等待的线程还在一直 `while` 循环读取 value  
改进：如果读到 value=1，就把自己挂载在一个等待队列里，进入 sleep 状态，把运行权让渡给别人；释放锁时，把 sleep 的线程唤醒  
但类似于 lock 的问题，简单的 sleep-wake 在检测状态-决定休眠之间也可能发生调度  

final solution: semaphore by Dijkstra  
信号量由一个整形 sem 变量和两个原子操作 P/V 组成  
sem 的值为正时，表示有多少个可用资源；为负时，表示有多少个线程在等待  

```c
classSemaphore {
	int sem;
	WaitQueue q;
}
Semaphore::P() {
	sem--;
	if (sem < 0) {
        Add this thread t to q;
        block(p);
     }
}
Semaphore::V() {
    sem++; 
    if (sem <= 0) {
        Remove a thread t from q;
        wakeup(t);        
    }
}
```
与 TSL 的设计思路类似，信号量把状态检测、改变进程状态封装到了原子操作中，在这个过程中不会发生中断或调度  
V 操作可以选择要把哪个线程唤醒（通常假定这种调度是公平的，线程不会无限期阻塞在 P 中）  

信号量使用的两个规则：  
1. 临界区（竞争）：多个线程试图访问同一个资源  
	每个临界区设置一个信号量，初值为 1，每个线程进入临界区时调用 P，出来时调用 V  
2. 条件同步（同步）：多个线程之间需要实现先后顺序  
	如何保证无法感知彼此存在的线程能按照一定的顺序完成任务？  
	每个条件同步设置一个信号量，初值为 0，命令先执行任务的线程在任务完成后调用 V，后执行的线程在开始执行前调用 P  

对任何一个问题，首先考虑有多少个竞争问题，多少个同步问题  
*e.g.1. producer-consumer*   

- 1 个竞争：任何时刻只能有一个线程操作缓冲区
- 2 个同步：缓冲区空时，消费者必须等待生产者；缓冲区满时，生产者必须等待消费者  

```c
Class BoundedBuffer {
    mutex = new Semaphore(1);
    fullBuffers = new Semaphore(0);
    emptyBuffers = new Semaphore(n);
}
BoundedBuffer::Deposit(c) {
    emptyBuffers-%3EP(); 
    mutex->P(); 
    Add c to the buffer;
    mutex->V();
    fullBuffers->V();
}
BoundedBuffer::Remove(c) {
    fullBuffers-%3EP();
    mutex->P();
    Remove c from buffer;
    mutex->V();
    emptyBuffers->V();
}
```

信号量在实际编程时非常容易因为顺序问题引发错误  
-> solution: monitor 管程  
管程由一个锁和多个条件变量组成，面向对象的思路  
每个条件变量表示一种等待原因，对应一个等待队列；条件变量包含两个函数 wait/signal，类似信号量的 P/V  
wait 时传递一个 lock 变量，首先将线程挂载到条件变量对应的等待队列里，然后释放持有的锁，让渡运行权；再次获得调度机会时，把刚才释放掉的锁拿回来  
signal 从条件变量的等待队列里唤醒一个线程  

*e.g.2. dining philosophers*  
*e.g.3. reader-writer*  
*e.g.4. sleeping barber*  

为了解决并发/同步问题，操作系统提供了硬件支持：  
1. 禁用中断（用不了，不能把它交给普通用户）
2. 原子操作（如 TS 指令）
3. 原子 load/store

锁是一种消极的代码保护机制，为了保证正确性付出了最差情况下的代价  
改进：事务性内存（类似数据库，成功就写入，不成功就 rollback）  

test-and-set 是两个内存操作；在 risc 的指令设计中，一条指令最多只能有一个内存操作数  
实现：特殊寄存器 exclusive monitor，特殊指令 load-exclusive & store-conditional  

实际编程中更倾向于锁，而非信号量——为什么？  
信号量是操作系统实现的功能，每次需要调用的时候都要用 system call 进入内核态，代价非常高；  
而且 P/V 是消极的操作，即使只有一个线程、不存在竞争时也要做  
