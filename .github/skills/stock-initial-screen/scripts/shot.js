// node shot.js <html file> [OUT_DIR] [TICKER,TICKER]  -> top.png, strip.png, co_<T>.png
const { chromium } = require('playwright');
(async () => {
  const [file, outDir = '.', ids = ''] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1240, height: 900 } });
  await p.goto('file://' + require('path').resolve(file));
  await p.screenshot({ path: outDir + '/top.png', fullPage: false });
  const w = await p.$$('.wrap'); if (w[1]) await w[1].screenshot({ path: outDir + '/strip.png' });
  for (const id of ids.split(',').filter(Boolean)) {
    await p.evaluate(i => { const d = document.getElementById(i); if (d) d.open = true; }, id);
    const el = await p.$('[id="' + id + '"] .top2'); if (el) await el.screenshot({ path: outDir + '/co_' + id + '.png' });
    const t = await p.$('[id="' + id + '"] .cobody'); if (t) await t.screenshot({ path: outDir + '/full_' + id + '.png' });
  }
  const mobile = await b.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto('file://' + require('path').resolve(file)); await mobile.screenshot({ path: outDir + '/mobile.png' });
  await b.close();
})();
