"""Independent raw-file audit. Does not trust collector numbers or parse its bundle.

BeautifulSoup's HTML parser is intentionally separate from filing_tables.NativeTables.
A source hash alone proves identity, not value, label, fiscal period or coverage.
"""
from __future__ import annotations

import hashlib
import math
import re
from datetime import date, timedelta
from pathlib import Path

from model_contract import ALLOWED_FORMS, TOKEN_RE, PeriodIndex, is_number, period_for, resolve_token
from provenance import EvidenceIndex, source_locator

def norm(text):
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def audit_number(text, normalization):
    """Independent exact-token parser; scale/sign transformations must be explained."""
    text = norm(text).replace("\u2212", "-")
    if text in {"—", "–", "-"}:
        if normalization.get("dash_means_zero") and normalization.get("reason"):
            return 0
        raise ValueError("A source dash has not been established as zero")
    negative = text.startswith("(") and text.endswith(")")
    core = text[1:-1].strip() if negative else text
    core = re.sub(r"^(?:US\$|S\$|HK\$|A\$|C\$|[$€£¥])\s*", "", core)
    pct = core.endswith("%")
    core = core[:-1].strip() if pct else core
    if not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", core):
        raise ValueError(f"Original cell is not a standalone number: {text!r}; use reviewed components")
    number = float(core.replace(",", ""))
    if negative: number = -number
    if pct: number /= 100
    multiplier, sign = normalization.get("multiplier", 1), normalization.get("sign", 1)
    if not is_number(multiplier) or multiplier <= 0 or sign not in (-1, 1):
        raise ValueError("Invalid normalization multiplier/sign")
    if (multiplier != 1 or sign != 1) and not normalization.get("reason"):
        raise ValueError("Scale/sign conversion needs an explanation")
    return number * multiplier * sign


