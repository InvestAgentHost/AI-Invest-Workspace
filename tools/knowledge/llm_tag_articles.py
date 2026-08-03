"""Tag Markdown source articles with an OpenAI-compatible LLM API.

The model is free to choose tags, while this tool owns only tags prefixed with
``llm/``. Existing source and manual tags are preserved. Responses are cached
by article content, model, and prompt version so reruns do not call the API
unnecessarily.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMPT_VERSION = "llm-tags-v1"
LLM_TAG_PREFIX = "llm/"
DEFAULT_ARTICLES = Path(
    "sources/publishers/substack/damnnang/normalized/markdown"
)
DEFAULT_CACHE = Path("knowledge/indexes/llm-tags/substack/damnnang")
DEFAULT_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

SYSTEM_PROMPT = """You are an investment-research source tagger.

Read the complete Markdown article supplied by the user. Return only JSON with
a `tags` array. Choose 3 to 8 concise tags that describe the article's core
topics, technologies, companies, industries, or value-chain segments.

Rules:
- Tags must describe the article's central discussion, not incidental mentions.
- Use short reusable noun phrases, not sentences or investment recommendations.
- Avoid generic tags such as ai, technology, stock, business, or research.
- Do not include author, source, date, URL, or access-status tags.
- Use one canonical wording for synonymous concepts within this article.
- You may use English or Chinese, matching the article's terminology.
- Tags are free-form: infer useful concepts from the article rather than using
  a fixed vocabulary.
"""

TAG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tags": {
            "type": "array",
            "minItems": 3,
            "maxItems": 8,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1, "maxLength": 64},
        }
    },
    "required": ["tags"],
}


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return "", text
    return match.group(1), match.group(2)


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding the process environment."""

    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            os.environ.setdefault(key, value)


def remove_tags_block(frontmatter: str) -> tuple[str, list[str]]:
    lines = frontmatter.splitlines()
    kept: list[str] = []
    tags: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("tags:"):
            kept.append(line)
            index += 1
            continue

        index += 1
        while index < len(lines):
            child = lines[index]
            if child.startswith("  - "):
                tags.append(child[4:].strip().strip('"').strip("'"))
                index += 1
                continue
            if not child.strip():
                index += 1
                continue
            break
    return "\n".join(kept), tags


def article_without_llm_tags(text: str) -> str:
    frontmatter, body = split_frontmatter(text)
    if not frontmatter:
        return text
    clean_frontmatter, tags = remove_tags_block(frontmatter)
    stable_tags = [tag for tag in tags if not tag.startswith(LLM_TAG_PREFIX)]
    if stable_tags:
        clean_frontmatter += "\ntags:\n" + "\n".join(
            f"  - {tag}" for tag in stable_tags
        )
    return f"---\n{clean_frontmatter}\n---\n{body.lstrip()}"


def content_hash(text: str) -> str:
    return hashlib.sha256(article_without_llm_tags(text).encode("utf-8")).hexdigest()


def normalize_tag(value: str) -> str:
    tag = value.strip().lstrip("#").strip()
    if tag.lower().startswith(LLM_TAG_PREFIX):
        tag = tag[len(LLM_TAG_PREFIX) :]
    tag = re.sub(r"\s+", "-", tag)
    tag = tag.replace("_", "-")
    tag = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff/.-]", "-", tag)
    tag = re.sub(r"-{2,}", "-", tag).strip("-./")
    if tag.isascii():
        tag = tag.lower()
    return f"{LLM_TAG_PREFIX}{tag}" if tag else ""


def normalize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        raise ValueError("API response field 'tags' must be an array")
    tags: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        if not isinstance(raw_tag, str):
            raise ValueError("Every tag must be a string")
        tag = normalize_tag(raw_tag)
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    if not 3 <= len(tags) <= 8:
        raise ValueError(f"Expected 3 to 8 usable tags, got {len(tags)}")
    return tags


