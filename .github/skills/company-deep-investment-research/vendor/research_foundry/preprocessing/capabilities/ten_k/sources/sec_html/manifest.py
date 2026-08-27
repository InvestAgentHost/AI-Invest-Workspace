from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import urljoin

from .models import FilingManifest, ManifestDocument

DOCUMENT_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.IGNORECASE | re.DOTALL)
TAG_LINE_RE = re.compile(r"<(?P<tag>[A-Z0-9-]+)>\s*(?P<value>[^\r\n<]*)", re.IGNORECASE)
HEADER_RE = re.compile(r"<SEC-HEADER>(.*?)</SEC-HEADER>", re.IGNORECASE | re.DOTALL)
HEADER_LINE_RE = re.compile(r"^\s*([A-Z0-9][A-Z0-9 -]+):\s*(.*?)\s*$")

INDEX_FILENAMES = ("-index.htm", "-index.html", "-index-headers.html", "index.json")
HTML_EXTS = (".htm", ".html")
XML_EXTS = (".xml", ".xsd")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
PDF_EXTS = (".pdf",)
TEXT_EXTS = (".txt",)


def parse_index_json(raw: str | dict, base_url: str | None = None, cik: str | None = None, accession: str | None = None) -> FilingManifest:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    directory = payload.get("directory", {}) if isinstance(payload, dict) else {}
    items = directory.get("item", []) or []
    manifest = FilingManifest(cik=cik, accession=accession, base_url=base_url, source="index.json")
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        doc = ManifestDocument(
            filename=name,
            type=str(item.get("type", "") or ""),
            size=_to_int(item.get("size")),
            url=urljoin(base_url or "", name) if base_url else None,
            category=categorize_filename(name, item.get("type", "")),
            metadata={"last_modified": item.get("last-modified") or item.get("last_modified")},
        )
        doc.is_primary_candidate = is_primary_candidate(doc)
        manifest.documents.append(doc)
    return manifest


def parse_submission_text(raw: str, base_url: str | None = None, cik: str | None = None, accession: str | None = None) -> FilingManifest:
    manifest = FilingManifest(cik=cik, accession=accession, base_url=base_url, source="submission_text")
    manifest.header = parse_sec_header(raw)
    for chunk in DOCUMENT_RE.findall(raw):
        fields = _parse_document_fields(chunk)
        filename = fields.get("FILENAME", "").strip()
        if not filename:
            continue
        doc = ManifestDocument(
            filename=filename,
            type=fields.get("TYPE", ""),
            sequence=fields.get("SEQUENCE", ""),
            description=fields.get("DESCRIPTION", ""),
            url=urljoin(base_url or "", filename) if base_url else None,
            category=categorize_filename(filename, fields.get("TYPE", "")),
            metadata={"raw_tags": fields},
        )
        doc.is_primary_candidate = is_primary_candidate(doc)
        manifest.documents.append(doc)
    return manifest


def parse_sec_header(raw: str) -> dict[str, str]:
    match = HEADER_RE.search(raw)
    if not match:
        return {}
    header: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line_match = HEADER_LINE_RE.match(line)
        if line_match:
            key = " ".join(line_match.group(1).lower().split())
            header[key] = line_match.group(2).strip()
    return header


def categorize_filename(filename: str, declared_type: object = "") -> str:
    name = filename.lower()
    doc_type = str(declared_type or "").strip().upper()
    if name.endswith(IMAGE_EXTS) or doc_type == "GRAPHIC":
        return "image"
    if name.endswith(HTML_EXTS):
        return "html"
    if name.endswith(XML_EXTS) or doc_type in {"XML", "INFORMATION TABLE", "PRIMARY_DOC_XML"}:
        return "xml"
    if name.endswith(PDF_EXTS):
        return "pdf"
    if name.endswith(TEXT_EXTS):
        return "text"
    return "unknown"


def is_primary_candidate(doc: ManifestDocument) -> bool:
    name = doc.filename.lower()
    doc_type = doc.type.upper().strip()
    if doc.category == "image" or doc_type == "GRAPHIC":
        return False
    if any(marker in name for marker in INDEX_FILENAMES):
        return False
    if name.endswith(".xsd"):
        return False
    if doc.category in {"html", "xml", "pdf", "text"}:
        return True
    return False


def merge_manifest(primary: FilingManifest, fallback: FilingManifest) -> FilingManifest:
    existing = {doc.filename.lower(): doc for doc in primary.documents}
    for doc in fallback.documents:
        key = doc.filename.lower()
        if key not in existing:
            primary.documents.append(doc)
            existing[key] = doc
            continue
        target = existing[key]
        if doc.sequence and not target.sequence:
            target.sequence = doc.sequence
        if doc.type and (not target.type or target.type.endswith(".gif")):
            target.type = doc.type
        if doc.description and not target.description:
            target.description = doc.description
        if doc.category != "unknown":
            target.category = doc.category
        target.is_primary_candidate = is_primary_candidate(target)
        target.metadata.setdefault("submission_text_tags", doc.metadata.get("raw_tags", {}))
    primary.header.update({key: value for key, value in fallback.header.items() if key not in primary.header})
    return primary


def manifest_to_dict(manifest: FilingManifest) -> dict:
    primary = manifest.primary_document()
    return {
        "cik": manifest.cik,
        "accession": manifest.accession,
        "base_url": manifest.base_url,
        "source": manifest.source,
        "header": manifest.header,
        "documents": [doc.__dict__ for doc in manifest.documents],
        "primary_document": primary.__dict__ if primary else None,
        "assets": [doc.__dict__ for doc in manifest.assets],
    }


def _parse_document_fields(chunk: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in TAG_LINE_RE.finditer(chunk):
        tag = match.group("tag").upper()
        if tag == "TEXT":
            continue
        fields[tag] = unescape(match.group("value").strip())
    return fields


def _to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None
