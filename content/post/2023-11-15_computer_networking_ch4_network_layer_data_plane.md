---
layout: 	 single
title:       "计算机网络笔记04A：网络层-数据平面"
subtitle:    ""
description: " "
date:        2023-11-15T21:20:51+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer networking"]
categories:  ["Tech" ]
URL: "2023/11/computer-networking-ch4/"
math: False
---

**Summary:**  
- 网络层概述
- 路由器工作原理
- 网际协议：IPv4、网络地址转换、IPv6

### 网络层概述

网络层的作用是将 packet 从发送主机移动到接收主机。  
1. 转发 forwarding，数据平面实现
2. 路由选择 routing，控制平面实现，确定 packet 从源到目的地的路径

每台路由器中有一个转发表 forwarding table，路由器检查到达的 packet header 的字段值，将其在转发表中索引，确定输出链路接口。  
转发表是如何配置的？  
1. 路由选择算法：每个路由器都有一个路由选择组件，可以互相通信
2. SDN (Software-Defined Networking)方法：远程控制器计算和向路由器分发转发表

网络服务模型 network service model  
确保交付、latency 上界、有序、最小带宽、安全性, etc  

### 路由器工作原理

![](/img/路由器体系结构.png)

路由器的 4 个组件：  
- 输入端口：执行物理层和链路层功能；查找转发表决定输出端口
- 交换结构
- 输出端口
- 路由选择处理器：执行路由选择协议、计算转发表，或（在 SDN 中）和远程控制器通信

1. 输入端口  
	路由器有 n 条链路，规定每个链路接口负责一个目的地址范围内所有 packet 的转发；路由器用 packet 目的地址前缀与表项进行匹配（多个匹配时使用最长前缀匹配规则），确定输出端口。  
	此后，还需要检查 packet 的版本号、检验和和 TTL，并且重写后两个字段；  
	最后，发送 packet 进入交换结构，如果其他输入端口的 packet 正在使用交换结构，可能就会出现阻塞-排队。  
2. 交换：经内存/总线/互联网络交换  
3. 排队  
	输入和输出端口都可能排队，队列增长到一定地步，路由器缓存用尽，无法存储到达的 packet，就会丢包  
	丢包和标记策略：主动队列管理 AQM 算法  
4. 分组调度：FCFS (FIFO) / priority queuing / 循环和加权公平排队  

### 网际协议：IPv4/IPv6

IPv4 数据报格式：

![](/img/IPv4数据报格式.png)

- 服务类型 TOS：使不同类型的 IP datagram 能分开，提供特定等级的服务
- 标识符、标志、分片偏移：和 IP 分片有关，IPv6 不允许在路由器上分片
- 协议：datagram 到达目的地后，数据部分应该交给哪个特定的运输层协议
#### 分片

一个链路层帧能承载的最大数据量 Maximum Transmission Unit (MTU) 限制了 IP datagram 的长度，但路径上每段链路可能有不同的链路层协议和不同 MTU  
solution：将 datagram 分成片 fragment，用单独的链路层帧封装后发送，到达目的地运输层前再在主机中重组  

- 同一个 datagram 的每个片有相同的标识号
- 最后一片的标志 bit=0，其他片的标志 bit=1
- 偏移字段指定该片应该放在 datagram 的哪个位置
#### IPv4 地址

一台主机只有一条链路连接到网络，路由器有多条链路，主机/路由器和链路之间有接口 interface  
**一个 IP 地址实际上和一个接口相关联，而不是和该接口的主机/路由器相关联。**  

IP 地址是 32 bit 的二进制数字，分为四个 8 bit 部分，由十进制书写  
每个接口都有唯一的 IP 地址，由其连接的子网决定  
IP 地址分为网络号 net-id 和主机号 host-id 部分，位于同一个物理网络、网络号相同的设备接口的网络形成一个子网 subnet  
*e.g.* 所有形如 223.1.1. xxx 的 IP 地址接口形成一个子网，其地址为 223.1.1.0/24  