class Original:
    def __init__(self, path, record, workspace):
        # Imported only for an actual audit; no parser or collector run at skill update.
        from bs4 import BeautifulSoup
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Original SHA-256 differs from recorded source")
        self.html = raw.decode("utf-8", errors="replace")
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.tables = self.soup.find_all("table")
        self.by_id = {tag["id"]: tag for tag in self.soup.find_all(attrs={"id": True})}
        self.row_cache, self.cell_cache, self.text_cache, self.grid_cache = {}, {}, {}, {}
        self.form = None
        for tag in self.soup.find_all():
            if str(tag.get("name", "")).lower() == "dei:documenttype":
                self.form = norm(tag.get_text()).upper()
                break
        if not self.form:
            match = re.search(r"<TYPE>\s*(10-[KQ](?:/A)?)\s*(?:\r?\n|<)", self.html, re.I)
            self.form = match[1].upper() if match else None
        # For non-inline-XBRL originals, the exact submission-header file is mandatory.
        if self.form is None and record.get("form_evidence"):
            evidence = record["form_evidence"]
            relative = Path(evidence["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Submission header path must be Workspace-relative")
            header_path = (workspace / relative).resolve()
            header_path.relative_to(workspace)
            header = header_path.read_bytes()
            if hashlib.sha256(header).hexdigest() != evidence.get("sha256"):
                raise ValueError("Submission header hash mismatch")
            header_text = header.decode("utf-8", errors="replace")
            if evidence.get("exact_text", "") not in header_text or not evidence.get("exact_text"):
                raise ValueError("Submission form evidence not found")
            match = re.search(r"(?:CONFORMED SUBMISSION TYPE:|<TYPE>)\s*(10-[KQ](?:/A)?)\b",
                              evidence["exact_text"], re.I)
            self.form = match[1].upper() if match else None
        if self.form not in ALLOWED_FORMS or self.form != record["filing_type"]:
            raise ValueError("Native original/submission header does not establish declared 10-K/10-Q")

    def rows(self, table_index):
        if not isinstance(table_index, int) or table_index < 0:
            raise ValueError("Physical table index must be a nonnegative integer")
        if table_index in self.row_cache:
            return self.row_cache[table_index]
        table = self.tables[table_index]
        if table.find("table"):
            raise ValueError("Nested wrapper table is not a financial leaf table")
        self.row_cache[table_index] = [r for r in table.find_all("tr") if r.find_parent("table") is table]
        return self.row_cache[table_index]

    def cells(self, ti, ri):
        if not isinstance(ri, int) or ri < 0:
            raise ValueError("Physical row index must be a nonnegative integer")
        if (ti, ri) in self.cell_cache:
            return self.cell_cache[ti, ri]
        row = self.rows(ti)[ri]
        self.cell_cache[ti, ri] = [c for c in row.find_all(["td", "th"]) if c.find_parent("tr") is row]
        return self.cell_cache[ti, ri]

    def cell(self, ti, ri, ci):
        if not isinstance(ci, int) or ci < 0:
            raise ValueError("Physical cell index must be a nonnegative integer")
        if (ti, ri, ci) in self.text_cache:
            return self.text_cache[ti, ri, ci]
        # Decompose a copy to leave the independent source tree intact.
        from bs4 import BeautifulSoup
        cell = self.cells(ti, ri)[ci]
        copy = BeautifulSoup(str(cell), "html.parser")
        for tag in copy.find_all(["sup", "script", "style", "ix:hidden"]):
            tag.decompose()
        for tag in copy.find_all("br"):
            tag.replace_with(" ")
        self.text_cache[ti, ri, ci] = norm(copy.get_text(separator=""))
        return self.text_cache[ti, ri, ci]

    def locator(self, locator):
        kind = locator.get("kind", "html_cell")
        expected = norm(locator.get("text", ""))
        if not expected:
            raise ValueError("Empty source context locator")
        if kind == "html_cell":
            actual = self.cell(locator["table_index"], locator["row_index"], locator["cell_index"])
        elif kind == "text":
            # Offsets are UTF-8 decoded original HTML character offsets, not cleaned Markdown offsets.
            start, end = locator["start"], locator["end"]
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(self.html):
                raise ValueError("Invalid original text offsets")
            actual = norm(self.html[start:end])
        else:
            raise ValueError("Unsupported source context locator")
        if actual != expected:
            raise ValueError(f"Source context changed: expected {expected!r}, found {actual!r}")
        return actual

    def context_period(self, ti, ri, ci, explicit_ref=None):
        cell = self.cells(ti, ri)[ci]
        facts = cell.find_all(attrs={"contextref": True})
        if explicit_ref:
            facts = [f for f in facts if f.get("contextref") == explicit_ref]
            if not facts:
                raise ValueError("Declared inline-XBRL context is absent from the original cell")
        refs = {f.get("contextref") for f in facts}
        if len(refs) != 1:
            return None
        context = self.by_id.get(next(iter(refs)))
        if context is None:
            raise ValueError("Inline XBRL context is missing")
        def text_for(local):
            tag = context.find(lambda t: t.name and t.name.split(":")[-1].lower() == local)
            return norm(tag.get_text()) if tag else None
        instant, start, end = text_for("instant"), text_for("startdate"), text_for("enddate")
        return {"start": None, "end": instant} if instant else {"start": start, "end": end}

    def grid(self, ti):
        """Independently map expanded columns to physical original cells."""
        if ti in self.grid_cache:
            return self.grid_cache[ti]
        grid = {}
        for ri, _ in enumerate(self.rows(ti)):
            col = 0
            for ci, cell in enumerate(self.cells(ti, ri)):
                while (ri, col) in grid:
                    col += 1
                rs, cs = int(cell.get("rowspan", 1)), int(cell.get("colspan", 1))
                if not 1 <= rs <= 1000 or not 1 <= cs <= 1000:
                    raise ValueError("Unsupported original span; Agent must resolve the source shape")
                for dr in range(rs):
                    for dc in range(cs):
                        grid[ri + dr, col + dc] = (ri, ci)
                col += cs
        self.grid_cache[ti] = grid
        return grid


def audit_sources(model, workspace):
    """Full raw-value reread plus financial-row coverage; no per-HTML-row ledger."""
    findings, originals, bindings = [], {}, {}
    index = EvidenceIndex(model)
    workspace = Path(workspace).resolve()
    def issue(where, message, status="FAIL"):
        findings.append({"status": status, "location": where, "message": str(message)})
    for source in model.get("sources", []):
        sid = source.get("source_id", "?")
        try:
            path = (workspace / source["path"]).resolve()
            path.relative_to(workspace)
            originals[sid] = Original(path, source, workspace)
        except Exception as exc:
            issue(sid, exc)
    # Shared context is verified once per selected source view.
    for tid, table in index.tables.items():
        try:
            original = originals[table["source_id"]]
            for field in ("unit", "scope"):
                locator = table.get("context", {}).get(field)
                if not locator: raise ValueError(f"Shared source {field} context missing")
                original.locator(source_locator(table, locator))
            if table.get("locator_kind", "html_cell") == "html_cell":
                ti = table["html_table_index"]
                first, last = table["data_rows"]
                if not 0 <= first <= last < len(original.rows(ti)):
                    raise ValueError("Financial body range is outside original table")
                for metric, row in table["rows"].items():
                    if original.cell(ti, row["r"], row["c"]) != norm(row["label"]):
                        raise ValueError(f"Original metric label differs: {metric}")
                for period in table["periods"].values():
                    for locator in period.get("headers", []):
                        original.locator(source_locator(table, locator))
        except Exception as exc:
            issue(tid, exc)
    for short, row, label, value, binding in index.facts(include_missing=True):
        where = f"{short}:{row['id']}/{label}"
        try:
            ref = index.resolve(row, label, binding)
            table = index.tables[ref["table_id"]]
            original = originals[ref["source_id"]]
            if ref["locator_kind"] == "html_cell":
                ti, ri, ci = ref["html_table_index"], ref["html_row_index"], ref["html_cell_index"]
                grid = original.grid(ti)
                if ri != ref["label_row_index"] and not any(
                    gr == ri and native == (ref["label_row_index"], ref["label_cell_index"])
                    for (gr, _), native in grid.items()
                ):
                    raise ValueError("Value is not on its metric-label row or an original label rowspan")
                if grid.get((ri, table["periods"][label]["column"])) != (ri, ci):
                    raise ValueError("Value coordinates do not match the shared fiscal column")
                raw = original.cell(ti, ri, ci)
                context = original.context_period(ti, ri, ci, ref.get("context_ref"))
                if context:
                    if any(context.get(k) != ref["period"].get(k) for k in ("start", "end")):
                        raise ValueError(f"Inline-XBRL interval differs from selected fiscal period: {context}")
                elif not ref["period_header_cells"]:
                    raise ValueError("No unambiguous XBRL interval or exact original period-heading locator")
                bindings.setdefault((ref["table_id"], ri, ci), set()).add((short, row["id"], label))
            else:
                raw = original.locator(ref["text_locator"])
                original.locator(ref["label_locator"])
                if norm(ref["source_label"]) not in norm(ref["label_locator"]["text"]):
                    raise ValueError("Narrative source label is not anchored in the original")
                if not ref["period_header_cells"]:
                    raise ValueError("Narrative value needs exact original period context")
                for locator in ref["period_header_cells"]:
                    original.locator(locator)
            normalization = ref.get("normalization", {})
            if is_number(value):
                actual = audit_number(raw, normalization)
                if normalization.get("sign", 1) == -1:
                    sign_locator = ref.get("sign_locator")
                    if not sign_locator or not any(s in original.locator(sign_locator) for s in ("(", "-", "−")):
                        raise ValueError("Negative sign conversion lacks original sign evidence")
                if not math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-10):
                    raise ValueError(f"Original value {actual} differs from workbook input {value}")
            else:
                missing_meanings = {
                    "n.a.": {"n.a.", "n/a", "not applicable"},
                    "n/a": {"n.a.", "n/a", "not applicable"},
                    "n.m.": {"n.m.", "n/m", "not comparable"},
                    "n/m": {"n.m.", "n/m", "not comparable"},
                    "not applicable": {"not applicable", "n.a.", "n/a"},
                    "not disclosed": {"not disclosed"},
                    "not comparable": {"not comparable", "n.m.", "n/m"},
                }
                if str(value).lower() not in missing_meanings.get(norm(raw).lower(), set()):
                    raise ValueError("Source missing marker is unresolved or its meaning was changed; missing is never zero")
        except Exception as exc:
            issue(where, exc)
    # Only numeric financial body rows need coverage. Title/blank/label-only
    # rows are handled mechanically; exclusions are recorded only when relevant.
    for tid, table in index.tables.items():
        if table.get("locator_kind", "html_cell") != "html_cell": continue
        try:
            original = originals[table["source_id"]]
            ti, (first, last) = table["html_table_index"], table["data_rows"]
            grid = original.grid(ti)
            excluded = table.get("exclude_rows", {})
            for ri in range(first, last + 1):
                if str(ri) in excluded: continue
                for label, period in table["periods"].items():
                    native = grid.get((ri, period["column"]))
                    if native is None: continue
                    raw = original.cell(ti, *native)
                    if not re.search(r"\d", raw) and raw not in {"—", "–", "-", "n.a.", "n.m."}:
                        continue
                    if not any(p == label for _, _, p in bindings.get((tid, *native), set())):
                        raise ValueError(f"Financial source row {ri}, fiscal column {label} has no exported value or explained exclusion")
        except Exception as exc:
            issue(tid, exc)
    for entry in model.get("coverage", []):
        for gap in entry.get("gaps", []):
            issue(entry["topic"], gap.get("reason", "Unresolved disclosure gap"), "UNVERIFIABLE")
    findings.extend(audit_derivations(model))
    status = ("FAIL" if any(f["status"] == "FAIL" for f in findings)
              else "UNVERIFIABLE" if findings else "PASS")
    return {"status": status, "originals_reopened": len(originals),
            "reported_cells_bound": sum(len(v) for v in bindings.values()), "findings": findings}


