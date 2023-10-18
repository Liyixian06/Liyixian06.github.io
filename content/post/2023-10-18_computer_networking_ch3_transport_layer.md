---
title:       "计算机网络笔记03：传输层"
subtitle:    ""
description: " "
date:        2023-10-18T14:17:50+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer networking"]
categories:  ["Tech" ]
URL: "2023/10/computer-networking-ch3/"
math: True

---

**Summary:**  
- 多路复用和多路分解
- UDP：特点、检验和
- 可靠数据传输：rdt、pipeline
- TCP：segment 结构、可靠数据传输、流量控制、连接管理

### 概述和传输层服务

传输层协议只工作在主机中，而非路由器  
传输层将从发送应用程序进程接收到的 message 转换为 segment with header，传递给网络层，后者封装成 packet 向目的地发送

传输层在网络层之上，后者提供主机之间的逻辑通信 logic communication，前者为不同主机的进程之间提供逻辑通信  
多个进程共享同一个网络层协议（IP 地址）和网络接口

两种传输层协议：用户数据报协议 UDP、传输控制协议 TCP  
网络层协议 IP 是不可靠服务，不保证 segment 中数据的完整  
UDP/TCP 提供的服务：  
1. 两个主机间 IP 的交互服务扩展为运行在主机上的两个进程之间的交互服务，称作多路复用 transport-layer multiplexing 和多路分解 demultiplexing
2. 在 segment header 中包括差错检查字段，进行完整性检查

TCP 的附加服务：  
1. 可靠数据传输 reliable data transfer
2. 拥塞控制 congestion control 调节发送端发送进网络的流量速率，使得每个连接都平等共享网络链路带宽

### 多路复用和多路分解

传输层从网络层接收 segment 后，要负责交付给主机上对应的应用程序  
一个进程有一个/多个 socket，每个有唯一标识符  
多路分解：传输层检查 segment 中的字段，定向到接收 socket  
多路复用：从不同 socket 中收集数据，封装 header 生成 segment，传递到网络层  

segment 中指示 socket 的字段：源端口号 source port number field、目的端口号 destination port number field  
端口号是 16bit 数字，0-1023 范围的叫周知端口号 well-known port number，要保留给 HTTP (80)/FTP (21) 等 well-known 应用层协议使用  

### UDP

UDP 的特点：  
1. 发送方和接收方不握手（无连接，连接要增加延时；协议简单）
2. 每个数据单元 datagram 独立传输
3. 提供多路复用分解、差错检查（IPv4 中可选，IPv6 强制）
4. 支持组播通信（点到多点）
5. 不提供可靠性保证、无拥塞控制

UDP segment 结构如下：  

![](/img/UDP_segment结构.png)

- 长度 - 字节数（header+data）  
- 检验和 - 差错检测，对 segment 中所有 16bit 字的和进行反码运算，溢出回卷  
- 复用和分解 - IP + 端口号 标识进程
- 如果需要实现可靠传输，需要增加机制

### 可靠数据传输

数据通过可靠信道传输，数据不会损坏/丢失，而且按照发送顺序交付  
可靠数据传输协议 reliable data transfer protocol (rdt)  
仅考虑单向数据传输的情况，发送方 `rdt_send()`，接收方 `rdt_recv()`  
使用有限状态机 FSM 描述发送方和接收方的状态迁移 event/actions  

#### rdt 的几个阶段

1. rdt 1.0：完全可靠信道  
无位错误、无 packet 丢失  

![](/img/rdt_1.0.png)
2. rdt 2.0：具有位差错信道的 stop-and-wait 协议  
可能具有位错误（0 变 1，1 变 0）  
自动重传请求 automatic repeat request ARQ 协议  
需要处理位差错的功能：  
- 差错检测
- 接收方反馈：肯定确认 ACK/否定确认 NAK  
- 重传  
问题：ACK/NAK 受损怎么办？  
不能简单地重传，可能导致重复接收（接收方不知道接收到的是新的还是重传）  

![](/img/rdt_2.0.png)
3. rdt 2.1：处理重复接收问题  
发送端在 packet 里附上序号，通过校验段判断 ACK/NAK 是否受损，受损则重传  
接收端通过序号判断是否是重传的 packet，在 ACK/NAK 中增加校验字段  
4. rdt 2.2：无 NAK  
只使用 ACK，不再使用 NAK（NAK-free）  
ACK 中携带所确认的 packet 的序列号，接收端发送最后收到正确的 packet 的 ACK；如果发送端收到 duplicate ACK，表明对当前 packet 的 NAK  
5. rdt 3.0：有位差错的丢包信道（比特交替协议 alternating-bit protocol）  
发送方等待一段时间，如果收不到 ACK，就判定 packet 已经丢失，重传  
如果接收方收到重复 packet（序号判断）就丢弃  
countdown timer 每次发送时重置  

#### 流水线协议

rdt 3.0 是一个 stop-and-wait 协议，吞吐量过低  
流水线协议：允许发送方发送多个 packet 而无需等待确认  

![](/img/流水线协议.png)

影响：  
- 增加序号范围
- 发送方和接收方都可能需要缓存多个 packet（已发送但没有确认的；已正确接收的）  
- 差错恢复：回退 N 步 Go-Back-N (GBN)、选择重传 selective repeat (SR)

1. Go-Back-N  
在流水线中未确认的 packet 数不能超过窗口长度 N；又称作滑动窗口协议  

![](/img/Go-Back-N.png)

- 每次要发送时先检查发送窗口是否已满  
- 对序号 n 的 packet 采取累积确认 cumulative acknowledgement，表明接收方已正确接收到序号为 n 之前（包括 n）的全部 packet  
- 超时则回退 N 步，重传所有未确认 packet  

