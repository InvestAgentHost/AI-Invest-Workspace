#!/usr/bin/env python3
"""Text-only disclosures: management outlook (forward-looking) and operating-KPI sentences.
Verbatim sentences from the prepared 10-K document.md with line locators; nothing paraphrased."""
import glob
import re

SRC = "../../../../../../sources/companies/US/MCD-mcdonalds/artifacts/ten_k/MCD-mcdonalds"


def lines(fy):
    p = glob.glob(f"{SRC}/FY{fy}/psp_*/prepared/document.md")[0]
    return p, open(p, encoding="utf-8").read().split("\n")


GUIDE_ITEMS = [
    (r"net restaurant (additions|unit expansion)", "Net restaurant additions contribution to Systemwide sales growth"),
    (r"systemwide sales growth", "Systemwide sales growth"),
    (r"general (and|&) administrative", "SG&A"),
    (r"operating margin", "Operating margin"),
    (r"interest expense", "Interest expense"),
    (r"effective (income )?tax rate", "Effective tax rate"),
    (r"capital expenditures", "Capital expenditures / restaurant openings"),
    (r"free cash flow", "Free cash flow conversion"),
]


def guidance():
    rows = []
    for fy in range(2016, 2026):
        p, L = lines(fy)
        seen = set()
        for i, ln in enumerate(L, 1):
            t = re.sub(r"^\|?\s*[•◦]\s*\|?\s*", "", ln.strip()).rstrip("|").strip()
            if i > 1100 or not re.search(r"\b(expects?|anticipates?)\b", t, re.I):
                continue
            item = next((name for pat, name in GUIDE_ITEMS if re.search(pat, t[:170], re.I)), None)
            if not item or (not re.search(rf"\b{fy + 1}\b", t) and item not in ("Operating margin", "Free cash flow conversion")):
                continue
            if not item or (fy, item) in seen:
                continue
            # skip sentences that are about the Tax Act benefit, litigation etc.
            if item in ("Systemwide sales growth",) and "net restaurant" in t.lower():
                item = GUIDE_ITEMS[0][1]
            seen.add((fy, item))
            rows.append({"fy": fy, "guided_year": fy + 1, "item": item, "text": re.sub(r"\s+", " ", t)[:520], "line": i})
    return rows


KPI_PAT = [
    (r"loyalty", "Loyalty / digital"), (r"90-day active", "Loyalty / digital"), (r"delivery (from|sales)", "Delivery"),
    (r"drive thru (locations|restaurants)|drive-thru", "Drive thru"), (r"new restaurants|restaurant openings|50,000 restaurants|new unit growth", "Restaurant development"),
    (r"employees.{0,80}totaled", "Employees"), (r"restructuring charges", "Restructuring"), (r"more than 100 countries", "Footprint"),
]


def kpi_sentences():
    out = []
    for fy in range(2021, 2026):
        p, L = lines(fy)
        for i, ln in enumerate(L, 1):
            if ln.startswith("|") or len(ln) < 60:
                continue
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z$])", ln):
                if not re.search(r"(\d[\d,.]*\s*(million|billion|%|markets|restaurants|locations|new)|\$\s?\d|\b\d{2,3},\d{3}\b)", s):
                    continue
                if s.lstrip("•◦ ").startswith("Capital expenditures increased"):
                    continue
                for pat, topic in KPI_PAT:
                    if topic == "Restructuring":
                        continue
                    if re.search(pat, s, re.I):
                        out.append({"fy": fy, "topic": topic, "text": re.sub(r"\s+", " ", s)[:560], "line": i})
                        break
    # de-duplicate
    seen, res = set(), []
    for r in out:
        k = (r["fy"], r["text"][:80])
        if k not in seen:
            seen.add(k)
            res.append(r)
    return res


if __name__ == "__main__":
    for g in guidance():
        print(g["fy"], g["guided_year"], g["item"], "|", g["text"][:150], "| L", g["line"])
    print()
    k = kpi_sentences()
    print(len(k))
    for r in k[:60]:
        print(r["fy"], r["topic"], "|", r["text"][:170], "| L", r["line"])
