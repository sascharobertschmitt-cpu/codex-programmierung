/*
 * Spielregeln "Rundkurs" für Aal You Ready? (64 Felder, mehrere Runden).
 * Reine Logik ohne 3D, im Browser als window.ClubRules, in Node per require().
 *
 * Feld 0 = Einlass (Start/Ziel). Felder 1..63 behalten die Typen des Hauptspiels.
 * - Über den Einlass ziehen: Einlass-Karte (Gästeliste +Cash oder Einlasskontrolle = aussetzen)
 * - Genau auf dem Einlass landen: Volltreffer, mehr Cash, keine Karte
 * - Wer die letzte Runde vollendet, gewinnt sofort und bleibt am Einlass stehen
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ClubRules = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const FIELDS = 80;
  const ACTIVITIES = [1, 3, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 32, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 56, 57, 59, 61, 63, 65, 67, 69, 71, 73, 75, 77, 79];
  const SLF = [4, 20, 24, 36, 48, 52, 68, 72];
  const SPECIAL = [12, 16, 28, 40, 44, 60, 64, 76];
  const EVENTS = [2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 62, 66, 70, 74, 78];

  const DEFAULTS = {
    laps: 2,
    cashGuestlist: 100,
    cashExact: 200,
    guestlistChance: 0.6,
  };

  function fieldType(n) {
    n = ((n % FIELDS) + FIELDS) % FIELDS;
    if (n === 0) return 'gate';
    if (ACTIVITIES.includes(n)) return 'activity';
    if (SLF.includes(n)) return 'slf';
    if (SPECIAL.includes(n)) return 'special';
    if (EVENTS.includes(n)) return 'event';
    return 'activity';   // Feld 63 (früher Ziel) wird ein normales Aktionsfeld
  }

  function newGame(names, opts) {
    const o = Object.assign({}, DEFAULTS, opts || {});
    return {
      opts: o,
      turn: 0,
      winner: null,
      players: names.map((name, i) => ({ id: i, name, pos: 0, lap: 0, cash: 0, skip: false })),
    };
  }

  // Liefert, wer als Nächstes würfeln darf, und verbraucht dabei Aussetzer.
  function nextTurn(game) {
    const events = [];
    for (let guard = 0; guard < game.players.length * 2; guard++) {
      const p = game.players[game.turn];
      if (!p.skip) return { player: p, events };
      p.skip = false;
      events.push({ type: 'skipped', player: p.id, text: `${p.name} setzt aus (Einlasskontrolle)` });
      game.turn = (game.turn + 1) % game.players.length;
    }
    return { player: game.players[game.turn], events };
  }

  /*
   * Ein Zug: Spieler game.turn zieht `roll` Felder.
   * rng: Funktion () => [0,1) für die Einlass-Karte (testbar mit festem Zufall).
   * Rückgabe: { path: [Feldnummern je Schritt], events: [...] }
   */
  function move(game, roll, rng) {
    rng = rng || Math.random;
    if (game.winner !== null) throw new Error('Spiel ist bereits beendet');
    const p = game.players[game.turn];
    const o = game.opts;
    const path = [];
    const events = [];
    let crossed = 0;
    for (let k = 1; k <= roll; k++) {
      p.pos = (p.pos + 1) % FIELDS;
      path.push(p.pos);
      if (p.pos === 0) {
        p.lap += 1;
        crossed += 1;
        events.push({ type: 'lap', player: p.id, lap: p.lap, text: `${p.name}: Runde ${p.lap} von ${o.laps} geschafft` });
        if (p.lap >= o.laps) {
          game.winner = p.id;
          events.push({ type: 'win', player: p.id, text: `${p.name} gewinnt nach ${o.laps} Runden` });
          return { path, events };
        }
      }
    }
    if (crossed > 0) {
      if (p.pos === 0) {
        p.cash += o.cashExact;
        events.push({ type: 'gate_exact', player: p.id, cash: o.cashExact,
          text: `Volltreffer am Einlass: +${o.cashExact} Cash` });
      } else if (rng() < o.guestlistChance) {
        p.cash += o.cashGuestlist;
        events.push({ type: 'gate_guestlist', player: p.id, cash: o.cashGuestlist,
          text: `Gästeliste: +${o.cashGuestlist} Cash` });
      } else {
        p.skip = true;
        events.push({ type: 'gate_control', player: p.id,
          text: 'Einlasskontrolle: nächste Runde aussetzen' });
      }
    }
    if (p.pos !== 0) {
      events.push({ type: 'field', player: p.id, field: p.pos, fieldType: fieldType(p.pos),
        text: `Feld ${p.pos}: ${LABELS[fieldType(p.pos)]}` });
    }
    game.turn = (game.turn + 1) % game.players.length;
    return { path, events };
  }

  // Club-Würfel (zweiter Würfel, Mario-Party-Prinzip). Normaler W6 + Club-Würfel.
  const CLUB_DIE = [
    { face: '0', value: 0, name: 'Stromausfall', text: 'Stromausfall: nur der normale Würfel zählt' },
    { face: '2', value: 2 },
    { face: '3', value: 3 },
    { face: '5', value: 5 },
    { face: '7', value: 7, name: 'Bass Drop', text: 'Bass Drop: +7' },
    { face: '×2', double: true, name: 'Doppelzeit', text: 'Doppelzeit: normaler Würfel zählt doppelt' },
  ];

  function rollDice(rng) {
    rng = rng || Math.random;
    const white = 1 + Math.floor(rng() * 6);
    const club = CLUB_DIE[Math.floor(rng() * CLUB_DIE.length)];
    const total = club.double ? white * 2 : white + club.value;
    return { white, club, total };
  }

  const STAIRS = [21, 61];
  const LABELS = { gate: 'Einlass', activity: 'Aktion', slf: 'Stadt-Land-Fluss', special: 'Spezial', event: 'Ereignis' };

  return { FIELDS, STAIRS, DEFAULTS, LABELS, CLUB_DIE, fieldType, newGame, nextTurn, move, rollDice };
}));
