#!/usr/bin/env python3
"""Read a DOCX reference without executing fields, macros, links or embedded content.

Default: compact structural JSON. --paragraph-range START:END additionally returns
selected top-level body paragraphs (1-based, inclusive, including empty ones).
--extract-images OUTPUT_DIR exports embedded main-body DrawingML raster pictures
and an index of their placement. It does not render pages or read image text.
Uses only Python's standard library and never modifies the source file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
W = "{" + NS["w"] + "}"
WP = "{" + NS["wp"] + "}"
EMBED = "{" + NS["r"] + "}embed"
EMUS_PER_INCH = 914400


def paragraph_text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.iter(W + "t"))


def clipped_text(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= 180 else text[:179] + "…"


def paragraph_pictures(paragraph: ET.Element) -> Iterator[tuple[ET.Element, str]]:
    """Yield a drawing frame and image relationship within this paragraph."""
    for element in paragraph:
        if element.tag == W + "drawing":
            for frame in element:
                if frame.tag not in {WP + "inline", WP + "anchor"}:
                    continue
                for blip in frame.findall(".//pic:pic/pic:blipFill/a:blip", NS):
                    yield frame, blip.get(EMBED, "")
        elif element.tag not in {W + "p", W + "object"}:
            yield from paragraph_pictures(element)


def media_relationships(archive: ZipFile) -> dict[str, str]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in archive.namelist():
        return {}
    result = {}
    for rel in ET.fromstring(archive.read(rels_path)).findall("rel:Relationship", NS):
        if rel.get("TargetMode", "Internal") != "Internal" or rel.get("Type") != NS["r"] + "/image":
            continue
        target = rel.get("Target", "")
        if target.startswith("media/"):
            member = "word/" + target
        elif target.startswith("/word/media/"):
            member = target[1:]
        else:
            continue
        if any(piece in {"", ".", ".."} for piece in member.split("/")) or any(c in member for c in "\\?#"):
            continue
        relationship_id = rel.get("Id")
        if relationship_id:
            result[relationship_id] = member
    return result


def raster_suffix(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if header.startswith((b"II*\0", b"MM\0*")):
        return ".tiff"
    if header.startswith(b"BM"):
        return ".bmp"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"
    return None


def copy_image(archive: ZipFile, member: str, output_dir: Path, number: int) -> str | None:
    with archive.open(member) as source:
        header = source.read(12)
        extension = raster_suffix(header)
        if extension is None:
            return None
        filename = f"image-{number:03d}{extension}"
        with (output_dir / filename).open("xb") as destination:
            destination.write(header)
            shutil.copyfileobj(source, destination)
        return filename


def picture_size(frame: ET.Element) -> dict | None:
    extent = frame.find("wp:extent", NS)
    if extent is None:
        return None
    cx, cy = extent.get("cx", ""), extent.get("cy", "")
    if not cx.isdecimal() or not cy.isdecimal() or int(cx) == 0 or int(cy) == 0:
        return None
    return {
        "width_in": round(int(cx) / EMUS_PER_INCH, 3),
        "height_in": round(int(cy) / EMUS_PER_INCH, 3),
    }


def export_images(archive: ZipFile, body: ET.Element, report: dict, output_dir: Path) -> dict:
    relations = media_relationships(archive)
    members = set(archive.namelist())
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ValueError(f"image output directory must be empty: {output_dir}")

    top_paragraphs = {p: i for i, p in enumerate(body.findall("w:p", NS), 1)}
    heading_by_number = {
        row["paragraph"]: (row["level"], clipped_text(row["text"])) for row in report["headings"]
    }
    body_paragraphs = list(body.iter(W + "p"))
    snippets = [clipped_text(paragraph_text(p)) for p in body_paragraphs]
    headings = []
    heading_contexts = []
    for paragraph in body_paragraphs:
        entry = heading_by_number.get(top_paragraphs.get(paragraph))
        if entry:
            level, title = entry
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, title))
        heading_contexts.append([title for _, title in headings])

    files: dict[str, str | None] = {}
    placements = []
    skipped = 0
    for i, paragraph in enumerate(body_paragraphs):
        for frame, relationship in paragraph_pictures(paragraph):
            member = relations.get(relationship)
            if member is None or member not in members:
                skipped += 1
                continue
            if member not in files:
                files[member] = copy_image(archive, member, output_dir, len(files) + 1)
            filename = files[member]
            if filename is None:
                skipped += 1
                continue
            prior = next((text for text in reversed(snippets[:i]) if text), None)
            following = next((text for text in snippets[i + 1:] if text), None)
            placement = {
                "file": filename,
                "source_media": PurePosixPath(member).name,
                "paragraph": top_paragraphs.get(paragraph),
                "body_paragraph": i + 1,
                "heading_path": heading_contexts[i],
                "paragraph_text": snippets[i] or None,
                "previous_text": prior,
                "following_text": following,
                "word_inserted_size": picture_size(frame),
            }
            properties = frame.find("wp:docPr", NS)
            if properties is not None and (title := properties.get("title") or properties.get("descr")):
                placement["alt_text"] = clipped_text(title)
            placements.append(placement)
    index = {
        "file": report["file"],
        "sha256": report["sha256"],
        "image_file_count": sum(filename is not None for filename in files.values()),
        "placement_count": len(placements),
        "skipped_picture_count": skipped,
        "limitations": (
            "Main-body DrawingML raster pictures only. Top-level paragraph numbers match --paragraph-range; "
            "body_paragraph also counts nested paragraphs. Sizes come from Word drawing extents, "
            "not rendered pages. No OCR, external links, embedded objects or layout validation."
        ),
        "images": placements,
    }
    index_path = output_dir / "index.json"
    with index_path.open("x", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {key: index[key] for key in ("image_file_count", "placement_count", "skipped_picture_count")} | {
        "index": str(index_path)
    }


def inspect_docx(
    path: Path, paragraph_range: tuple[int, int] | None = None, extract_images: Path | None = None
) -> dict:
    raw = path.read_bytes()
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        styles = {}
        if "word/styles.xml" in archive.namelist():
            style_root = ET.fromstring(archive.read("word/styles.xml"))
            for style in style_root.findall("w:style", NS):
                name = style.find("w:name", NS)
                base = style.find("w:basedOn", NS)
                level = style.find("w:pPr/w:outlineLvl", NS)
                styles[style.get(W + "styleId", "")] = {
                    "name": name.get(W + "val", "") if name is not None else "",
                    "base": base.get(W + "val", "") if base is not None else "",
                    "outline": level.get(W + "val") if level is not None else None,
                }

        def heading_level(style_id: str, direct: ET.Element | None) -> int | None:
            if direct is not None:
                value = direct.get(W + "val")
                return int(value) + 1 if value is not None and value.isdigit() and int(value) < 9 else None
            seen = set()
            while style_id and style_id not in seen:
                seen.add(style_id)
                style = styles.get(style_id, {})
                value = style.get("outline")
                if value is not None:
                    return int(value) + 1 if value.isdigit() and int(value) < 9 else None
                match = re.fullmatch(r"(?:heading|标题)\s*([1-9])", style.get("name", ""), re.I)
                if match:
                    return int(match.group(1))
                style_id = style.get("base", "")
            return None

        body = root.find("w:body", NS)
        if body is None:
            raise ValueError("DOCX has no document body")
        paragraphs = body.findall("w:p", NS)
        headings = []
        selected = []
        for number, p in enumerate(paragraphs, 1):
            text = paragraph_text(p)
            style_node = p.find("w:pPr/w:pStyle", NS)
            style_id = style_node.get(W + "val", "") if style_node is not None else ""
            level = heading_level(style_id, p.find("w:pPr/w:outlineLvl", NS))
            record = {"paragraph": number, "text": text, "style": styles.get(style_id, {}).get("name", style_id)}
            if level is not None and text.strip():
                headings.append({"level": level, **record})
            if paragraph_range and paragraph_range[0] <= number <= paragraph_range[1]:
                selected.append(record)
        if paragraph_range and paragraph_range[1] > len(paragraphs):
            raise ValueError(f"Paragraph range exceeds document length ({len(paragraphs)})")
        result = {
            "file": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "body_paragraph_count": len(paragraphs),
            "table_count": len(body.findall(".//w:tbl", NS)),
            "drawing_count": len(body.findall(".//w:drawing", NS)),
            "media_file_count": sum(n.startswith("word/media/") and not n.endswith("/") for n in archive.namelist()),
            "headings": headings,
            "limitations": "Style-derived headings only; no image OCR, fields, table contents, page layout or factual validation. Paragraphs are 1-based top-level body paragraphs, including empty ones, not page numbers.",
        }
        if paragraph_range:
            result["paragraphs"] = selected
        if extract_images is not None:
            result["image_extraction"] = export_images(archive, body, result, extract_images)
        return result


def parse_range(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+):(\d+)", value)
    if not match or not 1 <= int(match.group(1)) <= int(match.group(2)):
        raise argparse.ArgumentTypeError("Use an inclusive 1-based range such as 1:40")
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--paragraph-range", type=parse_range)
    parser.add_argument(
        "--extract-images", type=Path, metavar="OUTPUT_DIR",
        help="export embedded body raster pictures and index.json to a new or empty directory",
    )
    args = parser.parse_args()
    try:
        result = inspect_docx(args.docx, args.paragraph_range, args.extract_images)
    except (OSError, ValueError, KeyError, BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
