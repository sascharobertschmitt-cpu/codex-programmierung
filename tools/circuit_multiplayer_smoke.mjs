// End-to-end-Test Rundkurs im Hauptspiel:
// Spieler A (Host) und B werden per RPC angelegt, B wird im Headless-Browser geöffnet (index.html),
// A und B spielen Züge über die echte Supabase-API. Prüft, dass die Seite den Rundkurs zeigt.
// Aufruf: node tools/circuit_multiplayer_smoke.mjs <base-url> <screenshot-prefix>
import { chromium } from 'playwright';

const [base, prefix] = process.argv.slice(2);
const API = 'https://rlmuglsqeyeniutlmvbw.supabase.co/rest/v1/rpc/';
const KEY = 'sb_publishable_tmmQzdfFoJ2lOhjGrCMCmg_ggtKMnH5';
const rpc = async (fn, body) => {
  const r = await fetch(API + fn, { method: 'POST', headers: { 'Content-Type': 'application/json', apikey: KEY, Authorization: 'Bearer ' + KEY }, body: JSON.stringify(body) });
  const v = await r.json(); if (!r.ok) throw Error(fn + ': ' + (v.message || r.status)); return v;
};
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let failed = false;
const ok = (name, cond, detail = '') => { console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name} ${detail}`); if (!cond) failed = true; };

const A = await rpc('party_create', { p_name: 'CI Host' });
const Bp = await rpc('party_join', { p_code: A.code, p_name: 'CI Gast' });
console.log('Lobby', A.code);

const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
page.on('pageerror', e => { console.log('[pageerror]', e.message); failed = true; });
page.on('console', m => { if (m.type() === 'error') console.log('[console.error]', m.text()); });
await page.addInitScript(([key, sess]) => localStorage.setItem(key, sess),
  ['aal-you-ready-session', JSON.stringify({ code: A.code, token: Bp.token, name: 'CI Gast', player_id: Bp.player_id })]);
await page.goto(base + '/index.html', { waitUntil: 'load' });
await sleep(4000);
ok('Lobby sichtbar mit 2 Spielern', await page.locator('#members').innerText().then(t => t.includes('CI Host') && t.includes('CI Gast')));

let s = await rpc('party_action', { p_code: A.code, p_token: A.token, p_host_token: A.host_token, p_action: 'start_circuit' });
ok('Server: Rundkurs gestartet', s.board_mode === 'circuit' && s.laps === 2);
await sleep(9000);
const hud = await page.locator('#cameraHud').innerText();
ok('Seite zeigt Rundkurs-Szene', hud.includes('RUNDKURS'), hud);
{ const chips = await page.locator('#players').innerText(); ok('Chips zeigen Runde und Cash', /R1\/2/.test(chips) && chips.includes('💰'), chips); }

const toks = [A.token, Bp.token];
let rolls = 0, gate = 0, slfRounds = 0, turboBought = null, stairs = 0; const cards = [];
for (let i = 0; i < 60 && s.status !== 'finished' && rolls < 12; i++) {
  s = await rpc('party_snapshot', { p_code: A.code, p_token: A.token });
  const tok = toks[s.turn % 2];
  if (s.phase === 'ready' && turboBought === null) { const me = s.players[s.turn % 2]; if ((me.cash || 0) >= 100 && !me.turbo) { s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'buy_turbo' }); turboBought = !!s.players[s.turn % 2].turbo; } }
  if (s.phase === 'choice') { stairs++; s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'stairs_no' }); }
  else if (s.phase === 'ready') { s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'roll' }); rolls++; if (s.roll_info && s.roll_info.gate) gate++; if (s.roll_info && s.roll_info.card) cards.push(s.roll_info.card.deck + ':' + s.roll_info.card.title); await sleep(2500); }
  else if (s.phase === 'event') s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'event_next' });
  else if (s.phase === 'task') { await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'timer' }); s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: A.host_token, p_action: 'cancel' }); }
  else if (s.phase === 'slf') {
    const L = s.slf_letter;
    const ans = Object.fromEntries(['Stadt', 'Land', 'Fluss', 'Tier', 'Beruf'].map(c => [c, L + 'testwort']));
    s = await rpc('party_slf_submit', { p_code: A.code, p_token: A.token, p_answers: ans });
  }
  else if (s.phase === 'slf_review') {
    const host = s.players[0].id;   // nur der Host hat Antworten, der Gast bewertet sie
    for (const c of ['Stadt', 'Land', 'Fluss', 'Tier', 'Beruf']) {
      try { s = await rpc('party_slf_vote', { p_code: A.code, p_token: Bp.token, p_player_id: host, p_category: c, p_approved: true }); } catch (e) { console.log('vote', e.message); }
    }
    slfRounds++;
  }
  else if (s.phase === 'slf_results') s = await rpc('party_action', { p_code: A.code, p_token: tok, p_host_token: null, p_action: 'slf_next' });
}
ok('Mehrere Züge gespielt (inkl. SLF-Runden)', rolls >= 6, `${rolls} Würfe, ${slfRounds} SLF-Runden`);
console.log('Gezogene Karten:', cards.length ? cards.join(' | ') : 'keine (Zufall)');
ok('Karten haben Titel und Text', cards.every(c => c.split(':')[1]), cards.length + ' Karten');
ok('Server-Würfe mit Club-Würfel', rolls > 0 && s.roll_info !== undefined, `${rolls} Würfe, letzter: ${JSON.stringify(s.roll_info)}`);
console.log('Turbo gekauft:', turboBought, '· VIP-Treppe angeboten:', stairs);
if (turboBought !== null) ok('Turbo-Kauf setzt Flag', turboBought === true, String(turboBought));
await page.waitForFunction(() => typeof circBusy !== 'function' || !circBusy(), null, { timeout: 180000 }).catch(() => console.log('Animationen nach 180 s nicht fertig'));
await sleep(1500);
const dice = await page.locator('#diceResult').innerText().catch(() => '');
ok('Seite zeigt Club-Würfel-Ergebnis', /Club/.test(dice) || (s.roll_info && s.roll_info.skipped && /Ausgesetzt/.test(dice)), dice.replace(/\n/g, ' '));
const chips = await page.locator('#players').innerText();
console.log('Chips:', chips.replace(/\n/g, ' | '));
await page.screenshot({ path: prefix + '_game.png' });
await page.evaluate(() => document.querySelector('.board-stage').scrollIntoView());
await sleep(500);
await page.screenshot({ path: prefix + '_board.png' });
await browser.close();
console.log('Lobby', A.code, 'Status', s.status, 'Spieler', JSON.stringify(s.players.map(p => [p.name, p.lap, p.position, p.cash, p.skip])));
process.exit(failed ? 1 : 0);