![](/img/子网.png)  

其中 /24 称为子网掩码 network mask，指示 32bit 中最左侧 24bit 定义了子网地址，右侧 32-24=8bit 定义子网内部有 2^8 个地址。  
子网掩码写成 32 位地址：  

![](/img/子网掩码.png)

这样，要想找到某个 IP 地址的子网，要将其和路由表中所有的掩码做按位与运算，如果结果等于掩码对应的子网地址（网络号），它就属于这个子网。

子网是如何寻址的？  
无类地址划分 Classless Inter-Domain Routing：形如 a.b.c.d/x 的 IP 地址的 x 最高比特构成其网络号，也称作该地址的（网络）前缀 prefix  
一个组织通常会被分配前缀相同的地址，组织外部的路由器转发表仅考虑其前缀，内部路由器才会考虑剩余的 32-x bit  
分类编址 classful addressing：网络号被限制为 8/16/24 bit，称为 A/B/C 类网络  

另外，注意一些特殊的 IP 地址：  
![](/img/特殊IP地址.png)

一台设备（如主机）是如何获取一个 IP 地址的？  
1. 子网从 ISP 获取一组地址
2. 获取主机地址
	- 静态：申请固定 IP 地址，手动配置
	- 动态：动态主机配置协议 Dynamic Host Configuration (DHCP)
		- 主机每次和网络连接时，自动分配到一个 IP 地址
		- 主机还可以得到其他信息，如子网掩码、第一跳路由器地址（默认网关）、本地 DNS server 地址

DHCP 是一个 client-server 协议，client 即主机  
给 client 分配地址的 4 个步骤：  
1. DHCP discover：主机从标识本机地址向限制广播地址发送，即在本子网广播
2. DHCP offer：（可能是多个）DHCP server 广播响应，提供推荐的 IP 地址、子网掩码和 IP 地址有效时间
3. DHCP request：client 从多个 server 中选择一个，响应，回显配置参数
4. DHCP ACK

![](/img/DHCP分配IP地址.png)  
#### 网络地址转换

网络地址转换 Network Address Translation (NAT)：私有 IP 地址和公网 IP 地址的交互  
NAT 路由器类似具有单一 IP 地址的单一设备，使路由器对外界隐藏了家庭网络的细节，所有离开和进入家庭网络的 message 都有同一个源/目的 IP 地址。  

在内部借助端口号寻址：每次 NAT 路由器从内部主机向外转发时，都给它分配一个新的源端口号，将它的 IP 地址和转换前后的端口号填入 NAT 转换表的表项里；向内转发时，通过 NAT 转换表确定要转发给哪个内部主机  
*e.g.* 专用地址 10.0.0.1，源端口号 3345，路由器分配新的源端口号 5001，向外转发；向内转发时读到目的端口号 5001，查表得到专用地址和目的端口号 3345。  
#### IPv6 地址

IPv4 的地址空间要用尽了，因此开发了 IPv6  

![](/img/IPv6数据报格式.png)

改进：地址容量 32->128；简化 40-bits 基本 header；流标签，可以为一条 flow 中对某些 datagram 赋予优先权，或者对来自某些应用的赋予更高优先权  
一个基本 header、多个扩展 header (optional)  

IPv6 地址表示为 8 组 16 进制字段，每个字段 0000~FFFF  
-> 压缩：地址段中有时会出现连续的几组 0，可以用“::”代替，但一个地址中只能出现一次。 *e.g.FF01:0:0:0:0:0:0:101=FF01::101*  

### 通用转发和 SDN

传统路由器的转发仅基于 packet 的目的 IP 地址（匹配 + 动作）；而通用转发可以匹配 header 的多个字段，动作也不限于转发  

流表 flow table：匹配 + 动作转发表，表项包括 header 字段值集合、counter（匹配的 packet 数量）、采取的动作集合  

- 转发
- 负载均衡
- 重写 header（NAT）
- 阻挡或丢包（防火墙）
