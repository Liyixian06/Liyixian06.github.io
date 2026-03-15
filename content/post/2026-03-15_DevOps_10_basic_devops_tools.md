---
layout:		 single
title:       "DevOps 10 Basic DevOps Tools"
subtitle:    ""
description: " "
date:        2026-03-15T19:41:44-04:00
author: LiYixian
image:       ""
tags:        ["cs", "DevOps"]
categories:  ["Tech" ]
URL: "/2026/03/DevOps-10/"
math: False
---

### Infrastructure as Code

Automation 是 DevOps 的关键组成部分，它体现为一系列工具和脚本。这些工具和脚本既可以操作正在开发的代码，也可以操作支持从该代码创建和运行可执行文件的 infra。创建用于管理 infra 的脚本称为 Infrastructure as Code (IaC)。

IaC 的思想是把 infra 的配置和部署像代码一样对待：版本控制、共享、测试和复用。目的是避免环境不一致带来的错误，比如开发、测试、生产环境差异，或者库版本不同导致的问题。

- IaC 的 best practices 和代码相同，脚本要放在版本控制系统里，进行安全检查、测试和审核。
- IaC 的幂等性很重要，即一个 IaC 脚本多次执行应该产生相同结果，不受 infra 当前状态影响。这保证了重复部署或定期执行时的可靠性。
- Infra drift 问题指的是实际环境与 IaC 脚本生成的预期环境不一致。这会导致 debug 困难、环境不一致以及安全漏洞，因此最好所有修改都通过 IaC 完成，同时可以使用工具（如 Snyk、Driftctl）来检测 drift。

下面展开说明一些基本的 DevOps 工具类型，包括 issue tracking, version control, provisioning 和 configuration management 这四类。
### Issue Tracking

虽然 issue tracker（如 Issue Tracker, Jira, Solar Wind）早在 DevOps 之前就存在，但它是 DevOps 的重要流程。它记录 bug、功能需求或事件，并用唯一 ID 跟踪后续处理。

### Version Control

版本控制系统（VCS）是 DevOps 的基石，负责记录文本文件（代码、脚本、文档）的所有变更。其基本功能包括：

- version labeling/tagging
- branch：允许独立开发 `
- merge：整合不同 branch，解决冲突
- check in/out：和仓库同步代码

VCS 可以是集中式的或分布式的。前者如 SVN，必须联网才能操作，仓库在中央服务器；后者如 Git，本地有完整副本，可以离线提交，灵活性更高。

常见的 branching 策略有集中式工作流、feature 分支、个人分支，以及单仓库或多仓库的选择。

出于安全考虑，很多组织会引入 two-person verify 机制，以降低内部攻击风险，同时提高代码质量。

### Provisioning and Configuration Management

Provisioning 工具负责创建或配置节点和环境，确保环境加载指定软件；configuration management 工具负责保证多个节点上的文件和软件版本一致。两者都是声明式、幂等的。

Provisioning 工具根据规范创建或修改节点或环境，载入指定软件，并检查权限和安全性。常见工具包括 Docker（容器化）、Vagrant（开发环境）、Terraform（基础设施管理）以及云服务提供商的工具如 AWS CloudFormation。使用这些工具可以确保环境可重复、统一，并可扫描 Software Bill of Materials (SBOM) 或已知漏洞。

Config Management 工具可以让一组节点保持相同的软件和配置。与 provisioning 不同，它假设有一个主文件副本，通过安全通信（如 SSH 或 TLS）复制到目标节点。目标节点被分类管理，例如“web 服务器”，同一类的节点保持一致。常用工具包括 Chef、Puppet 和 Ansible。

### Vendor Lock In

在商业和技术上，依赖单一 provider 是很危险的（价格上涨、停产、服务中断）。避免 vendor lock in 的方法是选择跨 provider 兼容的工具，但可能无法直接使用特定 provider 的高级功能。例如 Terraform 可以跨云，但安全模型和某些特性不如 AWS CloudFormation 专用。

### Configuration Parameters

配置参数定义环境和服务行为，通常不同环境值不同（开发、测试、生产），包括网络信息（比如，DNS server 在哪里）、数据库连接信息、logging levels。

向 service 提供 config parameters 的方式包括资源文件（YAML 等）、环境变量、数据库或专用工具。无论采用什么方法，都应该进行版本控制，维护历史记录，并提供默认值和一致性检查。敏感参数（如数据库密码）需要特殊处理，否则可能泄露。
