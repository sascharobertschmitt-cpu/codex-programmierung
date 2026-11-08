// End-to-end-Test Solomodus: Name eingeben, "Solo gegen Bots" tippen, mitspielen.
// Bots werden vom Host-Client über party_bot_tick gesteuert. Prüft, dass Bots ziehen und
// der Mensch an die Reihe kommt. Aufruf: node tools/solo_smoke.mjs <base-url> <screenshot-prefix>
import { chromium } from 'playwright';
const [base, prefix] = process.argv.slice(2);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let failed = false;
const ok = (name, cond, detail = '') => { console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name} ${detail}`); if (!cond) failed = true; };

const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
page.on('pageerror', e => { console.log('[pageerror]', e.message); failed = true; });
await page.goto(base + '/index.html', { waitUntil: 'load' });
await sleep(1500);
await page.fill('#name', 'CI Solo');
await page.click('#solo');
await sleep(6000);
const chips0 = await page.locator('#players').innerText();
ok('Solo-Spiel gestartet mit 2 Bots', (chips0.match(/🤖/g) || []).length >= 2, chips0.replace(/\n/g, ' | '));

let humanRolls = 0, botSeen = false;
for (let i = 0; i < 70 && humanRolls < 3; i++) {
  const st = await page.evaluate(() => ({ phase: snapshot?.phase, mine: snapshot?.your_turn, status: snapshot?.status,
    botMoved: snapshot?.players.some(p => p.is_bot && (p.position > 0 || p.lap > 0)), judge: snapshot?.you_judge,
    timer: !!snapshot?.timer_started_at, slfMine: snapshot?.slf_mine, letter: snapshot?.slf_letter }));
  if (st.botMoved) botSeen = true;
  if (st.status === 'finished') break;
  try {
    if (st.mine && st.phase === 'ready' && await page.locator('#roll').isEnabled()) { await page.click('#roll'); humanRolls++; }
    else if (st.mine && st.phase === 'event' && await page.locator('#eventnext').isVisible()) await page.click('#eventnext');
    else if (st.mine && st.phase === 'task' && !st.timer) await page.evaluate(() => doAction('timer'));
    else if (st.mine && st.phase === 'task' && st.judge) await page.evaluate(() => doAction('success'));
    else if (st.phase === 'slf' && !st.slfMine) await page.evaluate((L) => rpc('party_slf_submit', { p_code: session.code, p_token: session.token, p_answers: { Stadt: L + 'test' } }), st.letter);
    else if (st.phase === 'slf_review') await page.evaluate(async () => { for (const p of snapshot.slf_results || []) if (p.id !== snapshot.your_id) for (const c of ['Stadt','Land','Fluss','Tier','Beruf']) { try { await rpc('party_slf_vote', { p_code: session.code, p_token: session.token, p_player_id: p.id, p_category: c, p_approved: true }); } catch (e) {} } });
    else if (st.phase === 'slf_results' && st.mine) await page.evaluate(() => doAction('slf_next'));
  } catch (e) { console.log('Schritt', e.message); }
  await sleep(2500);
}
ok('Bots ziehen selbstständig', botSeen);
ok('Mensch kommt an die Reihe und würfelt', humanRolls >= 1, humanRolls + ' Würfe');
const chips = await page.locator('#players').innerText();
console.log('Chips:', chips.replace(/\n/g, ' | '));
await page.screenshot({ path: prefix + '_solo.png' });
await browser.close();
process.exit(failed ? 1 : 0);
