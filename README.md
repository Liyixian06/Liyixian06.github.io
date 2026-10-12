# Liyixian06.github.io

这是一个 Hugo 框架生成的静态博客，主题使用了 [hugo-theme-cleanwhite](https://github.com/zhaohuabing/hugo-theme-cleanwhite)，配置 [Giscus](https://giscus.app/) 评论系统。  

#### 写作和发布
- 执行命令 `hugo new post/title.md` 新增 md 文件。
- 执行调试命令 `hugo server` 后直接通过 http://localhost:1313 地址访问本地生成预览网页，实时修改。
- 执行发布命令 `hugo` 在 public/ 目录下生成静态网站。
- git push 自动发布网站。

#### 豆瓣卡片

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

该命令只替换主机为 `*.doubanio.com` 的 `image` 字段，不修改其他元数据或已经使用其他图源的条目。

运行离线测试：

```bash
make douban-test
```