2. 选择重传 SR  
GBN 的问题：单个 packet 的差错会重传很多没必要的 packet  
- SR 中发送方只重传丢失/受损的 packet  
- 接收方逐个确认正确接收的 packet，产生一个 ACK，不管是否按序  
	注意：必须重新确认已收到的序号小于当前窗口 base 序号的 packet，否则发送方窗口无法向前滑动（发送方和接收方窗口不一定同步）  
- 失序的 packet 缓存，直到收到这批所有丢失 packet 为止，然后可以按序交付  

### TCP

TCP 是面向连接 connection-oriented 的，互相发送数据之前必须先三次握手 three-way handshake（相互发送某些预备 segment，建立数据传输的参数）  

client 将数据通过 socket 引导到连接到发送缓存 send buffer 里，随后不时从中取出一段数据（ <= 最大 segment 长度 MSS），加上 TCP header，形成 TCP segment，下传到网络层并封装到 IP datagram 里，发送到网络中  
另一端接收到 segment 后，将数据放入该连接到接收缓存中，application 从缓存中读取数据  

![](/img/TCP发送缓存和接收缓存.png)

TCP segment 结构：  

![](/img/TCP_segment结构.png)

- 接收窗口：指示接收方愿意接受的字节数，用于流量控制  
- 发送序号：segment 首字节的字节流编号
	- 数据流按 MSS 切片成 segment，每个的序号是 i\*MSS
- 确认号：主机 A 的确认号是主机 A expect 从主机 B 收到的下一字节的发送序号

#### TCP 可靠数据传输

TCP 可靠数据传输：超时和冗余确认  
```c
while(1){
	switch(case)
		case 1: 从 application 接收到数据
			生成 TCP segment，序号 NextSeqNum
			if (定时器没有运行)
				启动定时器
			向 IP 传递 segment
			NextSeqNum += length(data)
			break;
			
		case 2: 定时器超时
			重传未应答的 segment 中序号最小的  
			启动定时器
			break;
			
		case 3: 收到 ACK，具有 ACK 字段值 y
			if (y > SendBase){
				SendBase = y
				if (当前仍无任何应答 segment)
					启动定时器
			}
			break;
}
```
如果在超时之前收到了确认号更大的确认 segment，那么就不会重传  
i.e. ACK=100 的确认 segment 丢失，但 ACK=120 的传到了，就不会重传前一个

如何设定超时间隔 RTO？  
如果是从 application 接收到数据/收到了 ACK，基于最近的往返时间 RTT 计算  
为已发送但尚未被确认的 segment 测量 SampleRTT，计算估计值和偏差，设置 RTO：

$$EstimatedRTT = (1-\alpha)EstimatedRTT + \alpha ·SampleRTT,\quad \alpha=1/8$$

$$DevRTT = (1-\beta)DevRTT+\beta·\mid SampleRTT-EstimatedRTT\mid,\quad\beta=1/4$$

$$RTO = EstimatedRTT+4·DevRTT$$

每次重传时，将下一次的 timeout 设为当前的两倍  

快速重传 fast retransmit：冗余 duplicate ACK  
接收方接收到相同数据的 3 个 duplicate ACK，表明跟在这个 segment 之后的 segment 已经丢失，执行快速重传（在该 segment 的定时器过期之前就重传）  

```c
case 3: 收到 ACK，具有 ACK 字段值 y
	if (y > SendBase){
		SendBase = y
		if (当前仍无任何应答 segment)
			启动定时器
	}
	else {
		y 收到的 duplicate ACK++
		if (duplicate ACK == 3)
			重传序号 y 的 segment
	}
	break;
```
选择确认 SACK：接收方有选择地确认失序 segment，而非累积确认最后一个正确接收的 segment  
和重传机制结合后类似 SR 协议（跳过重传那些被选择性确认的 segment）

#### 流量控制

流量控制的目的：避免发送方发送数据速度太快，接收方无法正确处理，接收 buffer 溢出  
手段：发送方维护一个接收窗口 receive window，指示接收方还有多少可用的 buffer，据此调整窗口大小  

![](/img/TCP流量控制滑动窗口.png)

$$LastByteRcvd-LastByteRead\leq RecBuffer$$

$$rwnd = RcvBuffer-(LastByteRcvd-LastByteRead)$$

$$LastByteSent-LastByteAcked\leq rwnd$$

$$EffectiveWindow=rwnd-(LastByteSent-LastByteAcked)$$

$$LastByteWritten-LastByteAcked\leq SendBuffer$$

$$if(LastByteWritten-LastByteAcked+y>SendBuffer)\ stop\ sending$$

主机 B rwnd = 0 时，为了确认主机 A 还能给 B 发送数据，要求主机 A 继续发送只有一个字节数据的 segment，B 确认后返回 rwnd 新值  

buffer 过小影响吞吐率，过大浪费主机存储资源  

#### TCP 连接管理

TCP 连接建立（三次握手）：  
- client 发送 SYN=1 的 segment，选择初始序号 client_isn
- server 为 TCP 连接分配 buffer 和变量，选择初始序号 server_isn，发送允许连接的 segment（SYNACK segment, SYN=1）  
- client 为连接分配 buffer 和变量，发送确认 SYNACK 的 segment (SYN=0)
	- 这一步就可以携带数据了
- 此后所有 segment 中 SYN=0

TCP 连接终止：  
- client 发送 FIN=1 的 segment
	- client 不再发送数据，但可以接收
- server 发送 ACK，再发送自己的 FIN=1 的 segment
- client 发送 ACK

### 网络拥塞

### TCP 拥塞控制
