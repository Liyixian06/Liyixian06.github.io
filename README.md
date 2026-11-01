# Liyixian06.github.io

这是一个 Hugo 框架生成的静态博客，主题使用了 [hugo-theme-cleanwhite](https://github.com/zhaohuabing/hugo-theme-cleanwhite)，配置 [Giscus](https://giscus.app/) 评论系统。  

#### 写作和发布

- 执行命令 `hugo new post/title.md` 新增 md 文件。
- 执行调试命令 `hugo server` 后直接通过 http://localhost:1313 地址访问本地生成预览网页，实时修改。
- 执行发布命令 `make build` 在 public/ 目录下生成静态网站和搜索索引。
- git push 自动发布网站。

#### 本地搜索

搜索使用 Pagefind，索引由 GitHub Actions 在每次 Hugo 构建后自动生成，不需要单独的账号或远程索引。执行以下命令可构建网站和中文搜索索引，并启动本地预览：

```bash
make search-preview
```

Pagefind 默认在 http://localhost:1414 提供预览。

#### 图片优化

日记照片统一使用长边不超过 2000 px、质量 82 的 WebP。压缩前会自动应用照片的 EXIF 方向信息，避免手机照片发生旋转。首次使用时安装 Python 依赖和编码工具：

```bash
make douban-install
brew install webp
```

先查看待处理图片，再执行转换；脚本会同步更新 Markdown 中的图片路径：

```bash
make images-check
make images-optimize
```
