/*
 * Redraw the favicon and app icons from the logo mark.
 *
 *     node tools/gen-icons.js            # uses the mark named in build.py
 *     node tools/gen-icons.js mark-level # or any file in assets/img/logo/
 *
 * The mark itself ships as SVG and is what the browser tab actually uses; these
 * PNGs are the fallbacks for older browsers and for iOS home screens, which
 * cannot read an SVG icon. They are drawn on solid white because a transparent
 * dark-green shield disappears on a dark home screen.
 *
 * Needs Playwright + the pre-installed Chromium; nothing else in the build does.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..');
const IMG = path.join(ROOT, 'assets', 'img');

const OUT = [
  ['favicon-32.png', 32],
  ['apple-touch-icon.png', 180],
  ['icon-192.png', 192],
  ['icon-512.png', 512],
];

function markPath() {
  if (process.argv[2]) return path.join(IMG, 'logo', process.argv[2].replace(/\.svg$/, '') + '.svg');
  const build = fs.readFileSync(path.join(__dirname, 'build.py'), 'utf8');
  const m = build.match(/^LOGO_MARK = "([^"]+)"/m);
  if (!m) throw new Error('LOGO_MARK not found in build.py');
  return path.join(ROOT, m[1].replace(/^\//, ''));
}

(async () => {
  const svg = fs.readFileSync(markPath(), 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 512, height: 512 } });

  for (const [name, size] of OUT) {
    // 12% breathing room, matching the padding the header tile gives the mark.
    const inner = Math.round(size * 0.76);
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(
      `<style>html,body{margin:0;width:${size}px;height:${size}px;background:#fff;
         display:grid;place-items:center}svg{width:${inner}px;height:${inner}px}</style>${svg}`
    );
    await page.screenshot({ path: path.join(IMG, name), omitBackground: false });
    console.log('wrote', name, size + 'px');
  }
  await browser.close();
})();
