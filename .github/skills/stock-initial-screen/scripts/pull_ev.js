async () => {
  const KEYS = __KEYS__;            // Fiscal.ai keys of the run companies
  const FROM = "__FROM__";          // as_of minus 10 years minus one week, e.g. "2016-10-13"
  const ymd = s => s.slice(2, 4) + s.slice(5, 7) + s.slice(8, 10);
  const ser = (arr, f, dig) => { const pts = (arr || []).filter(x => x.date >= FROM).sort((a, b) => a.date.localeCompare(b.date));
    return { d: pts.map(x => ymd(x.date)).join(","), r: pts.map(x => { const v = f(x); return v == null ? "" : Math.round(v * dig) / dig; }).join(",") }; };
  async function one(k) {
    const [ebit, ebitda, tev, px] = await Promise.all([
      codemode.company_daily_ratios({ companyKey: k, ratioId: "ratio_ev_to_ebit" }),
      codemode.company_daily_ratios({ companyKey: k, ratioId: "ratio_ev_to_ebitda" }),
      codemode.company_daily_ratios({ companyKey: k, ratioId: "calculated_tev" }),
      codemode.company_stock_prices({ companyKey: k })]);
    return { ebit: ser(ebit, x => x.ratio, 10), ebitda: ser(ebitda, x => x.ratio, 10),
             tev: ser(tev, x => x.ratio == null ? null : x.ratio / 1e6, 1),           // millions, trading currency
             px: ser((px || {}).prices || [], x => x.closePrice, 1000), pxCur: (px || {}).tradingCurrency || null, pxListing: (px || {}).exchangeCode + "_" + (px || {}).ticker };
  }
  const out = {};
  for (const k of KEYS) out[k] = await one(k).catch(e => ({ err: String(e).slice(0, 150) }));
  console.log(JSON.stringify(out) + "\n//" + "x".repeat(130000));
}
