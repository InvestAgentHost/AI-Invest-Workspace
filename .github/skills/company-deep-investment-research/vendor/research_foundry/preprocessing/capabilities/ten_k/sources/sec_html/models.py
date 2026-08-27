from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Classification(str, Enum):
    SEC_NATIVE_HTML = "SEC_NATIVE_HTML"
    SEC_NATIVE_TEXT_ONLY = "SEC_NATIVE_TEXT_ONLY"
    SEC_NATIVE_XML = "SEC_NATIVE_XML"
    SEC_PDF_FALLBACK = "SEC_PDF_FALLBACK"
    NON_SEC_PDF = "NON_SEC_PDF"
    UNKNOWN_OR_UNSUPPORTED = "UNKNOWN_OR_UNSUPPORTED"


@dataclass
class SecUrls:
    cik: str
    accession: str
    accession_compact: str
    base_url: str
    index_json_url: str
    text_url: str
    index_html_url: str


@dataclass
class SecReference:
    cik: str | None = None
    accession: str | None = None
    accession_compact: str | None = None
    filename: str | None = None
    source_url: str | None = None
    local_path: str | None = None
    urls: SecUrls | None = None


@dataclass
class ManifestDocument:
    filename: str
    type: str = ""
    sequence: str = ""
    description: str = ""
    size: int | None = None
    url: str | None = None
    category: str = "unknown"
    is_primary_candidate: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FilingManifest:
    cik: str | None = None
    accession: str | None = None
    base_url: str | None = None
    source: str = ""
    documents: list[ManifestDocument] = field(default_factory=list)
    header: dict[str, str] = field(default_factory=dict)

    @property
    def assets(self) -> list[ManifestDocument]:
        return [doc for doc in self.documents if doc.category == "image"]

    def primary_document(self) -> ManifestDocument | None:
        candidates = [doc for doc in self.documents if doc.is_primary_candidate]
        if candidates:
            return sorted(candidates, key=_primary_sort_key)[0]
        non_assets = [doc for doc in self.documents if doc.category in {"html", "xml", "pdf", "text"}]
        return sorted(non_assets, key=_primary_sort_key)[0] if non_assets else None


@dataclass
class ClassificationResult:
    classification: Classification
    input: str
    reason: str
    recommended_pipeline: str
    reference: SecReference | None = None
    manifest: FilingManifest | None = None
    primary_document: ManifestDocument | None = None
    assets: list[ManifestDocument] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["classification"] = self.classification.value
        return data


def _primary_sort_key(doc: ManifestDocument) -> tuple[int, int, str]:
    category_rank = {"html": 0, "xml": 1, "pdf": 2, "text": 3}.get(doc.category, 9)
    try:
        sequence_rank = int(doc.sequence) if doc.sequence else 9999
    except ValueError:
        sequence_rank = 9999
    name = doc.filename.lower()
    index_penalty = 10 if "-index" in name or "index-headers" in name else 0
    return (category_rank + index_penalty, sequence_rank, name)
