/*
 * Render the horizontal email lockup as PNG.
 *
 *     node tools/gen-email-logo.js
 *
 * Email clients will not render the site's SVG mark or load webfonts, so the
 * lockup — mark, wordmark and tagline — has to ship as a flat raster. Outputs
 * four files to assets/img/logo/:
 *
 *     logo-email-800.png              800x240, white — the one to use
 *     logo-email-400.png              400x120, white — half size
 *     logo-email-800-transparent.png  same, alpha
 *     logo-email-400-transparent.png  same, alpha
 *
 * The 800px file is a 2x asset: set width="400" (or less) on the <img> so it
 * stays sharp on retina screens. Prefer the white-background files in email —
 * a transparent dark-green mark disappears against a dark-mode background.
 *
 * The mark comes from whichever SVG LOGO_MARK names in build.py, so switching
 * the brand mark and re-running keeps the email logo in step. Needs Playwright,
 * the pre-installed Chromium, and network access to fonts.googleapis.com.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'assets', 'img', 'logo');

const JOBS = [
  ['logo-email-400.png', 1, false],
  ['logo-email-800.png', 2, false],
  ['logo-email-400-transparent.png', 1, true],
  ['logo-email-800-transparent.png', 2, true],
];

function markSvg() {
  const build = fs.readFileSync(path.join(__dirname, 'build.py'), 'utf8');
  const m = build.match(/^LOGO_MARK = "([^"]+)"/m);
  if (!m) throw new Error('LOGO_MARK not found in build.py');
  return fs.readFileSync(path.join(ROOT, m[1].replace(/^\//, '')), 'utf8');
}

// Fixed 400x120 at scale 1, so the retina export lands on a round 800x240.
const page_html = (svg) => `<!doctype html>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,900&family=Karla:wght@600;700&display=swap" rel="stylesheet">
<style>
  :root{--leaf:#19551D;--char:#262626;--rule:#C9CFC9}
  *{box-sizing:border-box;margin:0}
  body{background:transparent}
  .lockup{width:400px;height:120px;display:flex;align-items:center;
    justify-content:center;gap:20px;font-family:Karla,sans-serif}
  .mark{width:84px;height:84px;flex:none}
  .bar{width:2px;height:76px;background:var(--rule);flex:none}
  .words{display:flex;flex-direction:column;align-items:center}
  .n{font-family:Fraunces,serif;font-weight:900;font-size:38px;line-height:1;
    letter-spacing:-.025em;color:var(--leaf);white-space:nowrap}
  .sub{display:flex;align-items:center;gap:10px;margin-top:8px;width:100%}
  .sub .line{flex:1;height:2px;background:var(--leaf)}
  .sub .t{font-weight:700;font-size:13px;letter-spacing:.24em;color:var(--char);
    text-transform:uppercase;white-space:nowrap}
  .tag{margin-top:8px;font-weight:600;font-size:10px;letter-spacing:.12em;
    color:#55605A;text-transform:uppercase;white-space:nowrap}
  .mark svg{width:100%;height:100%;display:block}
</style>
<div class="lockup" id="lockup">
  <span class="mark">${svg}</span>
  <span class="bar"></span>
  <div class="words">
    <div class="n">PRESTIGE</div>
    <div class="sub"><span class="line"></span><span class="t">Property Care</span><span class="line"></span></div>
    <div class="tag">Lawn &amp; Property Maintenance</div>
  </div>
</div>`;

(async () => {
  const html = page_html(markSvg());
  const browser = await chromium.launch();
  for (const [name, scale, transparent] of JOBS) {
    const page = await browser.newPage({
      viewport: { width: 700, height: 220 },
      deviceScaleFactor: scale,
    });
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    if (!transparent) {
      await page.evaluate(() => (document.body.style.background = '#ffffff'));
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
