"""Normalize cached regulatory annual facts and source-labelled balance sheets."""
import argparse
import json
from pathlib import Path
import re
from datetime import date


def web_table(path):
    text = path.read_text()
    currency = re.search(r"(?:millions|Millions)\s+(USD|EUR|BRL|MXN|CLP|GBP)", text)
    rows, years = {}, []
    for line in text.splitlines():
        line = re.sub(r"^L\d+:\s*", "", line)
        line = re.sub(r"cite[^]+", "", line)
        cells = [x.strip() for x in line.split("  | ")]
        if cells[0] == "Fiscal Year":
            years = [int(x[3:]) if re.fullmatch(r"FY \d{4}", x) else None for x in cells[1:]]
        elif years and len(cells) == len(years) + 1:
            for year, value in zip(years, cells[1:]):
                if year is None:
                    continue
                try:
                    value = float(value.replace(",", "").replace("%", ""))
                except ValueError:
                    value = None
                rows.setdefault(year, {})[cells[0]] = value
    return rows, currency.group(1) if currency else None


def prepare(config, root):
    old = root / config["baseline_dir"]
    src = root / config["source_dir"]
    facts = json.loads((old / "annual-facts.json").read_text())
    ix = json.loads((old / "primary-ix-facts.json").read_text())
    overrides = config.get("financial_overrides", {})
    result = {}
    for ticker, annual in facts.items():
        balance_path = src / f"{ticker}-sa-balance-web.txt"
        balance, currency = web_table(balance_path)
        if not balance:
            raise ValueError(f"{ticker}: no cached balance sheet parsed")
        cf_path = src / f"{ticker}-sa-cashflow-web.txt"
        cf, _ = web_table(cf_path) if cf_path.exists() else ({}, None)
        source_facts = json.loads((root / config['baseline_source_dir'] / f'{ticker}-companyfacts.json').read_text())['facts']
        records = []
        for year, bs in sorted(balance.items()):
            raw = next((r for r in annual if r["year"] == year), None)
            if raw is None:
                continue
            # Currency is enforced per field, including the pre-existing data.
            def get(key):
                value = raw.get(key)
                return value["value"] / 1e6 if value and value["unit"] == currency else None
            def tagged(tags):
                candidates = [f for f in ix[ticker] if f["tag"].split(":")[-1] in tags
                              and f["end"] == raw["end"] and f["unit"] == currency
                              and f.get("start") and 330 <= (date.fromisoformat(f['end']) - date.fromisoformat(f['start'])).days <= 390]
                if candidates:
                    return candidates[0]["value"] / 1e6
                for ns in source_facts.values():
                    for tag in tags:
                        vals = [v for v in ns.get(tag, {}).get('units', {}).get(currency, [])
                                if v.get('end')==raw['end'] and v.get('start') and v.get('filed','')<=config['as_of']
                                and 330 <= (date.fromisoformat(v['end'])-date.fromisoformat(v['start'])).days <= 390]
                        if vals:
                            return max(vals,key=lambda v:v.get('filed',''))['val']/1e6
                return None
            row = {"year": year, "end": raw["end"], "currency": currency,
                   "unit": "million", "source_paths": [str(balance_path.relative_to(root)),
                   config["baseline_dir"] + "/annual-facts.json"],
                   "source_notes": [], "gross_margin": raw.get("gross_margin")}
            for key in ("revenue", "gross", "ebit", "pretax", "tax", "cfo", "capex", "sbc", "net_income", "shares"):
                row[key] = get(key)
            # SEC raw monetary tags use full units; share data are separate.
            row["shares"] = raw.get("shares", {}).get("value") / 1e6 if raw.get("shares") else None
            for key, label in {"equity": "Shareholders' Equity", "debt_leases": "Total Debt",
                               "liquid_assets": "Cash & Short-Term Investments", "goodwill": "Goodwill",
                               "intangibles": "Other Intangible Assets", "assets": "Total Assets",
                               "filing_shares": "Filing Date Shares Outstanding"}.items():
                row[key] = bs.get(label)
            # Debt-free and immaterial-intangible cases require a visible source
            # aggregate, not absence in the SEC tag mapping.
            if row["goodwill"] is None and row["intangibles"] is None:
                combined = get("intangibles_including_goodwill")
                if combined is not None:
                    row["goodwill"], row["intangibles"] = 0, combined
                    row["source_notes"].append("Combined goodwill/intangible balance retained; no claim that goodwill is zero")
            if row["ebit"] is None and ticker in config.get("constructed_ebit", []):
                sga = get("selling")
                admin = get("admin")
                if all(v is not None for v in (row["gross"], sga, admin)):
                    other_income = tagged(["OtherIncome"])
                    other_expense = tagged(["OtherExpenseByFunction", "OtherExpenseByNature"])
                    if other_income is not None and other_expense is not None:
                        row["ebit"] = row["gross"] - sga - admin + other_income - other_expense
                        row["source_notes"].append("Constructed EBIT = gross profit - selling - administration + separately disclosed other income - other expense; not a reported IFRS subtotal")
            for key, label in {"capex": "Capital Expenditures", "sbc": "Stock-Based Compensation"}.items():
                if row[key] is None and cf.get(year, {}).get(label) is not None:
                    row[key] = abs(cf[year][label]) if key=='capex' else cf[year][label]
                    row["source_paths"].append(str(cf_path.relative_to(root)))
            row.update(overrides.get(ticker, {}).get(str(year), {}))
            # Tax signs in IFRS source tags differ. Reconcile instead of abs().
            ni = tagged(["ProfitLossFromContinuingOperations"])
            if ni is not None:
                row["net_income"] = ni
            if row["tax"] is not None and row["pretax"] is not None and row["net_income"] is not None:
                difference = row["pretax"] - row["net_income"]
                if abs(row["tax"] + difference) < max(1, abs(difference) * .005) and difference != 0:
                    row["tax"] = difference
                    row["source_notes"].append("IFRS tax sign reconciled to pretax minus consolidated profit")
            if row["tax"] is None and row["pretax"] is not None and row["net_income"] is not None:
                row["tax"] = row["pretax"] - row["net_income"]
                row["source_notes"].append("Tax derived from pretax minus consolidated continuing profit")
            paid = tagged(['InterestPaidClassifiedAsFinancingActivities'])
            received = tagged(['InterestReceivedClassifiedAsInvestingActivities'])
            row["financing_interest_paid"] = overrides.get(ticker, {}).get(str(year), {}).get("financing_interest_paid", paid if paid is not None else 0)
            row["investing_interest_received"] = overrides.get(ticker, {}).get(str(year), {}).get("investing_interest_received", received if received is not None else 0)
            row['interest_classification_basis'] = 'SEC financing/investing interest tags where present; issuer cash flow classification reviewed separately'
            row["equity_match_error"] = None if get("equity") is None or row["equity"] is None else row["equity"] - get("equity")
            bridge = config.get('capital_equity_bridge_notes', {}).get(ticker)
            if bridge:
                row['source_notes'].append(bridge)
            records.append(row)
        start = config.get("financial_start_year", {}).get(ticker)
        if start is not None:
            records = [r for r in records if r["year"] >= start]
        result[ticker] = records[-5:]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    config = json.loads(args.config.read_text())
    out = root / config["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    result = prepare(config, root)
    (out / "normalized-financials.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for ticker, rows in result.items():
        missing = {key: [r["year"] for r in rows if r.get(key) is None]
                   for key in ("ebit", "net_income", "cfo", "capex", "sbc", "equity", "debt_leases", "liquid_assets", "goodwill", "intangibles", "filing_shares")}
        print(ticker, len(rows), {k: v for k, v in missing.items() if v})


if __name__ == "__main__":
    main()
