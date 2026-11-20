/*
 * Render the replacement wordmark line as a mask: "PROPERTY CARE".
 *
 *     node tools/relabel-wordmark.js
 *
 * The client's artwork was drawn with "PROPERTY SERVICES" on its second line.
 * The trading name is Prestige Property Care, so that line is redrawn. This
 * step only produces the letterform mask; tools/gen-logo-assets.py samples the
 * original's own gold out of the artwork and paints the mask with it.
 *
 * Montserrat Bold matches the artwork's face closely: tracked to 24.7px at this
 * render size, the word PROPERTY measures the same 494px of ink it does in the
 * original once scaled to the artwork's 58px cap height. Do not change the font
 * size or tracking without re-measuring against the original.
 *
 * Needs Playwright, the pre-installed Chromium, and fonts.googleapis.com.
 */
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, '..', 'assets', 'img', 'logo', '.wordline.png');
const FONT_PX = 320;
const TRACK = 24.7;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 4200, height: 600 } });
  await page.setContent(`<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap" rel="stylesheet">
<style>
 html,body{margin:0;background:#000}
 #t{font-family:Montserrat,sans-serif;font-weight:700;color:#fff;font-size:${FONT_PX}px;
    letter-spacing:${TRACK}px;white-space:nowrap;display:inline-block;padding:80px 120px;line-height:1}
</style><span id="t">PROPERTY CARE</span>`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  await page.locator('#t').screenshot({ path: OUT });
  await browser.close();
  console.log('wrote', OUT);
})();
