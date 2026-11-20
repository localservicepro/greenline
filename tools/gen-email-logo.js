/*
 * Render the horizontal email lockup as PNG.
 *
 *     node tools/gen-email-logo.js
 *
 * Email clients will not load a webfont, so the lockup — the tree mark, the
 * PRESTIGE wordmark and the tagline — has to ship as a flat raster. Outputs
 * four files to assets/img/logo/:
 *
 *     logo-email-800.png              800x240, black ground — the one to use
 *     logo-email-400.png              400x120, black ground — half size
 *     logo-email-800-transparent.png  same, alpha
 *     logo-email-400-transparent.png  same, alpha
 *
 * The 800px file is a 2x asset: set width="400" (or less) on the <img> so it
 * stays sharp on retina screens. The ground is the brand's near-black, which is
 * what the gold artwork was drawn for — over white the mark keys out pale and
 * the wordmark has to carry the whole lockup. The transparent files are for
 * placing on another dark panel, not on a white email body.
 *
 * The mark comes from whichever file LOGO_MARK names in build.py, so changing
 * the brand mark and re-running keeps the email logo in step. Needs Playwright,
 * the pre-installed Chromium, and network access to fonts.googleapis.com.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'assets', 'img', 'logo');
const BG = '#0D0D0D';

const JOBS = [
  ['logo-email-400.png', 1, false],
  ['logo-email-800.png', 2, false],
  ['logo-email-400-transparent.png', 1, true],
  ['logo-email-800-transparent.png', 2, true],
];

function mark() {
  const build = fs.readFileSync(path.join(__dirname, 'build.py'), 'utf8');
  const m = build.match(/^LOGO_MARK = "([^"]+)"/m);
  if (!m) throw new Error('LOGO_MARK not found in build.py');
  const named = path.join(ROOT, m[1].replace(/^\//, ''));
  // Prefer a large sibling: the header file is sized for a 30px slot.
  const big = named.replace(/-\d+\.png$/, '-512.png');
  const file = fs.existsSync(big) ? big : named;
  if (file.toLowerCase().endsWith('.svg')) return fs.readFileSync(file, 'utf8');
  // setContent gives the page no origin, so Chromium refuses a file:// image.
  return `<img src="data:image/png;base64,${fs.readFileSync(file).toString('base64')}">`;
}

// Fixed 400x120 at scale 1, so the retina export lands on a round 800x240.
const page_html = (markHtml) => `<!doctype html>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,900&family=Karla:wght@600;700&display=swap" rel="stylesheet">
<style>
  :root{--gold:#F0C34B;--gold-2:#C9962B;--rule:#8A6E22}
  *{box-sizing:border-box;margin:0}
  body{background:transparent}
  .lockup{width:400px;height:120px;display:flex;align-items:center;
    justify-content:center;gap:18px;font-family:Karla,sans-serif}
  .mark{width:92px;height:92px;flex:none;display:grid;place-items:center}
  .mark svg,.mark img{width:100%;height:100%;object-fit:contain;display:block}
  .words{display:flex;flex-direction:column;align-items:center}
  .n{font-family:Fraunces,serif;font-weight:900;font-size:36px;line-height:1;
    letter-spacing:.01em;color:var(--gold);white-space:nowrap}
  .sub{display:flex;align-items:center;gap:10px;margin-top:9px;width:100%}
  .sub .line{flex:1;height:1.5px;background:var(--rule)}
  .sub .t{font-weight:700;font-size:12px;letter-spacing:.22em;color:var(--gold-2);
    text-transform:uppercase;white-space:nowrap}
  .tag{margin-top:8px;font-weight:600;font-size:9.5px;letter-spacing:.12em;
    color:#9A8A5E;text-transform:uppercase;white-space:nowrap}
</style>
<div class="lockup" id="lockup">
  <span class="mark">${markHtml}</span>
  <div class="words">
    <div class="n">PRESTIGE</div>
    <div class="sub"><span class="line"></span><span class="t">Property Care</span><span class="line"></span></div>
    <div class="tag">Lawn &amp; Property Maintenance</div>
  </div>
</div>`;

(async () => {
  const html = page_html(mark());
  const browser = await chromium.launch();
  for (const [name, scale, transparent] of JOBS) {
    const page = await browser.newPage({
      viewport: { width: 700, height: 220 },
      deviceScaleFactor: scale,
    });
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    if (!transparent) {
      await page.evaluate((bg) => (document.body.style.background = bg), BG);
    }
    await page.waitForTimeout(400);
    await page.locator('#lockup').screenshot({
      path: path.join(OUT, name),
      omitBackground: transparent,
    });
    console.log('wrote', name);
    await page.close();
  }
  await browser.close();
})();
