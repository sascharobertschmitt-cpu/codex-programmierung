// Diagnose: Solo-Spiel starten, im Hochformat warten und auflisten, welche Elemente über der 3D-Ansicht liegen.
import { chromium } from 'playwright';
const [base, shot] = process.argv.slice(2);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const [w, h, tag] of [[430, 932, 'hoch'], [932, 430, 'quer']]) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.goto(base + '/index.html');
  await sleep(1200);
  await page.fill('#name', 'CI Probe');
  await page.click('#solo');
  await sleep(14000);
  const info = await page.evaluate(() => {
    const desc = (el) => {
      const cs = getComputedStyle(el);
      return `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : ''} z=${cs.zIndex} bg=${cs.backgroundColor} op=${cs.opacity} bf=${cs.backdropFilter} sh=${cs.boxShadow.slice(0, 40)} rect=${JSON.stringify(el.getBoundingClientRect().toJSON(), (k, v) => typeof v === 'number' ? Math.round(v) : v)}`;
    };
    const pts = [[0.5, 0.5], [0.5, 0.35], [0.2, 0.7]];
    return { body: document.body.className, phase: snapshot?.phase,
      stacks: pts.map(([x, y]) => document.elementsFromPoint(innerWidth * x, innerHeight * y).slice(0, 9).map(desc)) };
  });
  console.log('=====', tag, 'body:', info.body, 'phase:', info.phase);
  info.stacks.forEach((s, i) => { console.log('-- Punkt', i); s.forEach(l => console.log('   ', l)); });
  await page.screenshot({ path: shot.replace('.png', '_' + tag + '.png') });
  await page.close();
}
await browser.close();
