---
layout: 	 single
title:       "A Test Post"
subtitle:    "a subtitle"
description: "this is a description."
date:        2018-06-04
author: Liyixian
image:       ""
tags:        ["CS"]
categories:  ["Tech" ]
URL:  "/test/"
math: true
---

这是一个测试网站功能/记录后续准备添加功能的页面。

# Update

- 字数统计
- Giscus 评论系统
- 使用 KaTex 支持了 Latex
- 本来想尝试一下图床，但确实找不到什么好用的，加之发布图片的需求并没有那么大，所以姑且还是保持原状。
- hugo 版本更新到了 0.147.3
- 显示全部 tag 以及文章数
- 内容折叠
- 修改了代码块样式，增加了代码复制功能
- 把书影音展示的方式改了，增加了自动根据url从豆瓣提取信息的爬虫脚本，另外由于豆瓣防盗链的问题，图片外链改成了 NeoDB
- 在页脚增加全站总字数和建站时长统计

{{% spoiler "You killed my father!" %}}
I am your father.
NOOOOOOO!
{{% /spoiler %}}

```markdown
This is the new code block. (You can copy it!)
```

# shortcode

## Bilibili

{{< bilibili BV1KW4y1B7W6 >}}

## Youtube

*可能需要科学上网才能显示。*

{{<youtube 2ykcUuZg9hI>}}

## Spotify

*可能需要科学上网才能显示。*

{{< spotify type="track" id="2D3gvohUyOfXIVX6Mvhqae" height="80px">}}

## 网易云音乐

使用[APlayer](https://github.com/DIYgod/APlayer) 和 [MetingJS](https://github.com/metowolf/MetingJS)。

{{<aplayer server="netease"  type="song" id="16778265">}}

## 豆瓣

读取本地文件夹下的CSV文件进行展示。

### 新增和同步数据

首次使用时创建专用 Python 虚拟环境并安装同步脚本依赖：

```bash
make douban-install
```

新增卡片时，在 `assets/douban/book.csv` 或 `assets/douban/movie.csv` 中增加一行，只填写 `url`：

```csv
,,,,https://book.douban.com/subject/25697546/,
```

先检查待同步条目，再抓取豆瓣元数据并写回 CSV：

```bash
make douban-check
make douban-sync
```

同步脚本只处理文字元数据完全为空的新增行，不覆盖已有完整条目或人工填写的封面。标题、评分、标签和简介来自豆瓣；封面优先使用 NeoDB 托管的远程地址，不下载到仓库。若豆瓣返回安全验证，失败行会保持原样，可以稍后重试。

将图书 CSV 中现存的豆瓣图片外链迁移为 NeoDB 封面：

```bash
make douban-migrate-book-images
```

该命令只替换主机为 `*.doubanio.com` 的 `image` 字段，不修改其他元数据或已经使用其他图源的条目。使用 `make douban-test` 可以运行离线测试。

### 在文章中使用

将豆瓣图书或电影条目 URL 传给 `douban-card`：

```markdown
{{</* douban-card "https://book.douban.com/subject/25697546/" */>}}
{{</* douban-card "https://movie.douban.com/subject/1300868/" */>}}
```

{{< douban-card "https://book.douban.com/subject/25697546/" >}}

{{< douban-card "https://movie.douban.com/subject/1300868/" >}}

## 图片排版

### 限制单张图片宽度

`width` 可以使用 `px` 或百分比，`align` 支持 `left`、`center` 和 `right`，`caption` 用于添加图片说明：

```markdown
{{</* photo src="/img/journal/2026/cold-dew/Wooster-proposes-Jeeves-disposes.webp" width="420px" align="center" caption="图片说明" */>}}
```

{{< photo src="/img/journal/2026/cold-dew/Wooster-proposes-Jeeves-disposes.webp" width="420px" align="center" caption="限制宽度并居中显示" >}}

### 双栏或三栏图片

`columns` 支持 `2` 或 `3`；窄屏会自动切换为单栏：

```markdown
{{</* photo-grid columns="2" */>}}
{{</* photo src="/img/a.webp" caption="第一张" */>}}
{{</* photo src="/img/b.webp" caption="第二张" */>}}
{{</* /photo-grid */>}}
```

{{< photo-grid columns="2" >}}
{{< photo src="/img/journal/2026/cold-dew/midautumn.webp" caption="第一张" >}}
{{< photo src="/img/journal/2026/cold-dew/Oktoberfest.webp" caption="第二张" >}}
{{< /photo-grid >}}

### 图片与文字并排

`side` 用来指定图片位于左侧或右侧，`width` 控制图片所占宽度；窄屏会自动改为上下排列：

```markdown
{{</* image-text src="/img/example.webp" side="left" width="42%" */>}}
这里可以正常使用 **Markdown**。
{{</* /image-text */>}}
```

{{< image-text src="/img/journal/2026/cold-dew/chaykhana.webp" side="left" width="42%" >}}
这里可以正常使用 **Markdown**，也可以加入链接、列表或其他段落内容。
{{< /image-text >}}

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

- 换更好的评论系统（需求有：开源、免费、无广告、墙内正常访问，以及不需要专门注册账号，因此 Discus 不纳入考虑），比如 [Waline](https://waline.js.org/)、[Twikoo](https://twikoo.js.org/) 
- 零零散散的装修
  - ~~代码复制~~
  - ~~总字数统计~~
  - ~~站点运行时长~~
  - 访问量统计
  - ~~代码块样式~~
  - Dark Mode
  - ……
