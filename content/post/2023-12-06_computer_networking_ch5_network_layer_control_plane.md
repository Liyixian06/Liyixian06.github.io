---
title:       "计算机网络笔记04B：网络层-控制平面"
subtitle:    ""
description: " "
date:        2023-12-06T22:36:25+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer networking"]
categories:  ["Tech" ]
URL: "2023/12/computer-networking-ch5/"
math: True
---

**Summary:**  
- 路由选择算法
	- 链路状态算法
	- 距离向量算法
- 互联网路由选择协议
	- RIP
	- OSPF
	- BGP
- 软件定义网络 SDN
- ICMP 互联网控制报文协议

### 路由选择算法

路由选择算法 routing algorithm：从发送方到接收方确定一条通过路由器网络的最好路径  
-> 最好：一般指开销最小 *（距离、时沿、费用、堵塞）*  
分布式：每台路由器独立计算  

形式化描述路由选择问题：图 \\(G=(N,E)\\)  
点 = 路由器，边 = 物理链路，权值 = 开销 \\(c(x_{i},x_{j})\\)（不相邻时记作 \\(\infty\\)）  
路径的开销即所有边的开销总和，即 \\(cost (x_{1}, x_{2},\dots, x_{p}) = \sum\limits_{i=1}^{p-1}c(x_{i},x_{i+1})\\)  
- 集中式路由选择算法（链路状态 Link State 算法）：完整的网络知识
- 分散式路由选择算法（距离向量 Distance-Vector 算法）：每个节点只知道其邻居的开销，通过迭代计算、与相邻节点交换信息，逐渐计算出最低开销路径

#### 链路状态算法

Dijkstra 算法，计算从某个节点到所有其他节点的最低开销路径，经过 k 次迭代可以算出到 k 个目的节点的路径  
符号定义：
- N：最低开销路径已知的节点集合
- D (k)：到节点 k 的**当前**路径开销
- p (k)：到节点 k 的路径中 k 的前继节点
```
Initialization:
N = {u}
for all nodes k
	if k is a neighbor of u
		then D(k) = c(u,k)
	else D(k) = inf

Loop:
find m not in N such that D(m) is a minimum
N.insert(m)
update D(k) for all k that's a neighbor of m and not in N:
	D(k) = min(D(k), D(m)+c(m,k))
until all nodes in N
```
算法终止时，对每个节点，都知道从当前节点到它的最低开销路径的前继节点，由此可以构建出到所有目的节点的完整路径，从而构建转发表。  
时间复杂度：\\(O(n^{2})\\)（一共需要搜寻 \\(n(n+1)/2\\) 个节点），用堆实现可以达到 \\(O(nlogn)\\)  

#### 距离向量算法

Bellman-Ford 方程：  
$$
d_{x}(y) = min(c(x,m)+d_{m}(y))
$$
也就是，从 x 到 y 的最低开销依赖于 x 的所有邻居 m 到 y 的最低开销。  
符号定义：
- \\(D_{x}(y)\\)：从 x 到 y 路径最低开销值
- 节点 x 只知道到它邻居的开销 \\(c(x,m)\\)
- 节点 x 维护自己的距离向量 \\(D_{x}=[D_{x}(y): y\in N]\\)
- 节点 x 维护它每个邻居的距离向量 \\(D_{m}=[D_{m}(y):y\in N]\\)

接收邻居的更新后，自己更新；自己更新后，发送给邻居  
```
Initialization:
for all destinations y in N:
	D_x(y) = c(x,y)  // if y is not a neighbor then c(x,y)=inf
for each neighbor m:
	D_m(y) = inf for all destinations y in N
	send distance vector D_x = [D_x(y): y in N] to m

Loop:
wait (until I see a link cost change to some neighbor m; OR until I receive a distance vector from some neighbor m)
for each y in N:
	D_x(y) = min_m {c(x,m)+D_m(y)}
if D_x(y) changed for any destination y:
	send distance vector D_x = [D_x(y): y in N] to all neighbors
forever
```
节点可以检测到链路开销的变化  
无穷计数问题：链路开销增加的坏消息传播得很慢  
-> 毒性逆转 poisoned reverse：如果 z-->y-->x，z 就告诉 y，它（z）到 x 的距离是无穷大，即向 y 通告 \\(D_{z}(x)=\infty\\)  

