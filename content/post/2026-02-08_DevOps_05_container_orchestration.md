---
layout:		 single
title:       "DevOps 05 Container Orchestration"
subtitle:    ""
description: " "
date:        2026-02-08T12:44:15-05:00
author: LiYixian
image:       ""
tags:        ["cs", "DevOps"]
categories:  ["Tech" ]
URL: "/2026/02/DevOps-05/"
math: False
---

### Pods

Kubernetes 不直接管理容器，只管理 Pod；Pod 是容器的上一级抽象，可以只装一个容器，也可以装多个。为了实现隔离，Pod 被划分到不同的 namespaces 中，后者是 Kubernetes 使用的一种 Linux 机制，[前文亦有提及](https://liyixian06.github.io/2026/01/DevOps-01-02/#containers)。

![](/img/Kubernetes_stack.png)

- 单容器 Pod 的情况下，Pod 拿到一个 IP 和一组端口，外界通过 Pod 的 IP + 端口访问容器。
- 多容器 Pod 的设计目标是 tightly coupled，也就是说这些容器应该具有相同的生命周期，同时被分配和释放。典型例子就是业务容器 + sidecar（即 utility 容器如日志或 monitor），它们被调度到同一主机上，彼此通信可以通过 localhost（带着彼此的端口号）、共享内存或者共享存储 volume，不需要经过网络。这带来的直接后果是：每个 Pod 可能都有一套自己的 sidecar，比如日志容器不会全局共享。所有容器共享同一个 IP，但端口不能冲突。

### Orchestration

编排系统本身并不包含容器，但它管理容器的生命周期，包括资源调配、部署、扩展和负载均衡。和 VM 时代相比，容器管理里这些职责被拆开了，扩缩容和故障恢复是编排系统的核心职责，而 discovery 和通信模式更多交给 service mesh。

以 Kubernetes 为例，可以设置包含以下信息的文件：

- Pod name
- Pod 里包含的容器
- 要创建的 Pod 实例数量
- Scaling rules

它是声明式的，描述所需要的状态，剩下的交给系统；Kubernetes 会持续监控健康状况，挂了就补，繁忙就创建新的 Pod。

### Container 安全

镜像创建的核心思想是最小化：

- 创建时要禁用 SSH 连接，否则会增加遭受恶意攻击的风险
- 必须设置以非特权用户身份创建
- 不能把 credential（密码、secret 或 key）存在镜像里，必须存在外部

容器部署时要限制可能造成的破坏范围：

- 设置容器可以消耗的资源上限，否则可能会导致其他容器资源不足，引发 DoS
- Root filesystem 必须是只读，不能写
- 容器不能访问 OS 的内核 namespace

运行时强调监控和审计，比如用 Falco 这种 threat detection 工具检测异常行为（如，创建特权容器或 unauthorized 用户读取敏感文件）。

### Service Mesh

在微服务数量上来之后，通信本身变成了一个系统性问题。Service mesh 的职责是管理 discovery 和通信模式，同时顺带处理安全、resiliency 和可观测性。

Service mesh 的基本架构分为 control plane 和 data plane。后者的元素是容器，或 Kubernetes 中的 Pods。理论上，任何容器都能和其他任何 Pod 通信，但实际上只允许和策略定义的那一小部分通信对象交流，通信路径构成了一个网络（mesh）。Control plane 就负责构建这个 mesh，它决定容器可能的通信路径，还可以限制消息速率、制定安全策略、收集容器间消息流量的指标。

Data plane 执行三种功能：

- 安全网络功能，包括所有服务之间的通信或 routing。具体来说，包括 service discovery，建立 TLS session，为每个微服务建立网络路径和路由规则，鉴权。
- 策略执行，通过 sidecar proxy（即，在相关服务容器所在的 Pod 里放一个 proxy，它通过 configuration 参数检查所有进出流量）执行 control plane 定下的规则。
- 收集服务的遥测数据以实现可观测性。

最后，关于 service mesh 和 orchestration 怎么配合，以扩容为例：当编排系统创建一个新的服务实例时，它会将这个新实例的存在通知 control plane，后者将原有实例的 discovery 信息复制给新实例，并将新实例的身份信息添加到其他（能和它通信的）实例的 discovery 中，新实例自然融入原有网络。

### Container 技术的发展

容器管理正朝着两个不同的方向发展：

- 一条是以 Kubernetes 为代表的容器编排，把容器能力完整暴露给服务设计者，需要关注 Pod 设计、扩缩规则和性能监控；
- 另一条是 serverless，把容器彻底藏起来，开发者只写函数，平台用容器来实现隔离和弹性。

两条路线对容器技术的诉求不同，一个追求通用和可配置，一个追求极致的启动速度和复用。现在两条路线还共用同一套容器技术，但未来很可能会进一步分化。
