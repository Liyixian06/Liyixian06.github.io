---
layout: 	 single
title:       "A Test Post"
subtitle:    "a subtitle"
description: "this is a description."
date:        2018-06-04
author: Liyixian
image:       ""
tags:        ["tag1", "tag2"]
categories:  ["Tech" ]
math: true
---

这是一个测试网站功能/记录后续准备添加功能的页面。

# Update

- 字数统计
- Giscus 评论系统
- 使用 KaTex 支持了 Latex
- 本来想尝试一下图床，但确实找不到什么好用的，加之发布图片的需求并没有那么大，所以姑且还是保持原状。
- hugo 版本更新到了 0.147.3

# shortcode

## Bilibili

{{< bilibili BV1KW4y1B7W6 >}}

## Spotify

*可能需要科学上网才能显示。*

{{< spotify type="track" id="2D3gvohUyOfXIVX6Mvhqae" height="80px">}}

# latex

只在需要渲染 latex 的页面加载，在 frontmatter 设置 `math: true` 即可。显示单行方程式，用 `$$` 作为分隔符，如：  
``
$$y_t = \beta_0 + \beta_1 x_t + \epsilon_t$$
``  
这会在网页上渲染为：  
$$y_t = \beta_0 + \beta_1 x_t + \epsilon_t$$

要显示 inline 方程，用 `\\( \\)` 分隔：  
``
\\(y_t\\)
``  
效果如 \\(y_t\\)。

注：要打花括号 `{}`，使用两个转义符 `\\{ \\}`，效果如 \\(\\{\\}\\)。

# To Do

- 搜索
- 换更好的评论系统（需求有：开源、免费、无广告、墙内正常访问，以及不需要专门注册账号，因此 Discus 不纳入考虑），比如 [Waline](https://waline.js.org/)、[Twikoo](https://twikoo.js.org/) 
- RSS 链接
- Tag 显示不全的问题
- 零零散散的装修
  - 代码复制
  - 总字数统计
  - 站点运行时长
  - 访问量统计
  - 代码块样式
  - 内容折叠
  - Dark Mode
  - ……