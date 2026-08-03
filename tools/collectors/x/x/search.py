from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .config import ProfileConfig
from .storage import SourcePaths, read_jsonl, utc_now


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS posts (
    profile TEXT NOT NULL,
    id TEXT NOT NULL,
    author_id TEXT,
    author_handle TEXT,
    author_name TEXT,
    created_at TEXT,
    text TEXT NOT NULL,
    post_type TEXT NOT NULL,
    conversation_id TEXT,
    in_reply_to_id TEXT,
    quoted_post_id TEXT,
    reposted_post_id TEXT,
    lang TEXT,
    like_count INTEGER,
    reply_count INTEGER,
    repost_count INTEGER,
    quote_count INTEGER,
    view_count INTEGER,
    url TEXT NOT NULL,
    is_target_author INTEGER NOT NULL,
    source_kind TEXT,
    content_hash TEXT,
    source_paths_json TEXT NOT NULL,
    PRIMARY KEY (profile, id)
);
CREATE INDEX IF NOT EXISTS posts_profile_created ON posts(profile, created_at);
CREATE INDEX IF NOT EXISTS posts_profile_type ON posts(profile, post_type);
CREATE INDEX IF NOT EXISTS posts_conversation ON posts(profile, conversation_id);
CREATE TABLE IF NOT EXISTS media (
    profile TEXT NOT NULL,
    media_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    position INTEGER NOT NULL,
    source_url TEXT,
    expanded_url TEXT,
    local_path TEXT,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    content_hash TEXT,
    downloaded_at TEXT,
    download_status TEXT NOT NULL,
    error TEXT,
    PRIMARY KEY (profile, post_id, media_id),
    FOREIGN KEY (profile, post_id) REFERENCES posts(profile, id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS media_post ON media(profile, post_id, position);
CREATE TABLE IF NOT EXISTS index_metadata (
    profile TEXT PRIMARY KEY,
    indexed_at TEXT NOT NULL,
    post_count INTEGER NOT NULL,
    media_count INTEGER NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
    profile UNINDEXED,
    id UNINDEXED,
    text,
    author_name,
    author_handle,
    tokenize='trigram'
);
"""


POST_COLUMNS = (
    "id",
    "author_id",
    "author_handle",
    "author_name",
    "created_at",
    "text",
    "post_type",
    "conversation_id",
    "in_reply_to_id",
    "quoted_post_id",
    "reposted_post_id",
    "lang",
    "like_count",
    "reply_count",
    "repost_count",
    "quote_count",
    "view_count",
    "url",
    "is_target_author",
    "source_kind",
    "content_hash",
)


MEDIA_COLUMNS = (
    "media_id",
    "post_id",
    "media_type",
    "position",
    "source_url",
    "expanded_url",
    "local_path",
    "mime_type",
    "width",
    "height",
    "content_hash",
    "downloaded_at",
    "download_status",
    "error",
)


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def index_profile(database_path: Path, profile: ProfileConfig) -> dict[str, Any]:
    paths = SourcePaths.from_root(profile.output_dir)
    posts = read_jsonl(paths.posts_jsonl)
    media = read_jsonl(paths.media_jsonl)
    with connect(database_path) as db:
        db.execute("DELETE FROM media WHERE profile = ?", (profile.name,))
        db.execute("DELETE FROM posts WHERE profile = ?", (profile.name,))
        db.execute("DELETE FROM posts_fts WHERE profile = ?", (profile.name,))
        for post in posts:
            values = [post.get(column) for column in POST_COLUMNS]
            values[POST_COLUMNS.index("is_target_author")] = int(
                bool(post.get("is_target_author"))
            )
            db.execute(
                f"INSERT INTO posts (profile,{','.join(POST_COLUMNS)},source_paths_json) VALUES ({','.join('?' for _ in range(len(POST_COLUMNS) + 2))})",
                [
                    profile.name,
                    *values,
                    json.dumps(post.get("source_paths", []), ensure_ascii=False),
                ],
            )
            db.execute(
                "INSERT INTO posts_fts(profile,id,text,author_name,author_handle) VALUES (?,?,?,?,?)",
                (
                    profile.name,
                    post["id"],
                    post.get("text") or "",
                    post.get("author_name") or "",
                    post.get("author_handle") or "",
                ),
            )
        known_ids = {post["id"] for post in posts}
        inserted_media = 0
        for row in media:
            if row.get("post_id") not in known_ids:
                continue
            db.execute(
                f"INSERT INTO media (profile,{','.join(MEDIA_COLUMNS)}) VALUES ({','.join('?' for _ in range(len(MEDIA_COLUMNS) + 1))})",
                [profile.name, *(row.get(column) for column in MEDIA_COLUMNS)],
            )
            inserted_media += 1
        db.execute(
            "INSERT OR REPLACE INTO index_metadata(profile,indexed_at,post_count,media_count) VALUES (?,?,?,?)",
            (profile.name, utc_now(), len(posts), inserted_media),
        )
    return {
        "profile": profile.name,
        "database": str(database_path),
        "posts": len(posts),
        "media": inserted_media,
    }


def _query_terms(query: str) -> tuple[list[str], list[str]]:
    terms = [term for term in query.replace('"', " ").split() if term]
    return (
        [term for term in terms if len(term) >= 3],
        [term for term in terms if len(term) < 3],
    )


def _media_for_posts(
    db: sqlite3.Connection, profile: str, post_ids: Iterable[str]
) -> dict[str, list[dict[str, Any]]]:
    ids = list(dict.fromkeys(post_ids))
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = db.execute(
        f"SELECT * FROM media WHERE profile = ? AND post_id IN ({placeholders}) ORDER BY post_id, position",
        [profile, *ids],
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        item = dict(row)
        item.pop("profile", None)
        grouped.setdefault(item["post_id"], []).append(item)
    return grouped


def _related_posts(
    db: sqlite3.Connection, profile: str, ids: Iterable[str]
) -> dict[str, dict[str, Any]]:
    values = [value for value in dict.fromkeys(ids) if value]
    if not values:
        return {}
    placeholders = ",".join("?" for _ in values)
    rows = db.execute(
        f"SELECT * FROM posts WHERE profile = ? AND id IN ({placeholders})",
        [profile, *values],
    ).fetchall()
    return {row["id"]: _post_dict(row) for row in rows}


def _post_dict(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result.pop("profile", None)
    raw_paths = result.pop("source_paths_json", "[]")
    result["source_paths"] = json.loads(raw_paths)
    result["is_target_author"] = bool(result["is_target_author"])
    return result


def search_posts(
    database_path: Path,
    profile: str,
    query: str = "",
    top_k: int = 20,
    post_type: str | None = None,
    start: str | None = None,
    end: str | None = None,
    include_context: bool = True,
) -> list[dict[str, Any]]:
    with connect(database_path) as db:
        parameters: list[Any] = [profile]
        filters = ["p.profile = ?", "p.is_target_author = 1"]
        if post_type:
            filters.append("p.post_type = ?")
            parameters.append(post_type)
        if start:
            filters.append("p.created_at >= ?")
            parameters.append(start)
        if end:
            filters.append("p.created_at <= ?")
            parameters.append(end)
        if query.strip():
            fts_terms, short_terms = _query_terms(query)
            for term in short_terms:
                filters.append("p.text LIKE ?")
                parameters.append(f"%{term}%")
            if fts_terms:
                sql = f"""
                    SELECT p.*, bm25(posts_fts) AS rank
                    FROM posts_fts JOIN posts p
                      ON p.profile = posts_fts.profile AND p.id = posts_fts.id
                    WHERE {' AND '.join(filters)} AND posts_fts MATCH ?
                    ORDER BY rank, p.created_at DESC LIMIT ?
                """
                parameters.extend(
                    [" AND ".join(f'"{term}"' for term in fts_terms), max(1, top_k)]
                )
            else:
                sql = f"""
                    SELECT p.*, 0.0 AS rank FROM posts p
                    WHERE {' AND '.join(filters)}
                    ORDER BY p.created_at DESC LIMIT ?
                """
                parameters.append(max(1, top_k))
        else:
            sql = f"""
                SELECT p.*, 0.0 AS rank FROM posts p
                WHERE {' AND '.join(filters)}
                ORDER BY p.created_at DESC LIMIT ?
            """
            parameters.append(max(1, top_k))
        rows = db.execute(sql, parameters).fetchall()
        results = [_post_dict(row) for row in rows]
        media = _media_for_posts(db, profile, (row["id"] for row in results))
        related_ids = []
        for row in results:
            related_ids.extend(
                value
                for value in (
                    row.get("in_reply_to_id"),
                    row.get("quoted_post_id"),
                    row.get("reposted_post_id"),
                )
                if value
            )
        related = _related_posts(db, profile, related_ids) if include_context else {}
        related_media = (
            _media_for_posts(db, profile, related) if include_context else {}
        )
        for row in results:
            row["media"] = media.get(row["id"], [])
            if include_context:
                row["context"] = {}
                for label, field in (
                    ("parent", "in_reply_to_id"),
                    ("quoted", "quoted_post_id"),
                    ("reposted", "reposted_post_id"),
                ):
                    related_post = related.get(row.get(field))
                    if related_post:
                        related_post["media"] = related_media.get(
                            related_post["id"], []
                        )
                        row["context"][label] = related_post
        return results
