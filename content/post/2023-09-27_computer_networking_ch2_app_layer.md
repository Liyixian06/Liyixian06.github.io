---
title:       "计算机网络笔记02：应用层"
subtitle:    ""
description: " "
date:        2023-09-27T19:22:27+08:00
author: LiYixian
image:       ""
tags:        ["CS", "computer networking"]
categories:  ["Tech" ]
URL: "/2023/09/computer-networking-ch2/"
math: False
---

**Summary:**  

- 应用层协议和进程通信模型
- 运输服务
- Web 服务与 HTTP 协议
- 电子邮件
- 域名系统 DNS
- P2P 文件分发
- DASH
- 内容分发网络 CDN 
- Socket 编程

### 应用层协议原理

应用：可以进行通信的分布式进程  
#### 应用程序体系结构

应用程序体系结构由开发者设计  
1. client-server architecture (e.g.Web, email)  
服务器服务于主机的请求 - 数据中心  
客户之间不直接通信  
服务器：被动等待、长久在线、固定的 IP 地址  
2. P2P architecture  
弱化或根本不用服务器，主机之间（对等方）直接通信  
流量密集型应用：BitTorrent，迅雷，Skype  
自扩展性 self-scalability  

#### 进程通信

应用程序由通信进程对组成，每对的两个进程互相发送 message  
1. 客户和服务器
每对通信进程，标识发起通信方是 client ，接收方是 server  
2. 套接字 socket  
进程通过 socket 发送和接收报文，它是应用层和运输层之间的接口  
开发者对运输层的控制：选择协议、设定参数  
3. 进程寻址  
进程标识符：主机的 IP 地址（32 位的 IPv4/128 位的 IPv6）、端口号 port number  

#### 运输服务  

1. 可靠数据传输
2. 吞吐量 - 带宽敏感 bandwidth-sensitive/elastic application
3. 定时 - 交互式实时，对时延有要求
4. 安全性

因特网提供的运输服务：  
1. TCP：面向连接、可靠数据传输
2. UDP：不可靠数据传送 - 效率优先，*e.g.Skype*
3. 运输协议不提供吞吐量和定时保证

应用层协议：类型、语法、语义、时序  
*e.g. Web 应用层协议 HTTP、电子邮件协议 SMTP*  

### Web 和 HTTP 

HTTP 超文本传输协议 HyperText Transfer Protocol  
Web page 由对象 object 文件组成，可以通过 URL 寻址，通常包括 HTML 基本文件和引用对象  
HTML 基本地址通过对象的 URL 地址引用其他对象。URL 由两部分组成：存放对象的服务器主机名 + 路径名  
Web browser 即 client，用户请求 Web 页面，browser 向 server 发出对页面中包含对象的 HTTP 请求报文；server 接收请求，用饱含这些对象的 HTTP 响应报文响应  
TCP 是其支撑运输协议  
无状态协议 stateless protocol，server 不存储 client 的状态信息  
#### 非持续连接和持续连接

非持续连接 non-persistent connection：每个请求/相应对是经单独的 TCP 连接发送的；反之如果都经相同的 TCP 连接发送则为持续连接（默认）  

