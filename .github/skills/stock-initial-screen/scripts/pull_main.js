async () => {
  const KEYS = __KEYS__;
  const v = (d, id) => { if (!d) return null; const x = d.metricsValues[id]; return (x && x.value != null) ? x.value : null; };
  const byFY = r => { const m = {}; for (const d of (r.data || [])) { if (d.periodType !== "Annual" || d.isStubPeriod || d.fiscalYear == null) continue; if (!m[d.fiscalYear]) m[d.fiscalYear] = d; } return m; };
  const M = x => x == null ? null : Math.round(x / 1e5) / 10;            // millions, 1 decimal
  const AM = /amorti[sz]ation of (acquired |purchased |other |customer-related )?(identifi\w+ )?intangible|intangible[^,]{0,40}amorti[sz]ation/i;
  const AMX = /debt|financing|deferred|inventory|loss contract|issuance|software|depreciation|profit|before|excluding/i;
  const IMP = /impairment/i, IMPG = /goodwill|intangible|trademark|brand/i, IMPX = /reversal|tax|deferred|profit|before|excluding|amorti/i;
  const CFC = /operating activities[^,]{0,40}(?<!dis)continuing|(?<!dis)continuing operations[^,]{0,40}operating/i, CFD = /operating activities[^,]{0,40}discontinued|discontinued operations[^,]{0,40}operating|operating[^,]{0,20}- discontinued/i;
  async function one(k) {
    const [is, bs, cf, ari, arc] = await Promise.all([
      codemode.company_financials_standardized({ companyKey: k, statementType: "income-statement", periodType: "annual" }),
      codemode.company_financials_standardized({ companyKey: k, statementType: "balance-sheet", periodType: "annual" }),
      codemode.company_financials_standardized({ companyKey: k, statementType: "cash-flow-statement", periodType: "annual" }),
      codemode.company_financials_as_reported({ companyKey: k, statementType: "income-statement", periodType: "annual" }).catch(() => ({ metrics: [], data: [] })),
      codemode.company_financials_as_reported({ companyKey: k, statementType: "cash-flow-statement", periodType: "annual" }).catch(() => ({ metrics: [], data: [] }))]);
    const IS = byFY(is), BS = byFY(bs), CF = byFY(cf), AI = byFY(ari), AC = byFY(arc);
    const find = (r, re, ex) => r.metrics.filter(m => re.test(m.metricName) && !(ex && ex.test(m.metricName)));
    // amortization of acquired intangibles: prefer an income-statement line, else the cash-flow add-back
    let amM = find(ari, AM, AMX), amSt = AI, amSrc = "IS";
    if (!amM.length) { amM = find(arc, AM, AMX); amSt = AC; amSrc = "CF"; }
    const impM = ari.metrics.filter(m => IMP.test(m.metricName) && IMPG.test(m.metricName) && !IMPX.test(m.metricName));
    const cfcM = arc.metrics.filter(m => CFC.test(m.metricName)).slice(0, 1), cfdM = arc.metrics.filter(m => CFD.test(m.metricName)).slice(0, 1);
    const one1 = (ms, y) => { const d = AC[y]; if (!d || !ms.length) return null; const x = d.metricsValues[ms[0].asReportedMetricId]; return (x && x.value != null) ? x.value : null; };
    const sum = (St, ms, y) => { const d = St[y]; if (!d) return 0; let t = 0; for (const m of ms) { const x = d.metricsValues[m.asReportedMetricId]; if (x && x.value != null) t += Math.abs(x.value); } return t; };
    const yrs = Object.keys(IS).map(Number).filter(y => v(IS[y], "income_statement_total_revenues") != null).sort((a, b) => a - b);
    const L = yrs[yrs.length - 1];
    const cols = ["fy","rev","op","gp","am","imp","debt","eq","cash","gw","ia","cfo","capex","sbc","nicf","int","intInc","pt","tax","dil","cfoCont","cfoDisc","da"];
    const rows = [];
    for (let y = L - 20; y <= L; y++) {
      const i = IS[y], b = BS[y], c = CF[y];
      if (!i) continue;
      const debt = b ? ["balance_sheet_short_term_debt","balance_sheet_current_portion_of_long_term_debt","balance_sheet_long_term_debt","balance_sheet_leases","balance_sheet_current_portion_of_leases"].reduce((t, id) => t + (v(b, id) || 0), 0) : null;
      let cash = v(b, "balance_sheet_total_cash_and_cash_equivalents"); if (cash == null) cash = v(b, "balance_sheet_cash_and_cash_equivalents");
      const ie = v(i, "income_statement_interest_expense");
      rows.push([y, M(v(i, "income_statement_total_revenues")), M(v(i, "income_statement_operating_profit")), M(v(i, "income_statement_gross_profit")),
        M(sum(amSt, amM, y)), M(sum(AI, impM, y)), M(debt), M(v(b, "balance_sheet_total_shareholders_equity")), M(cash),
        M(v(b, "balance_sheet_goodwill")), M(v(b, "balance_sheet_net_intangible_assets")),
        M(v(c, "cash_flow_statement_cash_from_operating_activities")), M(v(c, "cash_flow_statement_purchases_of_property_plant_and_equipment")),
        M(v(c, "cash_flow_statement_share_based_compensation_expense")), M(v(c, "cash_flow_statement_net_income")),
        ie == null ? null : M(Math.abs(ie)), M(v(i, "income_statement_interest_income")),
        M(v(i, "income_statement_income_before_provision_for_income_taxes")), M(v(i, "income_statement_provision_for_income_taxes")),
        M(v(i, "income_statement_diluted_weighted_average_shares_outstanding")), M(one1(cfcM, y)), M(one1(cfdM, y)), M(v(c, "cash_flow_statement_depreciation_and_amortization"))]);
    }
    return { L, cur: (is.data && is.data[0] && Object.values(is.data[0].metricsValues).find(x => x && x.currency) || {}).currency || null, cols, rows,
             amSrc: amM.length ? amSrc + ":" + amM.map(m => m.metricName).join(";") : "none", impSrc: impM.length ? "IS:" + impM.map(m => m.metricName).join(";") : "none", cfoSrc: (cfcM.length ? "cont:" + cfcM[0].metricName : "") + (cfdM.length ? " disc:" + cfdM[0].metricName : "") };
  }
  const out = {};
  for (let i = 0; i < KEYS.length; i += 1) {
    const rs = await Promise.all(KEYS.slice(i, i + 1).map(k => one(k).catch(e => ({ err: String(e).slice(0, 150) }))));
    rs.forEach((r, j) => out[KEYS[i + j]] = r);
  }
  console.log(JSON.stringify(out) + "\n//" + "x".repeat(130000));
}
