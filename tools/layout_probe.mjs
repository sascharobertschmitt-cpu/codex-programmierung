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
    const veils = [...document.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); return cs.display !== 'none' && cs.visibility !== 'hidden' && e.getClientRects().length && /\d{3,}px/.test(cs.boxShadow.split(',')[0] || ''); }).map(desc);
    const covers = [...document.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return cs.display !== 'none' && r.width >= innerWidth * 0.9 && r.height >= innerHeight * 0.9 && !/^(HTML|BODY|MAIN|CANVAS)$/.test(e.tagName) && cs.backgroundColor !== 'rgba(0, 0, 0, 0)'; }).map(desc);
    return { veils, covers, body: document.body.className, phase: snapshot?.phase,
      stacks: pts.map(([x, y]) => document.elementsFromPoint(innerWidth * x, innerHeight * y).slice(0, 9).map(desc)) };
  });
  console.log('=====', tag, 'body:', info.body, 'phase:', info.phase);
  console.log('-- Schleier-Kandidaten (großer Schatten):'); info.veils.forEach(l => console.log('   V', l));
  console.log('-- Vollflächige Elemente mit Hintergrund:'); info.covers.forEach(l => console.log('   C', l));
  const ov = await page.evaluate(() => {
    const ids = ['.hud-brand', '#updateInLobby', '#turnlabel', '#status', '#players', '#circuitView', '#diceResult', '#roll', '#reopenPopup', '.exit-game', '#notice', '#scoreboard', '#shopBtn'];
    const vis = ids.map(q => [q, document.querySelector(q)]).filter(([, e]) => e && getComputedStyle(e).display !== 'none' && !e.classList.contains('hide') && e.getClientRects().length && e.getBoundingClientRect().width > 0)
      .map(([q, e]) => [q, e.getBoundingClientRect()]);
    const hits = [];
    for (let i = 0; i < vis.length; i++) for (let j = i + 1; j < vis.length; j++) {
      const [qa, a] = vis[i], [qb, b] = vis[j];
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 2 && h > 2) hits.push(`${qa} x ${qb} (${Math.round(w)}x${Math.round(h)})`);
    }
    return { rects: vis.map(([q, r]) => `${q} ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}`), hits };
  });
  console.log('-- HUD-Elemente:'); ov.rects.forEach(l => console.log('   R', l));
  console.log('-- Überlappungen:', ov.hits.length ? '' : 'keine'); ov.hits.forEach(l => console.log('   X', l));
  await page.screenshot({ path: shot.replace('.png', '_' + tag + '.png') });
  if (tag === 'hoch') {
    const fake = async (name, patch) => {
      await page.evaluate((patch) => { circ.busy = 0; circ.calmUntil = 0; dismissedPopupKey = ''; const s = JSON.parse(JSON.stringify(snapshot)); Object.assign(s, patch); if (patch.roll_info) s.roll_info = Object.assign({}, snapshot.roll_info || {}, patch.roll_info); render(s); }, patch);
      await sleep(700);
      await page.screenshot({ path: shot.replace('.png', '_' + tag + '_' + name + '.png') });
    };
    await page.evaluate(() => { sbOpen = true; renderScoreboard(snapshot); }); await sleep(400);
    await page.screenshot({ path: shot.replace('.png', '_' + tag + '_offen.png') });
    await page.evaluate(() => { sbOpen = false; renderScoreboard(snapshot); });
    await fake('ereignis', { phase: 'event', task: '🤖 DJ Bitrate hat die Aufgabe gemeistert! +30 Münzen' });
    await fake('stern', { phase: 'choice', your_turn: true, task: '⭐ Du kommst am Sternhändler vorbei: 1 Stern für 150 Münzen kaufen?', roll_info: { star_offer: true } });
  }
  await page.close();
}
await browser.close();
