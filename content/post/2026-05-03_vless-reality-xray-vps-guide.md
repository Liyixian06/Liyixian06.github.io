---
layout:		 single
title:       "傻瓜都能学会的代理服务搭建教程"
subtitle:    ""
description: "如何搭建一个基于 Xray 的代理服务（VLESS + Reality）"
date:        2026-05-03T21:35:20+08:00
author: LiYixian
image:       ""
tags:        ["cs", "tricks"]
categories:  ["Tech" ]
URL: "/2026/05/vless-reality-xray-vps-guide/"
math: False
---

总体来说，搭建代理需要以下四个步骤：

- 购买一台海外云服务器，SSH 登入
- 在服务器上跑一个服务（Xray）
- 打开一个端口
- 客户端连接

### 购买云服务器

可能是整个流程中最麻烦的一步，困难的地方主要在于需要找到一个没有被 GFW 屏蔽，而且最好能免费更新公网 IP 的服务器提供商。比较知名的提供商有搬瓦工 Bandwagon、V.PS、ByteVirt、RackNerd、Vultr、ClawCloud 等。

鉴于这只是一个如何跑通流程的教程，这里就不展开比较各个提供商了，直接使用最简单的 [Vultr](https://www.vultr.com/)：它的优点是按分钟计费，IP 不能用的时候可以直接删除重建，在不需要使用的时候把实例关掉就不会扣钱，而且可以用支付宝充值；缺点是由于太多中国人用了，IP 被封得比较严重，经常不稳定。

具体搭建方式可以参见这个视频：[【如何用 vultr 搭建一台超便宜的云服务器】](https://www.bilibili.com/video/BV1zeByBHEd9/)，最便宜的一个月 5 刀。部署完之后点进实例，能看到它的 IP 地址和密码，然后就可以进入下一步。

### Xray 服务

主流的翻墙协议也有很多种可以选择，包括 Shadowsocks 2022 (SS)、ShadowsocksR (SSR)、VMess、VLESS + Reality、Trojan、Hysteria2、OpenConnect 等；这里也不展开比较各个协议，使用目前比较主流的 VLESS + Reality 方案。

首先用 SSH 登入云服务器，输入刚才的密码：

```bash
ssh root@[你的IP地址]
```

在服务器上安装 Xray 服务：

```bash
apt update && apt install -y curl unzip
bash <(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)
```

生成一个 UUID:

```bash
cat /proc/sys/kernel/random/uuid
```

记下生成的 UUID。  
生成 Reality 密钥：

```bash
xray x25519
```

你会看到类似下面的输出：

```
PrivateKey: ...
Password (PublicKey): ...
```

把两个都保存下来。

最后，编辑配置文件：

```bash
vim /usr/local/etc/xray/config.json
```

可以直接使用下面的模板，替换掉标注的三个地方（UUID、私钥、shortIds）：

```yaml
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 443,
      "listen": "0.0.0.0",
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "你的UUID",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": [
            "www.microsoft.com"
          ],
          "privateKey": "你的Private key",
          "shortIds": [
            "自定义短标识，建议 8 位 hex，例如 a1b2c3d4"
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
```

保存配置文件并退出，然后启动 Xray 服务：

```bash
systemctl restart xray
systemctl enable xray
```

查看 Xray 服务的状态：

```bash
systemctl status xray
```

如果显示 `Active: active (running)`，那么 Xray 服务已经启动了。

### 打开端口

在云服务器的控制台打开端口。具体设置因服务器提供商而异，有可能叫 Security Group / VPC Firewall / Network Rules / Firewall Rules 等，然后在服务器实例上（一定要绑定到服务器实例！）添加一条：

```
protocol: TCP
port: 443
source: 0.0.0.0/0
```

在服务器上确定 Xray 在监听：

```bash
ss -lntp | grep 443
```

如果看到类似 `LISTEN 0 128 0.0.0.0:443 ...` 的输出，说明服务在正确监听 443 端口。

然后，确认在本地是否能连接到 443 端口：

```bash
nc -vz [你的IP地址] 443
```

如果看到 `Connection to [IP] port 443 [tcp/https] succeeded!`，说明端口能够连通，接下来只需要在客户端配置一下连接即可。

\*Debug：如果本地 Xray 监听是正常的，而且已经在云服务器打开了端口，本地还是无法连通，有可能是系统防火墙的问题；可以使用 `ufw status` 查看是否放行端口，如果没有的话，执行 `ufw allow 443/tcp` 放行 443 端口即可。

### 配置客户端

客户端也有若干种选择，如 Clash / V2RayN / Shadowrocket 等，我使用的是 V2RayN，但无论用什么，核心参数是一样的：

- 地址：服务器 IP
- 端口：443
- 用户 ID：UUID
- 传输协议：TCP
- TLS / 安全：Reality
	- public key：Reality 的 Public Key
	 - short id：配置里的 shortId
	 - server name / SNI：`www.microsoft.com`（也可以用其他可访问的 HTTPS 大网站，和配置文件里的 dest 与 serverNames 保持一致即可）
	 - Fingerprint：chrome（可选，推荐）
- flow：`xtls-rprx-vision`

保存节点，现在应该连接成功了。后面想再优化，可以再做多用户、分流、规则优化、BBR 加速等，但上面就是最基本的配置。

V2RayN 的路由规则讲解：[说一下自带的两个规则](https://github.com/2dust/v2rayN/issues/3983#issuecomment-2563289269)
