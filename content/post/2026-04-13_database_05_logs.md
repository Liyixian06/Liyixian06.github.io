---
layout:		 single
title:       "数据库笔记05：日志"
subtitle:    ""
description: " "
date:        2026-04-13T11:42:31+08:00
author: LiYixian
image:       ""
tags:        ["cs", "database"]
categories:  ["Tech" ]
URL: "2026/04/database-05/"
math: False
---

**Summary:**

- binlog 与 redo log 的区别与作用
- undo log 的作用
- 两阶段提交（2PC）保证 binlog 与 redo log 一致性

### 基础概念

数据库里的日志，是一系列按顺序追加写入的记录，记录的是某个事务对数据做了什么操作，比如某条记录从 A=10 改成 A=20，或者某个事务开始、提交、回滚。这些记录通常不会去改写已有内容，而是一直往后追加。

为什么要有日志？

- 磁盘太慢，内存不可靠
- 崩溃恢复
	- 假如数据库突然断电，有的事务已经提交了但还没写磁盘，有的事务执行到一半还没提交；此时为了事务的持久性和原子性，要用 redo log 和 undo log 重做和回滚事务
- 提升写磁盘的性能
	- 日志写磁盘时的顺序 IO 是很快的，修改先写到日志再慢慢刷盘的话，后者就可以合并和优化
- 复制和数据同步
	- binlog 是把操作记录下来发给从库让它再执行一次，实现数据同步

### Redo Log

数据库真正工作的地方是在内存的缓冲池（buffer poll）里，每次修改数据都直接写磁盘，那性能会非常差（随机 IO，很慢），所以数据库会先在内存里修改数据，再定期由后台线程刷新磁盘；但如果机器宕机，内存的修改就会丢失，因此需要有一种机制在真正写磁盘之前，先记录修改。

这就引入一个核心原则 WAL（Write-Ahead Logging），先写日志，再写磁盘。  
注意，此处的「写日志」也分成两个阶段：先写到 redo buffer，再根据策略刷到磁盘 redo log file。

redo log 记录的不是 SQL 语句或逻辑操作，而是物理层面的修改，比如，某个数据页（page 1234）的某个偏移位置（offset 88）改成了什么值（从 10 改到 20）, 这就是为什么它恢复特别快，可以直接在物理层面重放。

磁盘里的 redo log 不是无限增长的，它是由一个 file group 组成的环形结构（circular log）。数据库维护两个关键指针：

- write pos：当前 log 写到哪里了（持续往前写 log buffer → file）
- checkpoint：已经安全刷盘的位置

数据库定期把内存里的脏页刷到磁盘，然后告知 redo log 哪些记录可以被擦除；擦除后 checkpoint 向后移动，就有了新的能写入日志的空间。  
在 crash recovery 中，数据库重启时先找到 checkpoint，从此处开始扫描 redo log，把还没刷盘的全都重放一遍，恢复出崩溃前的最后状态。（注意，这里只负责重做已经提交的事务，未提交的靠 undo log 回滚）  
-> redo log 文件要是满了，write pos 追上了 checkpoint，MySQL 就必须阻塞直到上述步骤执行完，有新的写入空间才能继续运行，因此对并发量大的系统，redo log 文件大小设置很重要

那么，redo log buffer 什么时候写磁盘？  
InnoDB 有个关键参数 `innodb_flush_log_at_trx_commit`，它有三种取值：

- 1（最安全，默认）：每次事务提交都直接将 redo log buffer 写磁盘，数据不会丢失
- 2：事务提交时写到 OS cache，不立刻刷盘，后台线程每隔 1 秒调用 fsync 刷盘
	- 也比较安全，因为 MySQL 进程崩溃时不会丢数据，只有 OS 崩溃/系统断电时，才可能丢失上一秒全部事务数据
- 0：每 1 秒写一次盘，MySQL 进程崩溃时会丢失上一秒全部事务数据

越到下面性能越高、越不安全，因此如何选择参数是安全性和写入性能的 tradeoff。

总体而言，数据库修改数据时，流程如下：

- 如果数据页不在 buffer pool 里，从磁盘加载数据到 buffer pool
- 修改 buffer pool 里的页
- 写 redo log buffer
- 返回成功
- 异步刷盘

### Undo Log

undo log 是 InnoDB 用来记录“修改前数据”的逻辑日志，主要用于事务回滚和 MVCC。