### 互联网路由选择协议

路由器规模极大，存储的路由选择信息占空间极多，计算复杂性也极高，几乎不可收敛；每个 ISP 都有自己的路由器网络，应当自治地管理  
-> 将路由器组织进自治系统 Autonomous System (AS)，在一个 AS 内运行的路由选择算法叫自治系统内部路由选择协议/内部网关协议 IGP。  

层次化路由：AS 内路由/AS 间路由  
网关路由器/边界路由器 gateway router 既执行 AS 内路由，也执行 AS 间路由  

#### RIP

AS 内路由，使用距离向量算法，距离度量采用跳步数  
-> 跳步数定义：直接相连=1

![](/img/RIP例子.png)

- 相邻路由器每隔 30 s 发送 ack message
- 如果发现链路失效/有变，立刻发送 ack message
- 超时没有收到邻居通告，则认为链路失效

#### OSPF

AS 内路由，使用链路状态算法，每台路由器确定以自身为 root 到所有子网的最短路径树  

- 几个基本概念：邻居、邻接关系、链路状态通告 LSA、链路状态数据库 LSDB（记录收到的 LSA）  
- 三张表：邻居列表、LSDB、路由表

OSPF 的工作流程：  
1. hello message 发现邻居
2. 邻接路由器之间通过 LSU 洪泛 LSA，最终所有路由器同步，LSDB 完全相同
3. 每台路由器独立计算最优路由，写入路由表

OSPF 可以层次化地配置多个区域，其中有一个是主干区域 backbone，包含所有区域边界路由器，为其他区域之间提供路由选择。  

#### BGP

唯一的 AS 间路由，所有 AS 运行相同的 BGP，将因特网中的 ISP 粘合起来。  
BGP 可以让路由器：  
1. eBGP：从相邻的 AS 获得前缀的可达性信息；
2. iBGP：将可达性信息传给 AS 内的其他路由；
3. 基于可达性信息和策略，确定到该前缀的最好路由。

其中，路由器使用策略决定接受/拒绝收到的通告，也决定是否向其他相邻 AS 发送通告。  

一台路由器可能会接收到多条到目的网络的路径；如何选择？  
路由器通过 BGP 连接通告前缀时，update message 会包括一些 BGP 属性  
- NEXT-HOP：下一跳路由器的 IP 地址
- AS-PATH：通告已经通过的 AS 列表

bref. 路由器设置路由表项时，首先由 BGP 得到（通过网关路由器）到达目的网络的路径，然后从 AS 间路由（OSPF/RIP）得到到达网关路由器的路径。  

### 软件定义网络 SDN

1. 基于 flow 的转发，将数据平面抽象为通用的转发模型，可以基于传输/网络/链路层 header 中任意数量的字段值，而不限于 IP 地址
2. 控制平面和数据平面分离，二者只需要遵循一定的开放接口即可通信，前者负责决策控制，后者负责数据转发
3. 网络行为用编程语言实现，通过 controller 的 API 控制全局设备

OpenFlow 协议运行在 SDN controller 和交换机/其他实现 OpenFlow API 的设备之间，TCP 之上  
SDN 基本架构：  

![](/img/SDN基本架构.png)

flow table -> 通用转发，定义了交换机的匹配规则（匹配 header 的多个字段，不限于目的 IP 地址）和动作（不限于转发，可以拦截、重写 header、负载均衡等）  
可以实现路由器、交换机、防火墙、NAT 等的功能  

![](/img/SDN_flow_table.png)

*e.g.*  

![](/img/SDN_flow_table例子.png)

### ICMP

因特网控制报文协议 ICMP，被主机和路由器用来沟通网络层的信息，如差错报告  
ICMP message 有一个类型字段和一个编码字段，*e.g.* Ping 命令/目的网络不可达/路由发现/TTL 超期等