def write_tags(text: str, llm_tags: list[str]) -> str:
    frontmatter, body = split_frontmatter(text)
    if not frontmatter:
        raise ValueError("Article has no YAML frontmatter")
    clean_frontmatter, existing_tags = remove_tags_block(frontmatter)
    kept_tags = [tag for tag in existing_tags if not tag.startswith(LLM_TAG_PREFIX)]
    all_tags = kept_tags + [tag for tag in llm_tags if tag not in kept_tags]
    new_frontmatter = clean_frontmatter
    if all_tags:
        new_frontmatter += "\ntags:\n" + "\n".join(
            f"  - {tag}" for tag in all_tags
        )
    return f"---\n{new_frontmatter}\n---\n{body.lstrip()}"


def api_request(
    api_url: str,
    api_key: str,
    model: str,
    article: str,
    response_format: str,
    thinking: str,
    reasoning_effort: str,
    timeout: int,
    retries: int,
) -> list[str]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Here is the complete Markdown article:\n\n" + article,
            },
        ],
        "response_format": {"type": response_format},
    }
    if thinking == "enabled":
        payload["thinking"] = {"type": "enabled"}
        payload["reasoning_effort"] = reasoning_effort
    else:
        payload["thinking"] = {"type": "disabled"}
        payload["temperature"] = 0.2
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            content = response_data["choices"][0]["message"]["content"]
            result = json.loads(content)
            return normalize_tags(result.get("tags"))
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"LLM request failed after retries: {last_error}") from last_error


def cache_path(cache_root: Path, article_path: Path) -> Path:
    return cache_root / f"{article_path.stem}.json"


def load_cached_tags(path: Path, digest: str, model: str) -> list[str] | None:
    if not path.is_file():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        cached.get("content_sha256") == digest
        and cached.get("model") == model
        and cached.get("prompt_version") == PROMPT_VERSION
    ):
        try:
            return normalize_tags(cached.get("tags"))
        except ValueError:
            return None
    return None


def save_cache(path: Path, article_path: Path, digest: str, model: str, tags: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_path": article_path.as_posix(),
        "content_sha256": digest,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "tags": tags,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", type=Path, default=DEFAULT_ARTICLES)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--dotenv", type=Path, default=Path(".env"))
    parser.add_argument("--api-url")
    parser.add_argument("--api-key")
    parser.add_argument("--model")
    parser.add_argument("--response-format", choices=("json_object",), default="json_object")
    parser.add_argument("--thinking", choices=("enabled", "disabled"))
    parser.add_argument("--reasoning-effort", choices=("high", "max"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--slug", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    load_dotenv(args.dotenv)
    api_url = args.api_url or os.environ.get("DEEPSEEK_API_URL", DEFAULT_API_URL)
    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    model = args.model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
    thinking = args.thinking or os.environ.get("DEEPSEEK_THINKING", "enabled")
    reasoning_effort = args.reasoning_effort or os.environ.get(
        "DEEPSEEK_REASONING_EFFORT", "high"
    )

    article_paths = sorted(args.articles.glob("*.md"))
    if args.slug:
        requested = set(args.slug)
        article_paths = [path for path in article_paths if path.stem in requested]
    if args.limit > 0:
        article_paths = article_paths[: args.limit]
    if not article_paths:
        print(f"No Markdown articles found in {args.articles}", file=sys.stderr)
        return 2

    if not args.dry_run and not api_key:
        print("Set DEEPSEEK_API_KEY in .env or pass --api-key.", file=sys.stderr)
        return 2

    print(f"Articles selected: {len(article_paths)}")
    for article_path in article_paths:
        text = article_path.read_text(encoding="utf-8")
        digest = content_hash(text)
        cached_path = cache_path(args.cache, article_path)
        tags = None if args.force else load_cached_tags(cached_path, digest, model)
        source = "cache"
        if tags is None:
            if args.dry_run:
                print(f"DRY-RUN {article_path}")
                continue
            tags = api_request(
                api_url,
                api_key,
                model,
                text,
                args.response_format,
                thinking,
                reasoning_effort,
                args.timeout,
                args.retries,
            )
            save_cache(cached_path, article_path, digest, model, tags)
            source = "api"
        article_path.write_text(write_tags(text, tags), encoding="utf-8")
        print(f"{source}: {article_path.name} -> {', '.join(tags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
