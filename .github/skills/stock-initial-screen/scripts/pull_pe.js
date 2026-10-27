async () => {
  const KEYS = __KEYS__;            // Fiscal.ai keys of the run companies (both listings when a company moved exchange)
  const FROM = "__FROM__";          // as_of minus 10 years, e.g. "2016-10-20"
  const ymd = s => s.slice(2, 4) + s.slice(5, 7) + s.slice(8, 10);
  async function one(k) {
    const [dr, lt] = await Promise.all([
      codemode.company_daily_ratios({ companyKey: k, ratioId: "ratio_price_to_earnings" }),
      codemode.company_ratios({ companyKey: k, periodType: "latest", ratioId: "market_data_share_price,calculated_market_cap,ratio_forward_price_to_earnings,ratio_price_to_earnings" })]);
    const pts = (dr || []).filter(x => x.date >= FROM).sort((a, b) => a.date.localeCompare(b.date));
    const d = (lt.data || [])[lt.data.length - 1] || { metricValues: {} }; const mv = d.metricValues || {};
    return { d: pts.map(x => ymd(x.date)).join(","), r: pts.map(x => x.ratio == null ? "" : Math.round(x.ratio * 10) / 10).join(","),
             price: mv.market_data_share_price ?? null, mcap: mv.calculated_market_cap ?? null, fwd: mv.ratio_forward_price_to_earnings ?? null,
             ttm: mv.ratio_price_to_earnings ?? null, cur: (d.tradingCurrency || {}).currency || null };
  }
  const out = {};
  for (let i = 0; i < KEYS.length; i += 3) {
    const rs = await Promise.all(KEYS.slice(i, i + 3).map(k => one(k).catch(e => ({ err: String(e).slice(0, 150) }))));
    rs.forEach((r, j) => out[KEYS[i + j]] = r);
  }
  console.log(JSON.stringify(out) + "\n//" + "x".repeat(130000));
}