非持续连接中，每个 TCP 连接在 server 发送一个对象后就关闭  
用户可以配置 browser 控制连接的并行度  
往返时间 Round-Trip Time, RTT：分组从 client-server-client 花费的时间（包括内容见 [[计算机网络 Ch1 计算机网络和因特网#时延|Ch1 时延]]）  
每个对象经受两倍 RTT 时延，一个用于创建 TCP，一个用于请求/接收对象  
持续连接可以接连发送请求，不必等待之前的回答；如果经过一个超时间隔没有被使用，server 就关闭连接  

![](/img/HTTP发展.png)

#### HTTP 报文格式

HTTP 仅定义 client-server 的通信协议，不关于 client 如何解释一个 Web 页面  

1. HTTP 请求报文  
```http
GET /somedir/page.html HTTP/1.1
Host: www.someschool.edu
Connection: close
User-agent: Mozilla/5.0
Accept-language: fr
```
第一行：请求行 request line，后继行：首部行 header line  
request line 有三个字段：method, URL, HTTP version  
- `method`: GET/POST/HEAD/PUT/DELETE
- `URL`：请求对象的标识（主机名/路径名）
- `Host` 指明主机
- `Connection: close` 发送完被请求的对象就关闭连接
- `User-agent`：用户代理，即向 server 发送请求的 browser 类型
	- `Mozilla/5.0` 即 Firefox  
	- server 为不同类型的用户代理发送同一对象的不同版本

entity body 使用 POST method 时（e.g. 用户提交表单）才使用，包含的就是用户输入值  
HEAD 类似 GET，server 会响应，但不返回请求对象（调试）  
PUT 允许用户上传对象到指定 server 的指定路径  

2. HTTP 响应报文  
```HTTP
HTTP/1.1 200 OK
Connection: close
Date: Tue, 19 Aug 2015 15:11:03 GMT
Server: Apache/2.2.3 (CentOS)
Last-Modified: Tue, 18 Aug 2015 15:11:03 GMT
Content-Length: 6821
Content-Type: text/html
(data data data data...)
```
三个部分：初始状态行 status line，header line，entity body  
entity body 包含请求对象本身（data data data data...）  
状态行有三个字段：协议版本、状态码、状态信息  
- `200 OK`：请求成功，信息在响应报文中
- `301 Moved Permanently`：请求的对象已经被永久转移了，新的 URL 定义在响应报文的 header line 中；client 将自动获取新的 URL
- `400 Bad Request`
- `404 Not Found`
- `505 HTTP Version Not Supported`

#### cookie

server 希望把内容和 client 身份联系起来 - cookie 对 client 进行跟踪  

cookie 的四个组件：  
- HTTP 响应报文、请求报文中的 cookie header line
- 用户主机中保留的 cookie 文件，browser 管理
- Web 站点的后端数据库

用户首次访问 Web 站点时：  
1. 站点在后端数据库生成一个唯一识别码，然后用包含 `Set-cookie` 的 header 对 browser 进行响应；
2. browser 收到该 HTTP 响应报文，读到 header 中的 cookie，在其管理的特定 cookie 文件中添加一行，包含服务器主机名和识别码；  
3. 此后，用户每次请求这个站点的页面，browser 都会查询该 cookie 文件并将识别码放到请求报文的 header 中；  
4. 这样，Web 站点服务器就可以跟踪用户在站点的活动，将用户信息和识别码相关联

#### Web 缓存

Web 缓存器 Web cache/代理服务器 proxy server，是可以代表初始 Web 服务器满足 HTTP 请求的实体；可以配置 browser，使得用户所有的 HTTP 请求首先指向 Web cache  
Web cache 会检查本地是否存储了请求对象的 copy，有就返回响应，没有就对初始 server 发起请求，建立 copy，然后返回响应（即，既是 client 又是 server） 

部署 Web cache 的原因：  
- 减少对 client 请求的响应时间（client 和 Web cache 之间的瓶颈带宽比较高）
- 减少一个机构 *（e.g.大学、公司）* 的接入链路到因特网的流量，减少带宽费用

#### 条件 GET 方法

解决 Web cache 中存放的对象 copy 是不是最新版的问题  
Web cache 在存储对象时也会存储最后修改日期 `Last-Modified` 
条件 GET 方法 conditional GET：Web cache 给 Web server 发送的请求报文包含一个 `If-Modified-Since` header line，server 会确认对象是否被修改过  

### 电子邮件

email 系统总体由三个部分组成：用户代理 user agent、邮件服务器 mail server、简单邮件传输协议 Simple Mail Transfer Protocol SMTP  
- user agent 如 Outlook
- user agent 向 mail server 发送邮件，邮件放在 mail server 的外出报文队列中
- 用户要阅读时，user agent 在 mail server 的邮箱里取得报文
- SMTP 是 email 的应用层协议  

发送过程：A user agent - A mail server - B mail server - B mailbox

#### SMTP

SNTP 运行在 mail server 上，既是 client 又是 server，它发现报文队列中的报文之后就会创建一个到接收方的 SMTP 的 TCP 连接  
在 SMTP client 和 server 之间交换报文文本时，client 会发送命令 *（e.g. HELO, MAIL FROM, RCPT TO, DATA, QUIT）* ，server 对每条命令做出回答  

#### 和 HTTP 的对比

区别：  
- HTTP 主要是拉取协议 pull protocol，即 Web server 上装载信息，client 使用 HTTP 从 server 拉取信息，TCP 连接是接收方发起的
- SMTP 主要是推送协议 push protocol，发送邮件的 server 把报文 push 到接收 server 处，TCP 连接是发送方发起的
- 处理多媒体类型文档时，HTTP 把每个对象封装到单独的响应报文中，SMTP 把所有对象放在同一个报文中

### DNS 目录

主机的标识方法：主机名 hostname/IP 地址  

#### DNS 提供的服务

域名系统 Domain Name System DNS：主机名到 IP 地址转换的目录服务  
由分层的 DNS server 实现的分布式数据库；使得主机能够查询数据库的应用层协议  
DNS 由其他应用层协议 HTTP/SMTP/FTP 使用，将主机名解析为 IP 地址  
每次用户请求一个 URL 时，必须先抽取出主机名传给 DNS，收到含有 IP 地址的响应报文，然后再向位于该 IP 地址的 HTTP server 发起 TCP 连接  

其他服务：主机别名 host aliasing、mail server aliasing、负载分配（在冗余的 server 之间分配）

#### DNS 工作机制

分布式数据库：DNS 的大量 server 以层次方式组织  
三种类型的 server：根 DNS server、Top-Level Domain TLD server、权威 DNS server  
递归查询，上一级的 server 提供下一级 server 的 IP 地址  
- TLD server：对每个 TLD *（e.g. com, org, net, edu, gov）* 
- 权威 DNS：所有具有公共可访问主机（Web server、mail server）的机构都必须提供可访问的 DNS 记录，将主机名映射为 IP 地址  

先在本地 DNS server（LDNS）的 cache 里找，找不到再依次请求根 DNS server - TLD server - 权威 DNS server，每一级都直接向本地 DNS server 发送下一级的 IP 地址/所查询主机名的 IP 地址  

### P2P 文件分发

P2P architecture 中成对主机直接通信，它们受用户控制，不为服务提供商所拥有  
P2P 从单一服务器向大量主机（peer）分发一个大文件时，每个 peer 能向其他 peer 重新分发它已经收到的文件部分  

P2P architecture 的自扩展性：peer 除了是比特的 consumer，还是重新分发者；peer 越多，它们帮 server 承担的负载就越多，传输越快  

P2P 文件分发协议：BitTorrent  
参与一个特定文件分发的所有 peer 的集合称为 torrent，彼此下载等长度的文件块 chunk，下载的同时也为其他 peer 上传  
每个 torrent 有一个基础设施节点 tracker；一个 peer 加入 torrent 时，向 tracker 注册自己，并周期性告知自己仍在 torrent 里  
tracker 随机地选择一部分 peers 发送其 IP 地址给新加入的 peer，后者会与它们所有创建并行的 TCP 连接，周期性地询问它们持有的 chunk 列表，对当前自己还没有的 chunk 发起请求  
选择 chunk：使用 rarest first 技术以均衡每个 chunk 在 torrent 中的数量  
兑换算法：prioritize 能最快向自己发送数据的 peer，周期性更新  
“一报还一报” tit-for-tat 交换激励机制，避免用户成为搭便车者  
### 视频流和内容分发网

#### HTTP 流和 DASH

视频最大特征：高比特率；最重要的性能度量：平均端到端吞吐量  
HTTP 流中，视频是存在 HTTP server 中的普通文件，每个文件有特定 URL，用户看视频时发送一个对该 URL 的 HTTP GET 请求，响应报文中发送视频文件  
问题：所有用户接受的是相同编码的视频  

新型的经 HTTP 的动态适应性流 Dynamic Adaptive Streaming over HTTP, DASH  
基本思想：
- 视频拆分为固定时长、不同码率的片段
- Media Presentation Description MPD 文件描述片段信息，和视频一起存在 DASH server
- DASH client 评估当前情况，动态选择不同码率的片段
- 自适应码率 Adaptive bitrate ABR 规则
	- 码率切换：基于吞吐量/缓冲大小
	- 放弃请求规则：下载时如果有卡顿就转向码率更低的版本

#### CDN

内容分发网络 Content Distribution Network CDN  
单一 data center 分发流量的问题：可能跨越很多通信链路的 ISP，瓶颈问题；发送相同内容的带宽浪费；data center 故障的风险  
CDN 将 client 请求定向到可以提供最佳体验的 CDN server，一种 Web cache 系统  
could be private CDN（内容提供商自己拥有）or third-party CDN（代表多个内容提供商分发内容）  

操作细节：

1. 重定向  
权威 DNS server 不会直接向 LDNS 返回 IP 地址，而是返回一个 CDN 域的主机名；从这时起，DNS 请求就进入了 CDN 专用的 DNS 基础设施（负载均衡 DNS），LDNS 再向其发送请求，后者的 DNS 系统指定 CDN server 并返回 IP 地址  
2. 集群选择策略 cluster selection strategy  
负载均衡 DNS 收集 CDN server 的位置和负载情况  
地理临近；周期性测量集群和 client 之间的 latency 和丢包性能  

### Socket 编程

API：选择传输层协议；修改参数  
TCP or UDP?  
#### UDP  

![](/img/UDP_application.png)

操作系统会自动将源地址（IP + port）附在 packet 上  

client 的代码：
```python
# UDPclient.py
from socket import *
# 提供 IP 地址或主机名，如果是后者则自动执行 DNS lookup 解析
serverName = 'hostname'
serverPort = 12000
# AF_INET 指示底层网络使用 IPv4，SOCK_DGRAM 指示 UDP
clientSocket = socket(AF_INET, SOCK_DGRAM)
message = raw_input('Input lowercase sentence:')
clientSocket.sendto(message.encode(), (serverName, serverPort))
# 接收数据和源地址，取缓存长度 2048 作为输入
modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
print(modifiedMessage.decode())
clientSocket.close()
```
server 的代码：  
```python
from socket import *
serverPost = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
# 将端口号12000和server的socket绑定在一起
serverSocket.bind(('', serverPort))
print("The server is ready to receive.")
while True:
	message, clientAddress = serverSocket.recvfrom(2048)
	modifiedMessage = message.decode().upper()
	serverSocket.sendto(modifiedMessage.encode(), clientAddress)
```
#### TCP

TCP 是面向连接的协议，因此 client 和 server 在开始传送数据之前要先握手、创建一个 TCP 连接，两端分别与 client 和 server 的 socket address 相联系；此后，只需要经过 socket 将数据扔进 TCP 连接，不需要再附上地址  

流程：  
1. client 生成其 TCP socket，指定 server 欢迎 socket 的地址；
2. client 发起三次握手，创建和 server socket 的 TCP 连接；
3. server 创建一个新的 connection socket，专门用于特定的 client  

注意：TCP server 有两个 socket，一个是欢迎 socket（所有要和 server 通信的 client 的首次接触点），一个是新生成的 connection socket（为和每个客户通信生成的 socket）

![](/img/TCP_server_socket.png)

![](/img/TCP_application.png)

client 的代码：
```python
from socket import *
serverName = 'servername'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
# 发起 TCP 连接
clientSocket.connect((serverName, serverPort))
sentence = raw_input('Input lowercase sentence:')
clientSocket.send(sentence.encode())
modifiedSentence = clientSocket.recv(1024)
print('From Server: ', modifiedSentence.encode())
clientSocket.close()
```
server 的代码：
```python
from socket import *
serverPort = 12000
# SOCK_STREAM 指定 TCP
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
# 等待某个 client 敲门，参数是请求连接的最大数量
serverSocket.listen(1)
print('The server is ready to receive.')
while True:
	# 创建 client 专用的新 socket
	connectionSocket, addr = serverSocket.accept()
	sentence = connectionSocket.recv(1024).decode()
	capitalizedSentence = sentence.upper()
	conenctionSocket.send(capitalizedSentence.encode())
	# 关闭连接，但 serverSocket 还保持打开，另一个 client 此时可以敲门
	connectionSocket.close()
```

#### C 中常用的 Socket 函数

- `WSAStartup`：初始化 Socket DLL，协商使用的 Socket 版本
- `WSACleanup`：结束使用 Socket，释放 Socket DLL 资源
- `socket`：创建一个 socket，绑定到一个传输服务
- `bind`：将一个本地地址绑定到指定的 socket
- `listen`：server 使用，使 socket 进入监听状态，监听远程连接是否到来
- `connect`：client 使用，向特定 socket 发出连接请求
- `accept`：server 使用，接受特定 socket 请求等待队列中的连接请求
- `sendto/recvfrom`：向特定目的地发送/接收数据
- `send/recv`：向远程 socket 发送数据/从目的地接收数据
- `closesocket`：关闭一个存在的 socket 