def audit_derivations(model):
    """Check explicit cumulative-flow subtraction against actual input intervals."""
    findings, rows = [], {}
    index = PeriodIndex(model["periods"])
    for sheet in model.get("sheets", []):
        for block in sheet.get("blocks", []):
            for row in block.get("rows", []):
                if row.get("id"): rows[sheet["short"], row["id"]] = row
    for (short, rid), row in rows.items():
        for label, expr in {**row.get("cell_expr", {}), **row.get("expr_by_period", {})}.items():
            d = row.get("cell_meta", {}).get(label, {}).get("derivation", {})
            if d.get("kind") != "quarter_difference": continue
            where = f"{short}:{rid}/{label}"
            try:
                tokens = list(TOKEN_RE.finditer(expr))
                resolved = [resolve_token(t, short, label, index) for t in tokens]
                declared = [(v["sheet"], v["row"], v["period"]) for v in d["inputs"]]
                if resolved != declared or len(resolved) != 2:
                    raise ValueError("Quarter difference must name exactly the two actual formula inputs in order")
                # No extra constants, multiplication, ratios or inverted subtraction.
                if TOKEN_RE.sub("X", expr).replace(" ", "") != "X-X":
                    raise ValueError("Quarter difference formula must be cumulative_end minus cumulative_prior")
                a, b = [period_for(model, rows[s, r], p) for s, r, p in resolved]
                out = period_for(model, row, label)
                if a.get("start") != b.get("start") or a.get("end") != out.get("end"):
                    raise ValueError("Cumulative inputs must share fiscal start and output end")
                if date.fromisoformat(b["end"]) + timedelta(days=1) != date.fromisoformat(out["start"]):
                    raise ValueError("Output interval does not begin immediately after prior cumulative interval")
                if a["grain"] not in {"annual", "ytd"} or b["grain"] != "ytd" or out["grain"] != "discrete":
                    raise ValueError("Subtraction requires annual/YTD minus YTD to a discrete quarter")
                for s, r, p in resolved:
                    dependency = rows[s, r]
                    if not dependency.get("additive") or dependency.get("metric_kind") in {"eps", "weighted_average_shares", "balance", "ratio"}:
                        raise ValueError("Subtraction dependency is not an additive flow")
                    for field in ("unit", "currency", "scope", "measure_basis"):
                        if dependency.get(field) != row.get(field):
                            raise ValueError(f"Quarter difference changes {field}")
            except Exception as exc:
                findings.append({"status": "FAIL", "location": where, "message": str(exc)})
    return findings
