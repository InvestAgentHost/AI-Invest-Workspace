async () => {
  // Resolve tickers to Fiscal.ai keys. Lists every exchange where the ticker exists, with trading status,
  // so a listing change (e.g. Nasdaq -> NYSE) is visible: score on the active key; join P/E histories by hand.
  const TICKERS = __TICKERS__;
  const EX = ["NYSE", "NASDAQ", "NYSEAM", "OTCM"];
  const out = {};
  for (let i = 0; i < TICKERS.length; i += 1) {
    const t = TICKERS[i]; const hits = [];
    const rs = await Promise.all(EX.map(ex => codemode.company_profile({ companyKey: ex + "_" + t }).catch(() => null)));
    rs.forEach((p, j) => { if (p) hits.push({ key: EX[j] + "_" + t, name: p.name, status: p.tradingStatus, country: p.countryCode, sector: p.sector, industry: p.industry, subIndustry: p.subIndustry, reporting: p.reportingCurrency }); });
    out[t] = hits.length ? hits : "not found";
  }
  console.log(JSON.stringify(out));
}
