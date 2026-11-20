/*
 * Redraw the favicon and app icons from the logo mark.
 *
 *     node tools/gen-icons.js                    # uses the mark named in build.py
 *     node tools/gen-icons.js mark-tree-512.png  # or any file in assets/img/logo/
 *
 * These PNGs are the browser tab icon and the iOS home-screen icon. They are
 * drawn on the brand's near-black because the mark is gold artwork: on white it
 * keys out to pale yellow and loses its shading, and a transparent mark
 * disappears on a dark home screen either way.
 *
 * Needs Playwright + the pre-installed Chromium; nothing else in the build does.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..');
const IMG = path.join(ROOT, 'assets', 'img');
const BG = '#0D0D0D';

const OUT = [
  ['favicon-32.png', 32],
  ['apple-touch-icon.png', 180],
  ['icon-192.png', 192],
  ['icon-512.png', 512],
];

function markPath() {
  if (process.argv[2]) {
    const given = process.argv[2];
    return path.join(IMG, 'logo', /\.(svg|png)$/i.test(given) ? given : given + '.svg');
  }
  const build = fs.readFileSync(path.join(__dirname, 'build.py'), 'utf8');
  const m = build.match(/^LOGO_MARK = "([^"]+)"/m);
  if (!m) throw new Error('LOGO_MARK not found in build.py');
  // The header file is sized for a 30px slot; icons go up to 512, so prefer a
  // large sibling when one exists.
  const named = path.join(ROOT, m[1].replace(/^\//, ''));
  const big = named.replace(/-\d+\.png$/, '-512.png');
  return fs.existsSync(big) ? big : named;
}

(async () => {
  const file = markPath();
  // A page built with setContent has no origin, so Chromium refuses a file://
  // subresource — a raster mark has to be inlined as a data URI.
  const svg = file.toLowerCase().endsWith('.svg')
    ? fs.readFileSync(file, 'utf8')
    : `<img src="data:image/png;base64,${fs.readFileSync(file).toString('base64')}">`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 512, height: 512 } });

  for (const [name, size] of OUT) {
    // 12% breathing room, matching the padding the header tile gives the mark.
    const inner = Math.round(size * 0.76);
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(
      `<style>html,body{margin:0;width:${size}px;height:${size}px;background:${BG};
         display:grid;place-items:center}svg,img{width:${inner}px;height:${inner}px;
         object-fit:contain;display:block}</style>${svg}`,
      { waitUntil: 'networkidle' }
    );
    await page.screenshot({ path: path.join(IMG, name), omitBackground: false });
    console.log('wrote', name, size + 'px');
  }
  await browser.close();
})();

