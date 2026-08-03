# Public website collector

Bounded crawler for public pages discovered from local sitemap XML files. It saves source HTML, normalized text and a JSONL provenance manifest with retrieval time, redirects and SHA-256 hashes.

The crawler is business-data agnostic. Keep its output in an appropriate top-level `sources/` directory and pass explicit URL roots and exclusions for each research task.

```powershell
python tools/collectors/web/main.py `
  --base-url https://example.com/ `
  --sitemap-glob "sources/example/raw/sitemap-*.xml" `
  --output-dir sources/example `
  --include-root products
```
