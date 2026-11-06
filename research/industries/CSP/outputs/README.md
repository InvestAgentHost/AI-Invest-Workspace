# HTML 阅读版

[打开 HTML 阅读版](notes.html)。浏览器可直接打开，无需启动服务。图片和所引本地文本资料已嵌入单个文件，外部原始网页需联网访问。页面提供目录、搜索、脚注查看、图片放大和打印样式。

主稿为 [notes.md](../notes.md)，HTML 是生成时的快照。修改主稿后，在 Workspace 根目录重新生成：

```sh
.venv/bin/python tools/research/render_html.py \
  research/industries/CSP/notes.md \
  research/industries/CSP/outputs/notes.html \
  --title 'AI 算力与云服务' \
  --subtitle '四家 CSP 与三家 Neocloud 的商业模式、资本回报与供需判断' \
  --eyebrow '行业研究 / AI 基础设施' \
  --monogram AI
```

生成器依赖 Pandoc，以及 Workspace Python 环境中的 beautifulsoup4、Pillow。主稿与生成器保留在 Git 中，HTML 和排版检查图片属于可重建输出。
