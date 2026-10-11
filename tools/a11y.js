const { chromium } = require('playwright');
const path = require('path');
const AXE = path.join(process.cwd(),'node_modules/axe-core/axe.min.js');
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const pages = process.argv[2] ? [process.argv[2]] : ['/','/services/lawn-mowing/','/about/','/contact/','/services/','/thank-you/'];
  let total = 0;
  for (const url of pages) {
    for (const [tag,w,h] of [['mobile',412,823],['desktop',1350,940]]) {
      const ctx = await b.newContext({ viewport:{width:w,height:h}, deviceScaleFactor: tag==='mobile'?1.75:1, isMobile: tag==='mobile', hasTouch: tag==='mobile' });
      const p = await ctx.newPage();
      await p.route('**google.com/maps/embed**', r=>r.fulfill({contentType:'text/html',body:'<body>map</body>'}));
      await p.route('**/external-tracking.js', r=>r.fulfill({contentType:'application/javascript',body:''}));
      await p.goto('http://127.0.0.1:8099'+url,{waitUntil:'networkidle'});
      await p.addScriptTag({ path: AXE });
      const res = await p.evaluate(async () => await window.axe.run(document, {
        runOnly:{ type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice'] }
      }));
      if (res.violations.length) {
        console.log(`\n=== ${url}  [${tag}] ===`);
        for (const v of res.violations) {
          total += v.nodes.length;
          console.log(`  [${v.impact}] ${v.id}: ${v.help}`);
          v.nodes.slice(0,3).forEach(n => console.log(`      ${n.html.replace(/\s+/g,' ').slice(0,140)}`));
          if (v.nodes.length>3) console.log(`      ...and ${v.nodes.length-3} more`);
        }
      }
      await ctx.close();
    }
  }
  console.log(`\nTOTAL violating nodes: ${total}`);
  await b.close();
})();
