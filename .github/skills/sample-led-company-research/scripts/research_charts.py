"""Small, native Matplotlib helpers for research figures; no chart schema.

Use ChartTheme.figure(), add ordinary Matplotlib axes, then export().  Export
checks glyphs and canvas bounds, but requires separate visual review of the PNG
at its intended insertion size. Labels use plain Unicode (math parsing is off).
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import warnings

import numpy as np
from fontTools.ttLib import TTCollection, TTFont, TTLibError
from matplotlib import font_manager, ft2font, rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.table import Table
from matplotlib.text import Text


_STYLE = Path(__file__).resolve().parent.parent / "assets/research-chart-style.json"
_SC_NAME = re.compile(
    r"^(PingFangSC-|NotoSansCJKsc-|NotoSansSC-|SourceHanSansSC-|"
    r"SourceHanSansCN-|MicrosoftYaHei(?:$|-))"
)
_FONT_HELP = (
    "No verified Simplified Chinese font face found. Install Noto Sans CJK SC "
    "or Source Han Sans SC, or pass font_path pointing to a PingFang SC / "
    "Microsoft YaHei font (TTF, OTF or TTC). For another independently verified "
    "SC face, pass font_path and font_verification with its exact postscript_name, "
    "source_sha256 and verification_note. A family name or glyph coverage alone "
    "does not verify Simplified Chinese typography."
)


def _sha(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


@lru_cache(maxsize=1024)
def _font_faces(path, source_sha=None):
    """Inspect all collection faces; source_sha binds the cache to verified bytes."""
    with open(path, "rb") as handle:
        collection = handle.read(4) == b"ttcf"
    owner = TTCollection(path, lazy=True) if collection else TTFont(path, lazy=True)
    fonts = owner.fonts if collection else [owner]
    try:
        faces = []
        for i, font in enumerate(fonts):
            name = font["name"].getDebugName(6) or ""
            # Decode glyph tables only for default candidates or a verified file.
            chinese = (bool(_SC_NAME.match(name)) or source_sha is not None) and set(
                map(ord, "简体中文")
            ).issubset(font.getBestCmap() or {})
            faces.append((i, name, collection, chinese))
        return tuple(faces)
    finally:
        owner.close()


@lru_cache(maxsize=1)
def _system_fonts():
    return tuple(sorted(font_manager.findSystemFonts()))


def _select_font(work_dir, preferences, explicit=None, verification=None):
    if verification is not None:
        fields = ("postscript_name", "source_sha256", "verification_note")
        if (not explicit or not isinstance(verification, dict) or
                any(not isinstance(verification.get(key), str) or
                    not verification[key].strip() for key in fields) or
                not re.fullmatch(r"[0-9a-fA-F]{64}", verification["source_sha256"])):
            raise ValueError("font_verification requires font_path, an exact postscript_name, "
                             "a full source_sha256 and an independent SC verification_note")
        verification = {key: verification[key] for key in fields}
        verification["source_sha256"] = verification["source_sha256"].lower()
        if _sha(Path(explicit).expanduser().resolve()) != verification["source_sha256"]:
            raise ValueError("Font verification source_sha256 mismatch")
    candidates = []
    paths = [str(Path(explicit).expanduser().resolve())] if explicit else _system_fonts()
    for path in paths:
        try:
            # Bind cached metadata to the verified bytes, even if a path is reused.
            fingerprint = verification["source_sha256"] if verification else None
            for index, name, collection, chinese in _font_faces(path, fingerprint):
                accepted = (name == verification["postscript_name"] if verification
                            else bool(_SC_NAME.match(name)))
                if chinese and accepted:
                    rank = preferences.index(name) if name in preferences else len(preferences)
                    candidates.append((rank, name, path, index, collection))
        except (OSError, KeyError, ValueError, TTLibError):
            if explicit:
                raise ValueError(f"Cannot inspect font: {path}. {_FONT_HELP}") from None
    if not candidates:
        if verification:
            raise ValueError("Font verification postscript_name mismatch or required SC glyphs missing")
        raise ValueError(_FONT_HELP)
    _, name, source, index, collection = min(candidates)
    source_sha = _sha(source)
    if verification and source_sha != verification["source_sha256"]:
        raise ValueError("Font verification source_sha256 mismatch")
    selected = Path(source)
    if collection:
        font = TTFont(source, fontNumber=index, recalcTimestamp=False)
        try:
            suffix = ".otf" if font.sfntVersion == "OTTO" else ".ttf"
            cache = Path(work_dir) / "font-cache"
            cache.mkdir(parents=True, exist_ok=True)
            selected = cache / f"{source_sha[:20]}-{name}{suffix}"
            if not selected.exists():
                fd, temporary = tempfile.mkstemp(dir=cache, suffix=suffix)
                os.close(fd)
                try:
                    font.save(temporary)
                    os.replace(temporary, selected)
                finally:
                    Path(temporary).unlink(missing_ok=True)
        finally:
            font.close()
    actual = ft2font.FT2Font(str(selected))
    if actual.postscript_name != name:
        raise ValueError(f"Selected font identity mismatch: {actual.postscript_name!r} != {name!r}")
    identity = {
        "postscript_name": name, "source_path": source, "source_face_index": index,
        "source_sha256": source_sha, "path": str(selected), "sha256": _sha(selected),
    }
    if verification:
        identity["verification"] = verification
    return selected, identity


def _texts(fig):
    # Matplotlib table cells do not expose their Text through get_children().
    texts = list(fig.findobj(Text))
    for table in fig.findobj(Table):
        texts.extend(cell.get_text() for cell in table.get_celld().values())
    return list(dict.fromkeys(texts))


def _render(callback, *args, **kwargs):
    # A future artist missed by traversal must not silently render tofu.
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message=r"Glyph .* missing from font", category=UserWarning)
        try:
            return callback(*args, **kwargs)
        except UserWarning as exc:
            raise ValueError(f"Renderer font/glyph check failed: {exc}") from exc


def _drawn_texts(fig):
    """Record Text.draw calls, excluding unused out-of-range tick artists."""
    drawn, restore = [], []
    for artist in _texts(fig):
        original = artist.draw
        restore.append((artist, artist.__dict__.get("draw"), "draw" in artist.__dict__))

        def draw(renderer, *args, _artist=artist, _draw=original, **kwargs):
            result = _draw(renderer, *args, **kwargs)
            if _artist.get_visible() and _artist.get_text().strip():
                drawn.append(_artist)
            return result

        artist.draw = draw
    try:
        _render(fig.canvas.draw)
    finally:
        for artist, previous, existed in restore:
            if existed:
                artist.draw = previous
            else:
                del artist.draw
    return drawn


class ChartTheme:
    """A theme, a verified SC font, and explicit export checks.

    work_dir is a caller-owned rebuildable directory for an extracted TTC face.
    Attributes colors / font_sizes and normal Matplotlib remain freely usable.

    For a face outside the built-in SC families, supply font_path plus
    font_verification: a dict with exact postscript_name, full source_sha256,
    and verification_note citing independent evidence of SC typography. This
    records caller-supplied evidence; glyph checks and PNG review still apply.
    """

    def __init__(self, work_dir, style_path=None, font_path=None, font_verification=None):
        self.style = json.loads(Path(style_path or _STYLE).read_text(encoding="utf-8"))
        self.colors, self.font_sizes = self.style["colors"], self.style["font_sizes"]
        self.font_path, self.font_identity = _select_font(
            work_dir, self.style["font_preferences"], font_path, font_verification
        )
        self._cmap = ft2font.FT2Font(str(self.font_path)).get_charmap()

    def _font(self, size):
        return FontProperties(fname=str(self.font_path), size=size)

    def figure(self, title, subtitle="", figsize=None):
        config = self.style["figure"]
        fig = Figure(figsize=figsize or (config["width_inches"], config["height_inches"]),
                     dpi=config["dpi"], facecolor="white")
        FigureCanvasAgg(fig)
        fig.subplots_adjust(**{key: config[key] for key in ("left", "right", "top", "bottom")})
        fig.text(config["left"], .97, title, va="top", color=self.colors["text"],
                 fontproperties=self._font(self.font_sizes["title"]))
        if subtitle:
            fig.text(config["left"], .91, subtitle, va="top", color=self.colors["muted"],
                     fontproperties=self._font(self.font_sizes["subtitle"]))
        return fig

    def footer(self, fig, text):
        return fig.text(self.style["figure"]["left"], .025, text, va="bottom",
                        color=self.colors["muted"], linespacing=1.5,
                        fontproperties=self._font(self.font_sizes["footnote"]))

    def axes(self, ax, grid="y"):
        if grid not in (None, "x", "y", "both"):
            raise ValueError("grid must be None, 'x', 'y' or 'both'")
        ax.set_facecolor("white")
        ax.set_axisbelow(True)
        ax.grid(False)
        if grid:
            ax.grid(True, axis=grid, color=self.colors["grid"], linewidth=.6)
        for side, spine in ax.spines.items():
            spine.set_visible(side in ("left", "bottom"))
            spine.set_color(self.colors["grid"])
        ax.tick_params(colors=self.colors["muted"], labelsize=self.font_sizes["tick"], length=0)
        for label in (ax.xaxis.label, ax.yaxis.label):
            label.set_color(self.colors["muted"])
            label.set_fontsize(self.font_sizes["body"])
        ax.set_prop_cycle(color=[self.colors[key] for key in
                                ("blue", "teal", "orange", "purple", "negative", "gray")])
        return ax

    def _pin_and_check(self, fig):
        texts, used = [], set()
        for artist in _texts(fig):
            if not artist.get_visible():
                continue
            if artist.get_usetex() and artist.get_text():
                raise ValueError("TeX text cannot use the verified font; use plain Unicode labels.")
            artist.set_parse_math(False)
            props = artist.get_fontproperties().copy()
            props.set_file(str(self.font_path))
            artist.set_fontproperties(props)
            # Empty tick artists gain categorical labels during the first draw.
            # Pin them now so newly populated/copied ticks inherit this face.
            if not artist.get_text():
                continue
            texts.append(artist)
            used.update(ord(char) for char in artist.get_text() if char != "\n")
        missing = used.difference(self._cmap)
        if missing:
            readable = ", ".join(f"{chr(code)!r} U+{code:04X}" for code in sorted(missing))
            raise ValueError(f"Missing glyphs in {self.font_identity['postscript_name']}: {readable}")
        return {"status": "pass", "text_count": len(texts), "unique_glyphs": len(used)}

    def export(self, fig, path, formats=("png",), replace=False):
        """Render, check, atomically publish requested files, return an audit dict.

        Bounds checks reject canvas clipping, not text-to-text collisions. A
        successful audit is not evidence of visual legibility; review the PNG.
        Existing targets require explicit replace=True. No sidecars are written.
        """
        formats = tuple(dict.fromkeys(fmt.lower() for fmt in formats))
        if not formats or any(fmt not in ("png", "svg", "pdf") for fmt in formats):
            raise ValueError("Request at least one of png, svg, pdf")
        base = Path(path)
        if base.suffix.lower() in (".png", ".svg", ".pdf"):
            base = base.with_suffix("")
        outputs = {fmt: Path(f"{base}.{fmt}") for fmt in formats}
        for target in outputs.values():
            if target.exists() and not replace:
                raise FileExistsError(f"Refusing to replace {target}; pass replace=True explicitly")
        self._pin_and_check(fig)
        _render(fig.canvas.draw)  # Materialize automatic tick labels before pinning again.
        glyphs = self._pin_and_check(fig)
        texts = _drawn_texts(fig)
        renderer, canvas = fig.canvas.get_renderer(), fig.bbox
        clipped = []
        for artist in texts:
            box = artist.get_window_extent(renderer)
            if np.isfinite(box.extents).all() and (
                box.x0 < canvas.x0 - 1 or box.y0 < canvas.y0 - 1 or
                box.x1 > canvas.x1 + 1 or box.y1 > canvas.y1 + 1
            ):
                clipped.append(artist.get_text())
        if clipped:
            raise ValueError(f"Text clips the canvas; adjust layout: {clipped!r}")
        pending = []
        try:
            for fmt, target in outputs.items():
                target.parent.mkdir(parents=True, exist_ok=True)
                fd, temporary = tempfile.mkstemp(dir=target.parent, suffix=f".{fmt}")
                os.close(fd)
                pending.append((Path(temporary), target))
                with rc_context({"svg.fonttype": "path", "pdf.fonttype": 42,
                                 "text.usetex": False, "savefig.bbox": None}):
                    _render(fig.savefig, temporary, format=fmt, dpi=fig.dpi,
                            facecolor=fig.get_facecolor())
            for temporary, target in pending:
                if replace:
                    os.replace(temporary, target)
                else:
                    os.link(temporary, target)  # Atomic publication without an overwrite race.
                    temporary.unlink()
        finally:
            for temporary, _ in pending:
                temporary.unlink(missing_ok=True)
        return {
            "font": dict(self.font_identity), "glyphs": glyphs,
            "bounds": {"status": "pass", "drawn_text_count": len(texts), "tolerance_px": 1},
            "visual_review": "required",
            "outputs": {fmt: {"path": str(target), "sha256": _sha(target)}
                        for fmt, target in outputs.items()},
        }


def label_bars(ax, container, fmt="{:,.1f}", padding=3, **kwargs):
    """Return native bar-label annotations; non-finite values remain unlabeled."""
    labels = [fmt.format(value) if np.isfinite(value) else "" for value in container.datavalues]
    return ax.bar_label(container, labels=labels, padding=padding, **kwargs)


def label_points(ax, x, y, fmt="{:,.1f}", offsets=None, **kwargs):
    """Label finite points. offsets may be an index->(dx,dy) mapping or sequence."""
    x, y = list(x), list(y)
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    labels = []
    for index, (xi, yi) in enumerate(zip(x, y)):
        if not np.isfinite(yi):
            continue
        offset = ((0, 5) if offsets is None else
                  offsets.get(index, (0, 5)) if hasattr(offsets, "get") else offsets[index])
        options = {"ha": "center", "va": "bottom", **kwargs}
        labels.append(ax.annotate(fmt.format(yi), (xi, yi), xytext=offset,
                                  textcoords="offset points", **options))
    return labels


def stacked_bars(ax, x, components, colors=None, **kwargs):
    """Signed stacks. Incomplete periods omit ALL components, never zero-fill.

    Returns containers (label->BarContainer), complete_mask and missing_mask.
    Use the exposed masks to annotate/report missing periods in the figure.
    colors may be a label->color mapping or a sequence in component order.
    """
    x = list(x)
    values = {label: np.asarray(series, dtype=float) for label, series in components.items()}
    if not values or any(array.shape != (len(x),) for array in values.values()):
        raise ValueError("Each component must be a 1D series with len(x) entries")
    complete = np.all(np.isfinite(np.stack(list(values.values()))), axis=0)
    positive, negative = np.zeros(len(x)), np.zeros(len(x))
    containers = {}
    for index, (label, array) in enumerate(values.items()):
        series = np.where(complete, array, np.nan)
        bottom = np.where(series >= 0, positive, negative)
        options = dict(kwargs)
        if colors is not None:
            options["color"] = colors[label] if hasattr(colors, "keys") else colors[index]
        containers[label] = ax.bar(x, series, bottom=bottom, label=label, **options)
        positive += np.where(complete & (array >= 0), array, 0)
        negative += np.where(complete & (array < 0), array, 0)
    return {"containers": containers, "complete_mask": complete, "missing_mask": ~complete}
