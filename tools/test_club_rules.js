// Tests fuer aal-you-ready/play/club-circuit-rules.js  (node tools/test_club_rules.js)
const assert = require('assert');
const R = require('../aal-you-ready/play/club-circuit-rules.js');
let n = 0;
const t = (name, fn) => { fn(); n++; console.log('ok', name); };

t('80 Felder, Typverteilung', () => {
  const c = {};
  for (let i = 0; i < 80; i++) c[R.fieldType(i)] = (c[R.fieldType(i)] || 0) + 1;
  assert.deepStrictEqual(c, { gate: 1, activity: 43, slf: 8, special: 8, event: 20 });
});
t('normaler Zug', () => {
  const g = R.newGame(['A', 'B']);
  const r = R.move(g, 5, () => 0);
  assert.deepStrictEqual(r.path, [1, 2, 3, 4, 5]);
  assert.strictEqual(g.players[0].pos, 5);
  assert.strictEqual(g.turn, 1);
  assert.strictEqual(r.events[0].fieldType, 'activity');
});
t('ueber Einlass: Gaesteliste', () => {
  const g = R.newGame(['A', 'B']); g.players[0].pos = 77;
  const r = R.move(g, 5, () => 0.1);
  assert.strictEqual(g.players[0].pos, 2);
  assert.strictEqual(g.players[0].lap, 1);
  assert.strictEqual(g.players[0].cash, 100);
  assert.ok(r.events.some(e => e.type === 'gate_guestlist'));
});
t('ueber Einlass: Kontrolle -> aussetzen', () => {
  const g = R.newGame(['A', 'B']); g.players[0].pos = 77;
  R.move(g, 5, () => 0.9);
  assert.strictEqual(g.players[0].skip, true);
  R.move(g, 3);                       // B zieht
  const nt = R.nextTurn(g);           // A muss aussetzen -> B ist dran
  assert.strictEqual(nt.player.name, 'B');
  assert.strictEqual(nt.events[0].type, 'skipped');
  assert.strictEqual(g.players[0].skip, false);
});
t('genau auf Einlass: Volltreffer', () => {
  const g = R.newGame(['A']); g.players[0].pos = 76;
  const r = R.move(g, 4, () => 0.9);
  assert.strictEqual(g.players[0].pos, 0);
  assert.strictEqual(g.players[0].cash, 200);
  assert.strictEqual(g.players[0].skip, false);
  assert.ok(!r.events.some(e => e.type === 'field'));
});
t('Sieg nach letzter Runde, bleibt am Einlass', () => {
  const g = R.newGame(['A', 'B'], { laps: 2 }); g.players[0].pos = 78; g.players[0].lap = 1;
  const r = R.move(g, 6);
  assert.strictEqual(g.winner, 0);
  assert.strictEqual(g.players[0].pos, 0);
  assert.deepStrictEqual(r.path, [79, 0]);
  assert.throws(() => R.move(g, 1));
});
t('komplettes Spiel endet immer', () => {
  for (let seed = 1; seed < 200; seed++) {
    let x = seed; const rnd = () => ((x = (x * 16807) % 2147483647) / 2147483647);
    const g = R.newGame(['A', 'B', 'C', 'D'], { laps: 3 });
    let turns = 0;
    while (g.winner === null && turns < 5000) { R.nextTurn(g); R.move(g, 1 + Math.floor(rnd() * 6), rnd); turns++; }
    assert.ok(g.winner !== null, 'kein Sieger bei seed ' + seed);
    assert.strictEqual(g.players[g.winner].lap, 3);
  }
});
t('Club-Wuerfel: Werte und Doppelzeit', () => {
  const seq = (arr) => { let i = 0; return () => arr[i++]; };
  assert.deepStrictEqual(R.rollDice(seq([0.5, 0.0])).total, 4);           // W6=4, Stromausfall
  assert.deepStrictEqual(R.rollDice(seq([0.99, 4.5 / 6])).total, 13);     // W6=6, Bass Drop
  const d = R.rollDice(seq([0.4, 0.99]));                                  // W6=3, Doppelzeit
  assert.strictEqual(d.club.double, true); assert.strictEqual(d.total, 6);
  let sum = 0, N = 60000;
  for (let i = 0; i < N; i++) { const r = R.rollDice(); assert.ok(r.total >= 1 && r.total <= 13); sum += r.total; }
  assert.ok(Math.abs(sum / N - 6.917) < 0.08, 'Mittelwert ' + sum / N);
});
console.log(`${n} Tests bestanden`);
