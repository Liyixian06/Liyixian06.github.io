---
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

这是一个测试网站功能的页面。

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