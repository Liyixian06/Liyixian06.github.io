---
layout: 	 single
title:       "计算机网络笔记01：计算机网络和因特网"
subtitle:    ""
description: "计算机网络的概述"
date:        2023-09-06T18:52:07+08:00
author: LiYixian
image:       ""
tags:        ["CS","computer networking"]
categories:  ["Tech" ]
URL: "/2023/09/computer-networking-ch1/"
---
*本文是《计算机网络：自顶向下方法》（Computer Networking: A Top-Down Approach）的阅读笔记，不成文，仅记录。*

**Summary：**  
- 构成网络的基本硬件和软件
- 边缘：网络中运行的主机和网络应用
- 核心：接入网、链路和交换机
- 分组交换的时延、丢包、吞吐
- 体系结构原则
- 攻击和安全

### 什么是因特网？
#### 因特网的硬件和软件组件

主机/端系统通过通信链路和分组交换机连接到一起；不同链路的传输速率不同  
发送数据时将数据分段并加上首部字节，形成信息包 packet  
分组交换机：路由器、链路层交换机 link-layer switch  
主机通过因特网服务提供商 ISP 接入因特网，每个 ISP 是多台分组交换机和多段通信链路组成的网络；ISP 互联，每个都独立管理  
主机、分组交换机和其他因特网部件运行协议 protocol，控制信息接收和发送：TCP 传输控制协议/IP 网际协议  

#### 因特网服务

分布式应用程序 distributed application 运行在主机上，涉及多个相互交换数据的主机  
主机提供了套接字接口 socket interface，规定主机之间交换数据的方式（因特网服务）  

#### 网络协议 protocol

协议：通信时一系列约定俗成的动作（语法、语义、时序）  
对等性，相同层次必须执行相同协议  

### 网络边缘与核心

主机：客户 client 和服务器 server *（存储、发布 Web 页面、流视频、中继 email）*  

#### 接入网 access network

将主机连接到边缘路由器（主机到任何其他远端主机的路径上的第一台路由器）  
有线接入（光纤宽带、以太网 Ethernet）、无线接入（WiFi、移动通信 4G/5G）

#### 分组交换

主机之间传输 message 时将其分为较小的数据块，称之为分组 packet；每个 packet 都通过通信链路和分组交换机传输  
分组转发率 PPS：以 packet 为单位的转发率 packet/秒  
存储转发传输 store-and-forward transmission：交换机必须先接收整个 packet 才能开始输出，存在存储转发时延  
每台分组交换机有多条链路，对每条链路都有一个 output buffer/queue 存储准备发送的 packet，因此存在等待的时延 queuing delay  
buffer 是有限的，如果满了就会出现丢包  

为什么要用 packet？  
可以降低 latency，避免某条链路/路由器缓存被一条 message 长时间占用  

![packet降低latency](/img/packet_latency.png)

路由器如何决定向哪条链路转发？  
每个主机都有 IP 地址，传输 packet 时包含了目的地的 IP 地址；IP 地址有等级结构，路由器会检查地址，并通过自带的转发表 forwarding table 将其映射为输出链路，将 packet 导向它  
转发表的设置是通过因特网的路由选择协议 routing protocol 决定的  

#### 电路交换

电路交换网络中，在主机通信期间会预留通信所需的资源（带宽、缓存），传送数据的速率是恒定的  
频分多路复用 FDM/时分多路复用 TDM/统计多路复用（带宽按需共享）  

#### 二者的对比

分组交换不适合实时服务（视频会议等），因为端到端的 latency 不可预测（主要是因为排队），会产生抖动 jitter  
电路交换在 silent period 专用电路空闲，空闲的网络资源（频段/时隙）不能被其他连接使用，会被浪费  
网络流量有很强的突发性（不平稳），不同流的峰值出现在不同时间；流越多，网络平均流量越平滑  
总体而言，分组交换的性能优于电路交换，因为每个用户的活跃时间都很短  

#### 网络的网络

主机经过接入 ISP 与因特网相连；同时，ISP 自身必须互联  
tier 3：金字塔形态的网络的网络：全球传输 ISP - 区域 ISP - 接入 ISP，每一层都要向其连接的上一层付费  
tier 4：增加存在点 Point of Presence、多宿 multi-home（任何 ISP 可以与多个提供商 ISP 连接）、对等 peer（ISP 不向同一层的其他 ISP 付费）、因特网交换点 IXP（多个对等 ISP 的汇合点）  
tier 5：增加提供商网络 content provider network（如 Google），经过专用的 TCP/IP 网络互联，专用网络仅承载出入其服务器的流量；直接与较低层 ISP 连接，减少向顶层 ISP 的付费，控制服务器如何交付给主机  

### 分组交换网中的时延、丢包、吞吐

#### 时延

- 节点处理时延 proc  
检查 packet 首部，决定将它导向哪条链路  
对路由器的最大吞吐量有重要影响
- 排队时延 queue  
packet 在链路上等待传输，取决于前面等待的 packet 数量；是流量的强度和性质的函数  
- 传输时延 trans  
packet 长度为 L bit，链路传输速率为 R bit/s，则传输时延是 L/R  
- 传播时延 prop  
传播时延等于两台路由器之间的距离 d/传播速率 s，速率取决于链路的物理媒体  

#### 排队时延和丢包

排队时延取决于流量到达队列的速率、链路传输速率、到达流量的性质（周期性/突发）  
流量强度 traffic intensity（La/R）不能大于 1  
丢包可能基于端到端的原则重传  

#### 端到端吞吐量

吞吐量是服务器和客户之间瓶颈链路 bottleneck link 的传输速率，限制因素通常是接入网  
也取决于干扰流量  

### 协议层次及其服务模型

分层 layer 的特点：  
1. 对上面层次提供服务 service，使用下面层次的服务（下层被包装了，只提供接口）
2. 某层的实现方式变化时，系统其余部分不受影响

第 n 层协议的不同部分分布于网络组件的各个部分中  
协议栈 protocol stack：物理层、链路层、网络层、运输层、应用层，自顶向下处理  

1. 应用层  
网络应用程序及其应用层协议  
应用层协议分布在多个主机上，其信息分组就是 message  
2. 运输层  
在应用程序端点之间传送应用层的 message  
两种运输协议 TCP/UDP  
TCP 面向连接的服务：流量控制、划分、拥塞控制  
运输层分组称为报文段 segment  
3. 网络层（IP 层）  
将网络层分组数据报 datagram 在主机之间移动  
运输层协议向网络层递交运输层 segment 和目的地址  
网际协议 IP 定义 datagram 的字段  
路由选择协议  
4. 链路层  
网络层将 datagram 下传给链路层，链路层沿路径将其传递给下一个节点，然后在那里将 datagram 上传给网络层  
一个 datagram 可能被不同链路的不同链路层协议处理  
链路层分组称为帧 frame  
5. 物理层
将 frame 中的一个个 bit 在节点间移动  
协议与链路的实际传输媒体相关  

TCP/IP 体系结构中链路层和物理层合并为接口层

![](/img/TCP_IP_architecture.png)

封装 encapsulation  
application-layer message - 运输层增加首部信息（差错检测等），构成 transport-layer segment - 网络层增加首部信息（源和目的系统地址等），构成 network-layer datagram - 链路层生成 link-layer frame  
每层的分组分为首部字段和有效载荷 payload field，通常来自上一层的分组  

### 网络攻击

- 自我复制的恶意软件：virus, worm
- DoS (Denial-of-Service) attack 主机、服务器瘫痪
- 分组嗅探器 packet sniffer 获得传输分组的副本
- 冒充其他用户：IP spoofing - 需要端点鉴别