undo log 是在修改之前生成的，也就是先把旧值（插入时记录主键，删除时记录整行，更新时记录旧值）写入 undo log，再修改数据页、生成 redo log、提交事务。  
之前 [MVCC](https://liyixian06.github.io/2026/03/database-03/#mvcc-%E7%9A%84%E5%AE%9E%E7%8E%B0%E6%9C%BA%E5%88%B6) 中提到了 undo log 串成的版本链以及它如何和 ReadView 配合实现 MVCC，这里不再赘述。

注意：undo log 不像 redo log，它没有独立的一组 log 文件，而是作为特殊的数据结构也存在于 InnoDB 的表空间里；因此，和普通数据一样，对 undo log 的修改也会写入 redo log，它所在的数据页在 buffer pool 里，和正常的数据页一起刷盘。

另外，undo log 不会无限增长，但它的回收比较复杂。因为 undo log 可能还在被 MVCC 使用，如果还有事务在读旧版本，那这些 undo log 就不能删。  
因此，有一个后台机制叫 purge，只有当所有「可能用到这个版本的事务」都结束后，undo log 才会被清理。其执行原理是：如果一个 undo log 对应的版本，其事务 ID 小于「当前所有活跃事务中最小的那个」，那它就不可能再被任何人读到了。  
这也是为什么长事务很危险，如果有一个很老的事务一直不结束，它的 trx\_id 很小，会导致大量 undo log 堆积，甚至影响性能。

### Binlog

binlog 是 MySQL Server 层的日志，记录的是发生了什么操作，主要用于主从复制和数据恢复。

binlog 不参与崩溃恢复，它主要做两件事：

- 主从复制  
	- 主库把 binlog 发给从库，从库按顺序再执行一遍，从而达到数据同步
- 数据恢复（时间点恢复）  
	- binlog 保存的是全量的日志，即所有数据变更的情况，而 redo log 只记录了没有刷盘的数据的物理日志
	- 比如误删了一张表，可以用全量备份恢复，再把备份之后的 binlog 重放到某个时间点，这叫 point-in-time recovery

binlog 和 redo log 最大的区别是，binlog 是逻辑日志，不是物理日志；它记录的是操作或结果，而不是页的物理变化。比如，对同一个 update：

- redo log：page 123 offset 88 改成 20
- binlog：`update user set age = 20 where id = 1`

binlog 有三种格式：

- Statement
	- 记录 SQL 语句本身
	- 日志小
	- 但有些动态函数的结果不一定一致，比如 `now(), rand()`
- Row
	- 记录每一行的变化（before/after）
	- 虽然能恢复得绝对一致，但是 binlog 文件会过大
- Mixed
	- MySQL 自动在 statement 和 row 之间切换，一般用 statement，有风险用 row

事务执行过程中，每个线程先把日志写到自己的 binlog cache 里，提交时再把 binlog cache 写到同一个 OS cache 的 binlog 文件中（此时还没有刷盘）。  
MySQL 提供一个参数 `sync_binlog` 控制 binlog 文件的刷盘频率：

- 0（默认）：每次提交只写 binlog 不刷盘，由 OS 自己决定何时刷盘
	- 性能最好、最不安全，一旦主机宕机，还没有刷盘的 binlog 都会丢失
- 1：每次提交写完 binlog 都立刻刷盘
- N：每次提交都写 binlog，累积 N 个事务后刷盘（一般是 100-1000 个）

#### binlog 和 redo log 的区别？

- 层级
	- binlog 是 MySQL 的 Server 层的日志，所有存储引擎都可以使用
	- redo log 是 InnoDB 实现的日志
- 内容格式
	- binlog 有上面三种格式，statement / row / mixed
	- redo log 是物理日志
- 用途
	- binlog 用于主从复制、备份恢复
	- redo log 用于故障恢复
- 写入方式
	- binlog 追加写，保存全量日志
	- redo log 循环写，用完可以覆盖

#### 有了 binlog 为什么还需要 redo log？

- binlog 是 server 层的日志，无法记录有什么脏页没有刷盘，redo log 是存储引擎层的日志，可以记录，这样崩溃恢复的时候就能恢复那些还没有刷盘的脏页；
- binlog 有些语句的执行结果未必和原本的一致，比如 now，redo log 是精确的

### 两阶段提交（2PC）

redo log 和 binlog 是如何一起工作的？  
虽然在事务提交后，二者都要持久化到磁盘，但是 redo log 在 InnoDB，影响主库的数据；binlog 在 Server 层，影响从库的数据。因此，它们在刷盘时如果不做协调，就有可能出现两种情况：

- redo log 写了，binlog 没写
	- 主库恢复正常，但从库少数据（不一致）
- binlog 写了，redo log 没写
	- 从库有数据，主库 crash 后丢数据

为了避免这种主从数据不一致的问题，引入了两阶段提交（2PC）的概念。这是分布式事务一致性协议，可以保证二者要么都成功，要么都失败。

两阶段提交把单个事务的提交拆分成 2 个阶段，分别是 prepare 和 commit，使用 MySQL 的内部 XA 事务来共享一个统一标识 XID：

- 事务执行完，进入提交状态
	- MySQL 会生成一个 XID（transaction ID for binlog）
- 写 redo log（prepare 状态）
	- 把 XID 写进 redo log 记录里
- 写 binlog
	- 把同一个 XID 写进 binlog 事件中
- 把 redo log 标记为 commit（commit 状态）

> Q：为什么是 binlog 决定提交，而不是 redo log？  
> A：因为 binlog 是要发给从库的，它代表对外可见的提交结果；只要 binlog 写了，这个事务必须算成功，否则主从就不一致。

数据库 crash 重启后，会这样判断事务状态：

- 扫描 redo log  
- 找到所有处于 prepare 状态的事务  
- 对每一个这样的事务，拿出它的 XID  
- 去 binlog 里查，是否存在这个 XID 对应的完整事务记录
	- 如果有，说明事务已经对外提交，执行 commit（redo）
	- 没有，说明事务还没完成，回滚（undo）

两阶段提交的问题在于磁盘 IO 很高（如果前面的两个参数都设为 1，每个事务提交都得刷两次盘），为此，MySQL 引入了 binlog 组提交（group commit）机制，有多个事务提交的时候，在 commit 阶段一起写 binlog 文件，合并一次刷盘。

group commit 有两个参数：`binlog_group_commit_sync_delay` 和 `group_commit_sync_no_delay`，前者表示 binlog 刷盘的间隔，后者表示有多少个事务一起写 binlog 的时候就立刻刷盘。
