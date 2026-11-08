/*
 * 3D-Szene "Club-Rundkurs" für Aal You Ready? (Babylon.js).
 * Wird vom Hauptspiel (index.html) im Modus board_mode='circuit' benutzt.
 * Entstanden aus club-circuit-test.html; Spiellogik liegt NICHT hier, sondern auf dem Server.
 *
 *   const sc = await ClubCircuitScene.create(canvas, { assetBase: './assets/' });
 *   sc.sync(players, activeIndex)         // players: [{id, position, lap}]
 *   await sc.walk(index, fromAbs, toAbs)  // abs = lap * 64 + position, auch rückwärts
 *   sc.setView('follow'|'overview'|'city'); sc.resize(); sc.dispose()
 */
(function (root) {
  'use strict';
  const COLORS = ['#bb38ff', '#278fff', '#f4bb41', '#4ee3ac', '#ff668c', '#f5ecff', '#ff9c4a', '#8e83ff'];
  const TYPE_COLOR = { gate: '#f5ecff', activity: '#bb38ff', event: '#29c6ff', slf: '#2ee6b0', special: '#ffb627' };

  async function create(canvas, opts) {
    const o = Object.assign({ assetBase: './assets/', exterior: true, rain: true, quality: 1, land: 1 }, opts || {});
    const B = BABYLON, R = ClubRules;
    const FAST = false;
    // ------------------------------------------------------------------ Szene
    const engine = new B.Engine(canvas, true, { stencil: true, preserveDrawingBuffer: true }, false);
    engine.setHardwareScalingLevel(1 / Math.min(devicePixelRatio || 1, 2));
    const scene = new B.Scene(engine);
    scene.clearColor = new B.Color4(0.01, 0.01, 0.018, 1);
    scene.ambientColor = new B.Color3(0.02, 0.02, 0.03);
    const ip = scene.imageProcessingConfiguration;
    ip.toneMappingEnabled = true; ip.toneMappingType = B.ImageProcessingConfiguration.TONEMAPPING_ACES;
    ip.exposure = 1.2; ip.contrast = 1.25;
    try {
      scene.environmentTexture = B.CubeTexture.CreateFromPrefilteredData(
        'https://assets.babylonjs.com/environments/environmentSpecular.env', scene);
      scene.environmentIntensity = 0.25;
    } catch (e) { }
    scene.fogMode = B.Scene.FOGMODE_EXP2; scene.fogDensity = 0.018; scene.fogColor = new B.Color3(0.02, 0.012, 0.04);

    const hemi = new B.HemisphericLight('hemi', new B.Vector3(0, 1, 0), scene);
    hemi.intensity = 0.38; hemi.diffuse = new B.Color3(0.6, 0.5, 0.9); hemi.groundColor = new B.Color3(0.05, 0.03, 0.08);
    const glow = new B.GlowLayer('glow', scene, { mainTextureRatio: 0.4, blurKernelSize: 32 });
    glow.intensity = 0.55;

    const pbr = (name, hex, metal, rough, emissive) => {
      const m = new B.PBRMaterial(name, scene);
      m.albedoColor = B.Color3.FromHexString(hex).toLinearSpace();
      m.metallic = metal; m.roughness = rough;
      if (emissive) { m.emissiveColor = B.Color3.FromHexString(emissive); }
      return m;
    };

    // Raum: Betonboden, dunkle Ziegelwände, Säulen
    const floor = B.MeshBuilder.CreateGround('floor', { width: 30, height: 44 }, scene);
    floor.material = pbr('concrete', '#ffffff', 0, 0.42);
    {   // Beton: Körnung, Flecken, Pfützen (glänzend), alte Hallenmarkierungen
      const ft = new B.DynamicTexture('floorTex', { width: 1024, height: 1024 }, scene, true);
      const g = ft.getContext();
      g.fillStyle = '#2a2830'; g.fillRect(0, 0, 1024, 1024);
      let sd = 3; const rr = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
      for (let i = 0; i < 9000; i++) { const v = 30 + rr() * 22; g.fillStyle = `rgba(${v},${v},${v + 4},0.5)`; g.fillRect(rr() * 1024, rr() * 1024, 2 + rr() * 3, 2 + rr() * 3); }
      for (let i = 0; i < 26; i++) { g.fillStyle = `rgba(10,9,14,${0.12 + rr() * 0.18})`; g.beginPath(); g.ellipse(rr() * 1024, rr() * 1024, 30 + rr() * 90, 20 + rr() * 60, rr() * 3, 0, 7); g.fill(); }
      g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 3;                          // Fugen
      for (let k = 0; k <= 1024; k += 256) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k, 1024); g.stroke(); g.beginPath(); g.moveTo(0, k); g.lineTo(1024, k); g.stroke(); }
      g.strokeStyle = 'rgba(214,190,60,0.28)'; g.lineWidth = 14; g.setLineDash([60, 40]);   // alte Fahrwege der Halle
      g.beginPath(); g.moveTo(0, 180); g.lineTo(1024, 180); g.stroke(); g.setLineDash([]);
      ft.update();
      floor.material.albedoTexture = ft; ft.uScale = 3; ft.vScale = 4.4;
    }
    floor.receiveShadows = true;
    // Außenwelt (Ruinenhalle + dystopische Stadt). ?ext=0 schaltet sie ab, ?q=0.5 reduziert Details.
    const EXT = o.exterior !== false;
    let exterior = null;
    if (EXT && window.ClubExterior) {
      exterior = ClubExterior.build(scene, B, { hall: { hw: 15, hl: 22, h: 8.5 }, glow,
        rain: o.rain !== false, quality: o.quality || 1 });
    } else {
      const wallMat = pbr('brick', '#231a20', 0, 0.85);
      [[0, 22, 30, 0.4], [0, -22, 30, 0.4], [15, 0, 0.4, 44], [-15, 0, 0.4, 44]].forEach(([x, z, w, d], i) => {
        const wl = B.MeshBuilder.CreateBox('wall' + i, { width: w, height: 7, depth: d }, scene);
        wl.position.set(x, 3.5, z); wl.material = wallMat;
      });
    }
    const pillarMat = pbr('steel', '#2a2a33', 0.8, 0.35);
    [[-10.5, -14], [10.5, -14], [-10.5, 0], [10.5, 0], [-10.5, 14], [10.5, 14]].forEach(([x, z], i) => {
      const p = B.MeshBuilder.CreateBox('pillar' + i, { width: 0.6, height: 7, depth: 0.6 }, scene);
      p.position.set(x, 3.5, z); p.material = pillarMat;
      const strip = B.MeshBuilder.CreateBox('pstrip' + i, { width: 0.62, height: 0.06, depth: 0.62 }, scene);
      strip.position.set(x, 2.4, z); strip.material = pbr('neonp' + i, '#000000', 0, 1, i % 2 ? '#29c6ff' : '#bb38ff');
    });

    // ------------------------------------------------------------ Rundkurs
    const HW = 6.0, HL = 12.0, RC = 4.0;
    const seg = [];
    const L = (ax, az, bx, bz) => seg.push({ t: 'l', ax, az, bx, bz, len: Math.hypot(bx - ax, bz - az) });
    const C = (cx, cz, a0, a1) => seg.push({ t: 'c', cx, cz, a0, a1, len: Math.abs(a1 - a0) * RC });
    L(0, -HL, HW - RC, -HL);
    C(HW - RC, -HL + RC, -Math.PI / 2, 0);
    L(HW, -HL + RC, HW, HL - RC);
    C(HW - RC, HL - RC, 0, Math.PI / 2);
    L(HW - RC, HL, -HW + RC, HL);
    C(-HW + RC, HL - RC, Math.PI / 2, Math.PI);
    L(-HW, HL - RC, -HW, -HL + RC);
    C(-HW + RC, -HL + RC, Math.PI, 1.5 * Math.PI);
    L(-HW + RC, -HL, 0, -HL);
    const TOTAL = seg.reduce((s, a) => s + a.len, 0);
    const SPACING = TOTAL / R.FIELDS;
    const at = (d) => {
      d = ((d % TOTAL) + TOTAL) % TOTAL;
      for (const s of seg) {
        if (d <= s.len + 1e-9) {
          const f = d / s.len;
          if (s.t === 'l') return { x: s.ax + (s.bx - s.ax) * f, z: s.az + (s.bz - s.az) * f, ang: Math.atan2(s.bz - s.az, s.bx - s.ax) };
          const a = s.a0 + (s.a1 - s.a0) * f;
          return { x: s.cx + RC * Math.cos(a), z: s.cz + RC * Math.sin(a), ang: a + Math.PI / 2 };
        }
        d -= s.len;
      }
    };
    // Höhenprofil: flach am Einlass, Anstieg bis vor den DJ, kleine Wellen. Periodisch -> Runde schließt.
    const LAND = o.land ?? 1;
    // Gelände: flacher Einlass, Hügelkette bis gut 2 m, jedes Podest mit eigenem Versatz.
    const JIT = [0, 0.22, -0.1, 0.3, 0.05, -0.18, 0.15, 0.35, -0.05, 0.25];
    const heightAt = (n) => {
      const u = n / R.FIELDS * Math.PI * 2;
      const g = Math.min(1, Math.min(n, R.FIELDS - n) / 4);          // Rampe am Einlass
      const hill = 1.0 * (1 - Math.cos(u)) + 0.55 * Math.sin(3 * u + 0.6) * Math.sin(u / 2)
        + 0.25 * Math.sin(5 * u + 2) * Math.sin(u / 2);
      return Math.max(0, (Math.max(0.05, hill) + 0.5 * JIT[(n * 7) % 10]) * g) * LAND;
    };
    const tiles = [];
    const truss0 = pbr('truss', '#3a3a44', 0.9, 0.3);
    for (let n = 0; n < R.FIELDS; n++) tiles.push(Object.assign(at(n * SPACING), { h: heightAt(n) }));

    // Feld-Icons als Canvas-Texturen (eine pro Typ)
    function iconTexture(type, color) {
      const t = new B.DynamicTexture('icon_' + type, { width: 256, height: 256 }, scene, true);
      const g = t.getContext();
      g.clearRect(0, 0, 256, 256);
      g.fillStyle = '#000'; g.fillRect(0, 0, 256, 256);
      g.strokeStyle = '#fff'; g.lineWidth = 10; g.lineJoin = 'round';
      const rr = (x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
      rr(14, 14, 228, 228, 28); g.stroke();
      g.globalAlpha = 0.12; g.fillStyle = '#fff'; g.fill(); g.globalAlpha = 1;
      g.lineWidth = 9; g.fillStyle = '#fff';
      const card = (inner) => {          // Spielkarte hochkant, Symbol innen
        g.save(); g.translate(128, 128); g.rotate(-0.12);
        rr(-50, -70, 100, 140, 12); g.stroke();
        inner(); g.restore();
      };
      if (type === 'activity') {           // Theatermaske
        g.beginPath(); g.moveTo(66, 70); g.quadraticCurveTo(128, 52, 190, 70); g.quadraticCurveTo(194, 170, 128, 206); g.quadraticCurveTo(62, 170, 66, 70); g.closePath(); g.stroke();
        g.beginPath(); g.ellipse(104, 112, 15, 9, 0.2, 0, 7); g.fill(); g.beginPath(); g.ellipse(152, 112, 15, 9, -0.2, 0, 7); g.fill();
        g.beginPath(); g.arc(128, 146, 26, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke();
      } else if (type === 'event') {        // Ereigniskarte mit Blitz
        card(() => { g.beginPath(); g.moveTo(10, -46); g.lineTo(-22, 6); g.lineTo(2, 6); g.lineTo(-10, 48); g.lineTo(24, -10); g.lineTo(0, -10); g.closePath(); g.fill(); });
      } else if (type === 'special') {      // Aufgabenkarte mit Stern
        card(() => { g.beginPath(); for (let i = 0; i < 10; i++) { const r = i % 2 ? 15 : 36, a = -Math.PI / 2 + i * Math.PI / 5; g.lineTo(r * Math.cos(a), r * Math.sin(a)); } g.closePath(); g.fill(); });
      } else if (type === 'slf') {
        g.font = 'bold 76px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('SLF', 128, 132);
      } else if (type === 'gate') {
        g.font = 'bold 44px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
        g.fillText('START', 128, 104); g.fillText('ZIEL', 128, 156);
      }
      // Laufrichtung: zwei kleine Pfeile am vorderen Rand (lokal +x = Laufrichtung)
      if (type !== 'gate') {
        g.globalAlpha = 0.75; g.lineWidth = 7;
        [222, 238].forEach(x => { g.beginPath(); g.moveTo(x - 10, 108); g.lineTo(x, 128); g.lineTo(x - 10, 148); g.stroke(); });
        g.globalAlpha = 1;
      }
      t.update(); t.hasAlpha = false;
      return t;
    }

    const base = B.MeshBuilder.CreateBox('tileBase', { width: 0.99, height: 0.16, depth: 1.24 }, scene);
    base.material = pbr('tileBody', '#3a3a48', 0.75, 0.32);
    base.receiveShadows = true;
    const tops = {};
    for (const type of Object.keys(TYPE_COLOR)) {
      const top = B.MeshBuilder.CreateGround('tileTop_' + type, { width: 0.88, height: 1.12 }, scene);
      const m = new B.PBRMaterial('tileTopMat_' + type, scene);
      m.albedoColor = new B.Color3(0.02, 0.02, 0.03); m.metallic = 0.2; m.roughness = 0.25;
      m.emissiveTexture = iconTexture(type, TYPE_COLOR[type]);
      m.emissiveColor = B.Color3.FromHexString(TYPE_COLOR[type]);
      m.emissiveIntensity = 1.3;
      top.material = m;
      tops[type] = top;
    }
    const rotY = (ang) => B.Quaternion.RotationAxis(B.Axis.Y, -ang);
    // Neonkante oben am Podest, eine Variante pro Feldtyp
    const edges = {};
    for (const type of Object.keys(TYPE_COLOR)) {
      const e = B.MeshBuilder.CreateBox('tileEdge_' + type, { width: 1.0, height: 0.025, depth: 1.26 }, scene);
      const m = new B.PBRMaterial('tileEdgeMat_' + type, scene);
      m.albedoColor = new B.Color3(0, 0, 0); m.emissiveColor = B.Color3.FromHexString(TYPE_COLOR[type]).scale(0.55);
      e.material = m; edges[type] = e;
    }
    tiles.forEach((t, n) => {
      const big = n === 0 ? 1.25 : 1;
      const hBase = 0.16 + t.h;                      // Podesthöhe inkl. Grundplatte
      base.thinInstanceAdd(B.Matrix.Compose(new B.Vector3(big, hBase / 0.16, big), rotY(t.ang), new B.Vector3(t.x, hBase / 2, t.z)));
      edges[R.fieldType(n)].thinInstanceAdd(B.Matrix.Compose(new B.Vector3(big, 1, big), rotY(t.ang),
        new B.Vector3(t.x, hBase - 0.03, t.z)));
      tops[R.fieldType(n)].thinInstanceAdd(B.Matrix.Compose(new B.Vector3(big, 1, big), rotY(t.ang),
        new B.Vector3(t.x, hBase + 0.005, t.z)));
    });

    // Prüfungen zur Streckengeometrie
    const gaps = tiles.map((t, i) => { const u = tiles[(i + 1) % tiles.length]; return Math.hypot(u.x - t.x, u.z - t.z); });
    const steps = tiles.map((t, i) => Math.abs(tiles[(i + 1) % tiles.length].h - t.h));

    // Fahrbahn: dunkler Belag unter dem ganzen Kurs, LED-Linien innen und außen
    {
      const left = [], right = [], inL = [], outL = [];
      for (let d = 0; d <= TOTAL + 1e-6; d += 0.25) {
        const p = at(d), nx = -Math.sin(p.ang), nz = Math.cos(p.ang);
        const out = (nx * p.x + nz * p.z) >= 0 ? 1 : -1;
        left.push(new B.Vector3(p.x + nx * 0.9, 0.006, p.z + nz * 0.9));
        right.push(new B.Vector3(p.x - nx * 0.9, 0.006, p.z - nz * 0.9));
        inL.push(new B.Vector3(p.x - out * nx * 0.86, 0.02, p.z - out * nz * 0.86));
        outL.push(new B.Vector3(p.x + out * nx * 0.86, 0.02, p.z + out * nz * 0.86));
      }
      const lane = B.MeshBuilder.CreateRibbon('lane', { pathArray: [left, right], closePath: true, sideOrientation: B.Mesh.DOUBLESIDE }, scene);
      lane.material = pbr('laneM', '#121118', 0.1, 0.55); lane.receiveShadows = true;
      [[inL, '#29c6ff'], [outL, '#bb38ff']].forEach(([path, col], i) => {
        const tube = B.MeshBuilder.CreateTube('laneLed' + i, { path: path.concat([path[0]]), radius: 0.022, tessellation: 6 }, scene);
        tube.material = pbr('laneLedM' + i, '#000000', 0, 1, col); tube.material.emissiveColor = tube.material.emissiveColor.scale(0.7);
      });
    }
    // Nummernschilder an jedem 8. Feld, außen am Kurs
    for (let n = 8; n < R.FIELDS; n += 8) {
      const t = tiles[n], nx = -Math.sin(t.ang), nz = Math.cos(t.ang);
      const out = (nx * t.x + nz * t.z) >= 0 ? 1 : -1;
      const pos = new B.Vector3(t.x + out * nx * 1.05, 0, t.z + out * nz * 1.05);
      const hgt = t.h + 1.25;
      const pole = B.MeshBuilder.CreateCylinder('numPole' + n, { diameter: 0.05, height: hgt, tessellation: 8 }, scene);
      pole.position.set(pos.x, hgt / 2, pos.z); pole.material = truss0;
      const tx = new B.DynamicTexture('numTex' + n, { width: 128, height: 128 }, scene, true);
      const g = tx.getContext(); g.fillStyle = '#07060c'; g.fillRect(0, 0, 128, 128);
      g.strokeStyle = '#f5ecff'; g.lineWidth = 6; g.strokeRect(5, 5, 118, 118);
      g.fillStyle = '#fff'; g.font = 'bold 66px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(n), 64, 68); tx.update();
      const sign = B.MeshBuilder.CreatePlane('numSign' + n, { size: 0.62, sideOrientation: B.Mesh.DOUBLESIDE }, scene);
      sign.position.set(pos.x, hgt + 0.3, pos.z);
      sign.billboardMode = B.Mesh.BILLBOARDMODE_Y;
      const sm2 = new B.StandardMaterial('numM' + n, scene); sm2.disableLighting = true; sm2.emissiveTexture = tx; sign.material = sm2;
      glow.addExcludedMesh(sign);
    }

    // Einlass-Tor (Start/Ziel) über Feld 0
    const gateRoot = new B.TransformNode('gate', scene);
    gateRoot.position.set(tiles[0].x, 0, tiles[0].z);
    const truss = truss0;
    const neonW = pbr('neonW', '#000000', 0, 1, '#f5ecff');
    [-1, 1].forEach(s => {
      const p = B.MeshBuilder.CreateBox('gatePost', { width: 0.22, height: 2.9, depth: 0.22 }, scene);
      p.parent = gateRoot; p.position.set(0, 1.45, s * 0.95); p.material = truss;
      const n = B.MeshBuilder.CreateBox('gateNeon', { width: 0.04, height: 2.6, depth: 0.04 }, scene);
      n.parent = gateRoot; n.position.set(-0.12, 1.4, s * 0.95); n.material = neonW;
    });
    const beam = B.MeshBuilder.CreateBox('gateBeam', { width: 0.24, height: 0.24, depth: 2.12 }, scene);
    beam.parent = gateRoot; beam.position.y = 2.9; beam.material = truss;
    const signTex = new B.DynamicTexture('signTex', { width: 512, height: 128 }, scene, true);
    { const g = signTex.getContext(); g.fillStyle = '#000'; g.fillRect(0, 0, 512, 128);
      g.strokeStyle = '#ff4fd8'; g.lineWidth = 8; g.strokeRect(10, 10, 492, 108);
      g.fillStyle = '#fff'; g.font = 'bold 62px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText('EINLASS', 256, 66); signTex.update(); }
    const sign = B.MeshBuilder.CreatePlane('sign', { width: 1.9, height: 0.48, sideOrientation: B.Mesh.DOUBLESIDE }, scene);
    sign.parent = gateRoot; sign.position.y = 2.5; sign.rotation.y = Math.PI / 2;
    const sm = new B.StandardMaterial('signMat', scene);
    sm.disableLighting = true; sm.emissiveTexture = signTex; sign.material = sm; glow.addExcludedMesh(sign);

    // DJ-Booth am Kopfende (Platzhalter, wird später ein eigenes GLB)
    const booth = new B.TransformNode('booth', scene);
    booth.position.set(0, 0.25, HL - 4.4);
    const riser = B.MeshBuilder.CreateBox('riser', { width: 5.2, height: 0.6, depth: 2.6 }, scene);
    riser.parent = booth; riser.position.y = 0.05; riser.material = pbr('riser', '#16161c', 0.3, 0.6);
    const desk = B.MeshBuilder.CreateBox('desk', { width: 2.8, height: 1.0, depth: 0.85 }, scene);
    desk.parent = booth; desk.position.set(0, 0.85, -0.3); desk.material = pbr('desk', '#101014', 0.4, 0.5);
    const eqTex = new B.DynamicTexture('eqTex', { width: 512, height: 128 }, scene, true);
    const drawEq = (t) => { const g = eqTex.getContext(); g.fillStyle = '#000'; g.fillRect(0, 0, 512, 128);
      for (let i = 0; i < 48; i++) { const h = 18 + 92 * Math.abs(Math.sin(i * 0.45 + t * 3) * Math.cos(i * 0.13 + t));
        g.fillStyle = i % 2 ? '#29c6ff' : '#bb38ff'; g.fillRect(6 + i * 10.5, 64 - h / 2, 6, h); } eqTex.update(); };
    drawEq(0);
    const eq = B.MeshBuilder.CreatePlane('eq', { width: 2.6, height: 0.62 }, scene);
    eq.parent = booth; eq.position.set(0, 0.85, -0.73); eq.rotation.y = 0;
    const eqm = new B.StandardMaterial('eqm', scene); eqm.disableLighting = true; eqm.emissiveTexture = eqTex; eq.material = eqm; glow.addExcludedMesh(eq);
    [-0.7, 0.7].forEach((x, i) => {
      const deck = B.MeshBuilder.CreateBox('deck' + i, { width: 0.5, height: 0.06, depth: 0.4 }, scene);
      deck.parent = booth; deck.position.set(x, 1.38, -0.3); deck.material = pbr('deckm' + i, '#25252c', 0.6, 0.35);
      const pl = B.MeshBuilder.CreateCylinder('platter' + i, { diameter: 0.3, height: 0.012, tessellation: 32 }, scene);
      pl.parent = booth; pl.position.set(x, 1.42, -0.3); pl.material = pbr('pl' + i, '#8a8a95', 1, 0.25);
    });
    const mixer = B.MeshBuilder.CreateBox('mixer', { width: 0.36, height: 0.08, depth: 0.4 }, scene);
    mixer.parent = booth; mixer.position.set(0, 1.39, -0.3); mixer.material = pbr('mixm', '#1d1d24', 0.5, 0.4);
    const wall = B.MeshBuilder.CreatePlane('ledwall', { width: 8, height: 3.2 }, scene);
    wall.position.set(0, 4.4, HL + 2.3);
    const wallTex = new B.DynamicTexture('wallTex', { width: 512, height: 205 }, scene, true);
    const wm = new B.StandardMaterial('wallm', scene); wm.disableLighting = true; wm.emissiveTexture = wallTex; wall.material = wm; glow.addExcludedMesh(wall);
    const drawWall = (t) => { const g = wallTex.getContext(); g.fillStyle = '#05030a'; g.fillRect(0, 0, 512, 205);
      g.strokeStyle = '#bb38ff'; g.lineWidth = 7; const s = 1 + 0.06 * Math.sin(t * 4);
      g.beginPath(); g.moveTo(256 - 70 * s, 50); g.lineTo(256 + 70 * s, 50); g.lineTo(256, 50 + 115 * s); g.closePath(); g.stroke();
      g.strokeStyle = '#29c6ff'; g.lineWidth = 2;
      for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(0, 30 + i * 30 + 6 * Math.sin(t * 2 + i)); g.lineTo(512, 30 + i * 30 - 6 * Math.sin(t * 2 + i)); g.globalAlpha = 0.25; g.stroke(); g.globalAlpha = 1; }
      wallTex.update(); };
    drawWall(0);

    // Licht: Moving-Head-artige Spots über der Tanzfläche
    const spots = [];
    [[-4, '#bb38ff'], [4, '#29c6ff'], [-1.5, '#ff4fd8'], [1.5, '#2ee6b0']].forEach(([x, c], i) => {
      const sp = new B.SpotLight('spot' + i, new B.Vector3(x, 6.5, HL - 6), new B.Vector3(0, -1, -0.4), 0.7, 6, scene);
      sp.diffuse = B.Color3.FromHexString(c); sp.intensity = 170; spots.push(sp);
    });
    const key = new B.DirectionalLight('key', new B.Vector3(0.3, -1, 0.45), scene);
    key.position = new B.Vector3(-6, 14, -14); key.intensity = 0.55; key.diffuse = new B.Color3(0.85, 0.8, 1);
    const shadows = new B.ShadowGenerator(1024, key);
    shadows.useBlurExponentialShadowMap = true; shadows.blurKernel = 12; shadows.darkness = 0.45;

    // ------------------------------------------- Kartenstapel in der Mitte
    // Links Ereigniskarten (cyan), rechts Aufgabenkarten (gold). drawCard() hebt eine Karte ab.
    const DECKS = { ereignis: { x: -0.85, col: '#29c6ff', label: 'EREIGNIS', icon: '⚡' },
                    aufgabe: { x: 0.85, col: '#ffb627', label: 'AUFGABE', icon: '★' } };
    const CARD_Z = -6.2, CARD_W = 0.9, CARD_D = 1.25;
    const cardFace = (deck, title, body) => {
      const d = DECKS[deck];
      const t = new B.DynamicTexture('cardTex_' + deck + (title ? '_t' : ''), { width: 256, height: 356 }, scene, true);
      const g = t.getContext();
      g.fillStyle = '#0b0a14'; g.fillRect(0, 0, 256, 356);
      g.strokeStyle = d.col; g.lineWidth = 10; g.strokeRect(10, 10, 236, 336);
      g.fillStyle = d.col; g.textAlign = 'center'; g.textBaseline = 'middle';
      if (!title) {
        g.font = 'bold 120px system-ui,sans-serif'; g.fillText(d.icon, 128, 150);
        g.font = 'bold 34px system-ui,sans-serif'; g.fillText(d.label, 128, 270);
      } else {
        g.font = 'bold 22px system-ui,sans-serif'; g.fillText(d.label + 'KARTE', 128, 44);
        g.fillStyle = '#fff'; g.font = 'bold 30px system-ui,sans-serif';
        const words = String(title).split(' '); let line = '', y = 120; const lines = [];
        words.forEach(w => { const tl = line ? line + ' ' + w : w; if (g.measureText(tl).width > 210) { lines.push(line); line = w; } else line = tl; });
        lines.push(line); lines.slice(0, 4).forEach((l, i) => g.fillText(l, 128, y + i * 38));
        g.fillStyle = d.col; g.font = 'bold 70px system-ui,sans-serif'; g.fillText(d.icon, 128, 300);
      }
      t.update(); return t;
    };
    const decks = {};
    Object.entries(DECKS).forEach(([key, d]) => {
      const root = new B.TransformNode('deck_' + key, scene);
      root.position.set(d.x, 0, CARD_Z);
      const ped = B.MeshBuilder.CreateBox('deckPed_' + key, { width: 1.25, height: 0.7, depth: 1.65 }, scene);
      ped.parent = root; ped.position.y = 0.35; ped.material = pbr('deckPedM_' + key, '#1b1b24', 0.6, 0.35);
      ped.receiveShadows = true;
      const edge = B.MeshBuilder.CreateBox('deckEdge_' + key, { width: 1.27, height: 0.03, depth: 1.67 }, scene);
      edge.parent = root; edge.position.y = 0.69; edge.material = pbr('deckEdgeM_' + key, '#000000', 0, 1, d.col); edge.material.emissiveColor = edge.material.emissiveColor.scale(0.6);
      const sideMat = pbr('cardSide_' + key, '#e8e4f2', 0, 0.6);
      for (let k = 0; k < 9; k++) {
        const c = B.MeshBuilder.CreateBox('deckCard_' + key + k, { width: CARD_W, height: 0.018, depth: CARD_D }, scene);
        c.parent = root; c.position.set((Math.sin(k * 2.1) * 0.03), 0.72 + k * 0.02, Math.cos(k * 1.7) * 0.03);
        c.rotation.y = Math.sin(k * 3.3) * 0.05; c.material = sideMat; shadows.addShadowCaster(c);
      }
      const faceMat = new B.StandardMaterial('cardFaceM_' + key, scene);
      faceMat.disableLighting = true; faceMat.emissiveTexture = cardFace(key); faceMat.diffuseTexture = null;
      const top = B.MeshBuilder.CreatePlane('deckTop_' + key, { width: CARD_W * 0.98, height: CARD_D * 0.98 }, scene);
      top.parent = root; top.rotation.x = Math.PI / 2; top.position.y = 0.72 + 9 * 0.02 + 0.001; top.material = faceMat;
      glow.addExcludedMesh(top);
      // schwebende Karte, die beim Ziehen hochfliegt
      const fly = new B.TransformNode('deckFly_' + key, scene);
      fly.parent = root; fly.position.y = 0.92; fly.setEnabled(false);
      const back = B.MeshBuilder.CreatePlane('flyBack_' + key, { width: CARD_W, height: CARD_D, sideOrientation: B.Mesh.DOUBLESIDE }, scene);
      back.parent = fly; back.material = faceMat; glow.addExcludedMesh(back);
      const frontMat = new B.StandardMaterial('flyFrontM_' + key, scene); frontMat.disableLighting = true;
      const front = B.MeshBuilder.CreatePlane('flyFront_' + key, { width: CARD_W, height: CARD_D }, scene);
      front.parent = fly; front.position.z = -0.004; front.material = frontMat; glow.addExcludedMesh(front);
      const lamp = new B.PointLight('deckLamp_' + key, new B.Vector3(d.x, 2.2, CARD_Z), scene);
      lamp.diffuse = B.Color3.FromHexString(d.col); lamp.intensity = 1.6; lamp.range = 3.5;
      lamp.includedOnlyMeshes = [ped].concat(root.getChildMeshes(false));
      decks[key] = { root, fly, front, frontMat, t: -1 };
    });
    let flyTex = null;
    const drawCard = (deck, title) => {
      const dk = decks[deck]; if (!dk) return;
      Object.values(decks).forEach(o => { o.fly.setEnabled(false); o.t = -1; });
      if (flyTex) flyTex.dispose();
      flyTex = cardFace(deck, title); dk.frontMat.emissiveTexture = flyTex;
      dk.fly.setEnabled(true); dk.t = 0;
    };
    scene.onBeforeRenderObservable.add(() => {
      const dt = engine.getDeltaTime() / 1000;
      Object.values(decks).forEach(o => {
        if (o.t < 0) return;
        o.t += dt;
        const u = Math.min(1, o.t / 1.1);                              // hochheben und umdrehen
        const e = 1 - Math.pow(1 - u, 3);
        o.fly.position.y = 0.92 + e * 1.75 + Math.sin(o.t * 2) * 0.05 * e;
        o.fly.position.x = -o.root.position.x * e;                       // zur Mitte zwischen den Stapeln
        o.fly.rotation.x = Math.PI / 2 * (1 - e);                       // flach -> aufrecht
        // aufrecht zur Kamera drehen
        const cp = cam.position, wp = o.fly.getAbsolutePosition();
        o.fly.rotation.y = Math.atan2(wp.x - cp.x, wp.z - cp.z) * e;
        if (o.t > 9) { o.fly.setEnabled(false); o.t = -1; }
      });
    });

    // PA-Stacks links und rechts vom DJ (eigene GLBs: Sub + Topteil)
    let paLoaded = false;
    try {
      const [sub, top] = await Promise.all([
        B.SceneLoader.LoadAssetContainerAsync(o.assetBase, 'club_sub_118.glb', scene, null, '.glb'),
        B.SceneLoader.LoadAssetContainerAsync(o.assetBase, 'club_speaker_pa212.glb', scene, null, '.glb'),
      ]);
      [-3.3, 3.3].forEach((x, i) => {
        const s = sub.instantiateModelsToScene(n => n + '_s' + i, false);
        const t = top.instantiateModelsToScene(n => n + '_t' + i, false);
        const r1 = s.rootNodes[0], r2 = t.rootNodes[0];
        const stack = new B.TransformNode('stack' + i, scene);
        r1.parent = stack; r2.parent = stack; r2.position.y = 0.654;
        stack.position.set(x, 0, HL - 4.6);
        stack.rotation.y = Math.PI + (x < 0 ? -0.18 : 0.18);   // zur Tanzfläche, leicht eingedreht
        stack.getChildMeshes().forEach(m => shadows.addShadowCaster(m));
      });
      paLoaded = true;
    } catch (e) { console.warn('PA nicht geladen', e); }


    // ------------------------------------------------------------ DJ-Booth + Lichtrigg (eigene GLBs)
    const heads = [];
    let rigLoaded = false;
    try {
      const load = (f) => B.SceneLoader.LoadAssetContainerAsync(o.assetBase, f, scene, null, '.glb');
      const [dj, tr, mh] = await Promise.all([load('club_dj_booth.glb'), load('club_truss_3m.glb'), load('club_moving_head.glb')]);
      // Platzhalter-Pult entfernen
      ['desk', 'eq', 'deck0', 'deck1', 'platter0', 'platter1', 'mixer'].forEach(n => { const m = scene.getMeshByName(n); if (m) m.dispose(); });
      const place = (container, name, pos, rot) => {
        const inst = container.instantiateModelsToScene(n => name + '_' + n, false);
        const holder = new B.TransformNode(name, scene);
        inst.rootNodes.forEach(r => { r.parent = holder; });
        holder.position.copyFrom(pos);
        if (rot) holder.rotation.copyFrom(rot);
        return { holder, inst };
      };
      // DJ-Booth auf dem Podest, Front zur Tanzfläche (-Z)
      const d = place(dj, 'djbooth', new B.Vector3(0, 0, 0), new B.Vector3(0, Math.PI, 0));
      d.holder.parent = booth; d.holder.position.set(0, 0.35, -0.15);
      d.holder.getChildMeshes().forEach(m => shadows.addShadowCaster(m));

      // Rigg: 4 Türme (je 2 x 3 m senkrecht), vorne und hinten je 3 Segmente quer
      const zF = HL - 6.4, zR = HL - 2.9, xT = 4.65, yTop = 6.0;
      [[-xT, zF], [xT, zF], [-xT, zR], [xT, zR]].forEach(([x, z], i) => {
        [1.5, 4.5].forEach((y, k) => place(tr, `tower${i}_${k}`, new B.Vector3(x, y, z), new B.Vector3(0, 0, Math.PI / 2)));
      });
      [zF, zR].forEach((z, j) => [-3, 0, 3].forEach((x, k) =>
        place(tr, `beam${j}_${k}`, new B.Vector3(x, yTop, z), new B.Vector3(0, 0, 0))));

      // Moving Heads kopfüber unter dem vorderen Träger
      const beamCols = ['#ff4fd8', '#29c6ff', '#f5ecff', '#2ee6b0', '#bb38ff', '#ffb627'];
      [-3.75, -2.25, -0.75, 0.75, 2.25, 3.75].forEach((x, i) => {
        const h = place(mh, 'mh' + i, new B.Vector3(x, yTop, zF), new B.Vector3(0, 0, Math.PI));
        const nodes = h.holder.getDescendants(false);
        const pan = nodes.find(n => n.name.endsWith('MH_Pan'));
        const tilt = nodes.find(n => n.name.endsWith('MH_Tilt'));
        if (!pan || !tilt) return;
        pan.rotationQuaternion = null; tilt.rotationQuaternion = null;
        const cone = B.MeshBuilder.CreateCylinder('mhBeam' + i, { diameterTop: 2.4, diameterBottom: 0.09, height: 10, tessellation: 20, cap: B.Mesh.NO_CAP }, scene);
        cone.parent = tilt; cone.position.y = 0.16 + 5;
        const bm = new B.StandardMaterial('mhBeamMat' + i, scene);
        bm.disableLighting = true; bm.emissiveColor = B.Color3.FromHexString(beamCols[i]);
        bm.alpha = 0.10; bm.alphaMode = B.Engine.ALPHA_ADD; bm.backFaceCulling = false;
        cone.material = bm;
        glow.addExcludedMesh(cone);
        heads.push({ pan, tilt, bm, i });
      });
      rigLoaded = true;
    } catch (e) { console.warn('DJ/Rigg nicht geladen', e); }

    // ------------------------------------------------- Figuren (eigene GLBs)
    // Spielfiguren in Spielerfarbe, DJ hinterm Pult, Türsteher am Einlass, tanzende Menge.
    // Ein überspitzter Charakter für alle (club_character.glb, ca. 0,9 m modelliert),
    // unterschieden über Spielerfarbe, Hautton und eine wählbare Kopfbedeckung (club_hats_a/b.glb).
    const HAT_LIFT = [0.73, 0.6726];   // Hüte liegen in der GLB auf dem Boden (Prüfung), hier zurück auf Kopfhöhe
    const HAT_ORDER = ['fischerhut', 'cap', 'kopfhoerer', 'beanie', 'gasmaske', 'aalmuetze', 'hasenohren', 'ledhelm'];
    const SKINS = ['#e9b493', '#a8704c', '#5a3624', '#d29a74', '#7b4a2e', '#f1c7a5'];
    const TOK_SCALE = 1.15, NPC_SCALE = 2.0;
    let charC = null, hatC = [];
    const npcs = [];
    let figuresLoaded = false, crowdLoaded = false;
    const crowd = { meshes: [], dancers: [] };
    const tameGlow = (mt) => { if (mt && mt.name.includes('M_Glow')) mt.emissiveIntensity = 1.1; };
    const tint = (meshes, hex, glowScale, skin) => meshes.forEach(m => {
      const mt = m.material;
      tameGlow(mt);
      if (mt && mt.name.includes('M_Accent')) {
        mt.albedoColor = B.Color3.FromHexString(hex).toLinearSpace();
        mt.emissiveColor = B.Color3.FromHexString(hex).scale(glowScale);
      }
      if (mt && skin && mt.name.includes('M_Skin')) mt.albedoColor = B.Color3.FromHexString(skin).toLinearSpace();
    });
    // Hut-Instanz: nur die Gruppe HAT_<name> behalten
    const spawnHat = (hat, name) => {
      const ci = hatC.findIndex(h => h && (h.transformNodes.some(n => n.name === 'HAT_' + hat) || h.meshes.some(m => m.name.includes('HAT_' + hat))));
      if (ci < 0) return null;
      const c = hatC[ci];
      const inst = c.instantiateModelsToScene(n => name + '_' + n, true);
      inst.rootNodes.forEach(r => { r.position.y += HAT_LIFT[ci]; });
      inst.rootNodes.forEach(r => r.getChildren(null, true).forEach(ch => {
        if (ch.name && /HAT_/.test(ch.name) && !ch.name.endsWith('HAT_' + hat) && ch.getClassName() === 'TransformNode') ch.dispose(false, true);
      }));
      return inst.rootNodes;
    };
    const spawnFig = (name, scale, hex, hat, skin) => {
      if (!charC) return null;
      const body = new B.TransformNode(name, scene);
      charC.instantiateModelsToScene(n => name + '_' + n, true).rootNodes.forEach(r => { r.parent = body; });
      if (hat) (spawnHat(hat, name + '_hat') || []).forEach(r => { r.parent = body; });
      body.scaling.setAll(scale);
      const meshes = body.getChildMeshes(false);
      if (hex) tint(meshes, hex, 0.1, skin);
      meshes.forEach(m => shadows.addShadowCaster(m));
      body.metadata = { hat };
      return body;
    };
    try {
      const load = (f) => B.SceneLoader.LoadAssetContainerAsync(o.assetBase, f, scene, null, '.glb');
      const [ch, ha, hb] = await Promise.all(['club_character.glb', 'club_hats_a.glb', 'club_hats_b.glb'].map(f => load(f).catch(() => null)));
      charC = ch; hatC = [ha, hb];
      figuresLoaded = !!(ch && ha && hb);
      // DJ hinter dem Pult (Podest-Oberkante y 0.6), Blick zur Tanzfläche
      const dj = spawnFig('npcDJ', NPC_SCALE, '#29c6ff', 'kopfhoerer', SKINS[1]);
      if (dj) { dj.position.set(0, 0.6, HL - 3.95); dj.rotation.y = Math.PI; npcs.push({ node: dj, kind: 'dj', y: 0.6 }); }
      // Türsteher innen neben dem Einlass: breit gebaut, schaut den ankommenden Figuren entgegen
      const bo = spawnFig('npcBouncer', NPC_SCALE, '#1a1a22', 'beanie', SKINS[2]);
      if (bo) { bo.scaling.x *= 1.3; bo.position.set(tiles[0].x + 1.5, 0, tiles[0].z + 2.7); bo.rotation.y = -Math.PI / 2 - 0.6; npcs.push({ node: bo, kind: 'bouncer', y: 0 }); }
    } catch (e) { console.warn('Figuren nicht geladen', e); }
    try {
      const cc = await B.SceneLoader.LoadAssetContainerAsync(o.assetBase, 'club_crowd.glb', scene, null, '.glb');
      const inst = cc.instantiateModelsToScene(n => 'crowd_' + n, false);
      const all = inst.rootNodes[0].getChildMeshes(false).filter(m => m.getTotalVertices() > 0);
      // 6 Gäste-Varianten (Kleidung, Haut, Haare als Vertex-Farben), je ein Mesh mit Thin Instances
      for (let v = 0; v < 6; v++) {
        const parts = all.filter(m => m.name.includes('CROWD_V' + v + '_'));
        if (!parts.length) continue;
        const mesh = B.Mesh.MergeMeshes(parts, true, true, undefined, false, false);
        mesh.name = 'crowdV' + v;
        if (mesh.material) { mesh.material.backFaceCulling = false; }
        mesh.alwaysSelectAsActiveMesh = true;
        mesh.receiveShadows = true;
        crowd.meshes[v] = mesh;
      }
      inst.rootNodes.forEach(r => r.dispose());
      const nV = crowd.meshes.filter(Boolean).length;
      // Tanzfläche vor dem DJ, innerhalb des Rundkurses, lockeres Raster mit Zufall
      let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
      for (let gz = 0; gz < 5; gz++) for (let gx = 0; gx < 8; gx++) {
        if (rnd() < 0.12) continue;
        const x = -4.1 + gx * 1.17 + (rnd() - 0.5) * 0.6, z = 0.9 + gz * 1.12 + (rnd() - 0.5) * 0.5;
        crowd.dancers.push({ x, z, pose: Math.floor(rnd() * 6), ph: rnd() * 6.28, s: 0.94 + rnd() * 0.12,
          face: Math.atan2(-x * 0.15, (HL - 4.4) - z) + (rnd() - 0.5) * 0.6 });
      }
      crowd.meshes.forEach((mesh, pi) => {
        if (!mesh) return;
        const ds = crowd.dancers.filter(d => d.pose % nV === pi);
        const mats = new Float32Array(Math.max(1, ds.length) * 16);
        mesh.thinInstanceSetBuffer('matrix', mats, 16, false);
        crowd['list' + pi] = ds; crowd['buf' + pi] = mats;
      });
      crowdLoaded = crowd.dancers.length > 0 && !!crowd.meshes[0];
    } catch (e) { console.warn('Menge nicht geladen', e); }
    // LED-Tanzfläche: Raster aus Leuchtplatten, Farbwellen im Takt
    const ledTile = B.MeshBuilder.CreateBox('ledFloor', { width: 1.04, height: 0.04, depth: 1.04 }, scene);
    { const lm = new B.StandardMaterial('ledFloorM', scene); lm.disableLighting = true; lm.diffuseColor = new B.Color3(0, 0, 0); lm.emissiveColor = new B.Color3(1, 1, 1); ledTile.material = lm; }
    glow.addExcludedMesh(ledTile);
    const LED_COLS = ['#bb38ff', '#29c6ff', '#ff4fd8', '#2ee6b0'].map(c => B.Color3.FromHexString(c));
    const ledCells = [];
    for (let gx = 0; gx < 8; gx++) for (let gz = 0; gz < 5; gz++) ledCells.push({ x: -3.85 + gx * 1.1, z: 0.75 + gz * 1.1 });
    { const mats = new Float32Array(ledCells.length * 16);
      ledCells.forEach((c, i) => B.Matrix.Translation(c.x, 0.02, c.z).copyToArray(mats, i * 16));
      ledTile.thinInstanceSetBuffer('matrix', mats, 16, true);
    }
    const ledColors = new Float32Array(ledCells.length * 4);
    ledTile.thinInstanceSetBuffer('color', ledColors, 4, false);
    let ledStep = -1;
    const BPM = 130 / 60;
    scene.onBeforeRenderObservable.add(() => {
      const t = performance.now() / 1000, step = Math.floor(t * BPM * 2);       // Achtelnoten
      if (step === ledStep) return; ledStep = step;
      const pat = Math.floor(step / 32) % 3, base = LED_COLS[Math.floor(step / 8) % LED_COLS.length];
      ledCells.forEach((c, i) => {
        let k;
        if (pat === 0) k = 0.5 + 0.5 * Math.sin(step * 0.8 - Math.hypot(c.x, c.z - 3) * 1.6);          // Ringe
        else if (pat === 1) k = ((Math.round((c.x + 3.85) / 1.1) + step) % 4 === 0) ? 1 : 0.12;       // Lauflicht
        else k = ((Math.round((c.x + 3.85) / 1.1) + Math.round((c.z - 0.75) / 1.1) + step) % 2) ? 0.9 : 0.1;  // Schach
        const col = (i + step) % 7 === 0 ? LED_COLS[(Math.floor(step / 8) + 1) % LED_COLS.length] : base;
        const a = 0.08 + 0.42 * k;
        ledColors.set([col.r * a, col.g * a, col.b * a, 1], i * 4);
      });
      ledTile.thinInstanceBufferUpdated('color');
    });
    const tmpM = new B.Matrix(), tmpQ = new B.Quaternion(), tmpS = new B.Vector3(), tmpP = new B.Vector3();
    scene.onBeforeRenderObservable.add(() => {
      const t = performance.now() / 1000;
      const beat = t * BPM * Math.PI;
      crowd.meshes.forEach((mesh, pi) => {
        if (!mesh) return;
        const ds = crowd['list' + pi], buf = crowd['buf' + pi];
        ds.forEach((d, i) => {
          const b = Math.abs(Math.sin(beat + d.ph * 0.3));
          tmpS.set(d.s, d.s * (0.985 + 0.015 * b), d.s);
          B.Quaternion.RotationYawPitchRollToRef(d.face + Math.sin(t * 0.9 + d.ph) * 0.35, 0, Math.sin(beat * 0.5 + d.ph) * 0.06, tmpQ);
          tmpP.set(d.x, 0.04 + b * 0.05, d.z);
          B.Matrix.ComposeToRef(tmpS, tmpQ, tmpP, tmpM);
          tmpM.copyToArray(buf, i * 16);
        });
        mesh.thinInstanceBufferUpdated('matrix');
      });
      npcs.forEach(n => {
        if (n.kind === 'dj') { n.node.position.y = n.y + Math.abs(Math.sin(beat)) * 0.035; n.node.rotation.x = Math.sin(beat) * 0.04; }
        else n.node.rotation.z = Math.sin(t * 0.8) * 0.012;
      });
    });

    const BEAM_COLORS = ['#ff4fd8', '#29c6ff', '#f5ecff', '#2ee6b0', '#bb38ff', '#ffb627'].map(c => B.Color3.FromHexString(c));
    scene.onBeforeRenderObservable.add(() => {
      if (!heads.length) return;
      const t = performance.now() / 1000;
      const scheme = Math.floor(t / 8) % 3;      // alle 8 s neues Muster
      heads.forEach(h => {
        const ph = h.i * 0.55;
        h.pan.rotation.y = scheme === 1 ? Math.sin(t * 0.9) * 1.1 : Math.sin(t * 0.6 + ph) * 1.2;
        h.tilt.rotation.x = 0.35 + (scheme === 2 ? 0.25 + Math.sin(t * 2 + ph) * 0.2 : Math.sin(t * 0.8 + ph) * 0.45);
        h.bm.emissiveColor = BEAM_COLORS[(h.i + scheme * 2) % BEAM_COLORS.length];
      });
    });

    // ------------------------------------------------------------ Spieler
    const SLOTS = [[-0.22, -0.3], [0.22, 0.3], [0.22, -0.3], [-0.22, 0.3], [0, 0], [-0.3, 0], [0.3, 0], [0, 0.45]];
    const tokens = [];
    const makeToken = (i, players) => {
      const rootN = new B.TransformNode('tok' + i, scene);
      const col = COLORS[i % COLORS.length];
      const ring = B.MeshBuilder.CreateTorus('ring' + i, { diameter: 0.46, thickness: 0.035, tessellation: 32 }, scene);
      ring.parent = rootN; ring.position.y = 0.02; ring.material = pbr('ringm' + i, '#000000', 0, 1, col);
      const hat = (players && players[i] && players[i].hat) || HAT_ORDER[i % HAT_ORDER.length];
      let body = spawnFig('tokFig' + i, TOK_SCALE, col, hat, SKINS[i % SKINS.length]);
      if (body) {
        body.parent = rootN;
      } else {                                    // Rückfall: einfache Figur aus Grundformen
        body = new B.TransformNode('tokFig' + i, scene); body.parent = rootN;
        const mat = pbr('tokm' + i, col, 0.3, 0.35); mat.emissiveColor = B.Color3.FromHexString(col).scale(0.25);
        const b = B.MeshBuilder.CreateCylinder('body' + i, { diameterTop: 0.2, diameterBottom: 0.34, height: 0.5, tessellation: 24 }, scene);
        b.parent = body; b.position.y = 0.25; b.material = mat;
        const h = B.MeshBuilder.CreateSphere('head' + i, { diameter: 0.26, segments: 16 }, scene);
        h.parent = body; h.position.y = 0.62; h.material = mat;
        [b, h].forEach(m => shadows.addShadowCaster(m));
      }
      return { root: rootN, body, ring, walking: false, hat, i };
    };
    // Ruheblick: nach außen (zur Kamera) und etwas in Laufrichtung
    const restYaw = (f) => {
      const t = tiles[((f % 64) + 64) % 64];
      const ol = Math.hypot(t.x, t.z) || 1;
      const dx = t.x / ol + 0.6 * Math.cos(t.ang), dz = t.z / ol + 0.6 * Math.sin(t.ang);
      return Math.atan2(dx, dz);
    };
    const field = (abs) => ((abs % 64) + 64) % 64;
    const slotPos = (f, idx) => {
      const t = tiles[field(f)], [a, b] = SLOTS[idx % SLOTS.length];
      const tx = Math.cos(t.ang), tz = Math.sin(t.ang);
      return new B.Vector3(t.x + tx * a - tz * b, 0.17 + t.h, t.z + tz * a + tx * b);
    };

    // ------------------------------------------------------------ Kamera
    const cam = new B.ArcRotateCamera('cam', -Math.PI / 2, 1.02, 10, new B.Vector3(0, 0.4, -HL + 2), scene);
    cam.attachControl(canvas, true);
    cam.minZ = 0.1; cam.lowerRadiusLimit = 3; cam.upperRadiusLimit = 42;
    cam.lowerBetaLimit = 0.25; cam.upperBetaLimit = 1.45;
    cam.wheelPrecision = 25; cam.pinchPrecision = 60; cam.panningSensibility = 0;
    const VIEWS = {
      follow: { radius: 8.3, beta: 0.95 },
      overview: { target: new B.Vector3(0, 2.0, 1.5), radius: 31, beta: 1.16, alpha: -Math.PI / 2 - 0.35 },
      city: { target: new B.Vector3(0, 20, 20), radius: 70, beta: 1.47, alpha: -Math.PI / 2 - 0.45 },
      floor: { target: new B.Vector3(0, 1.4, 4.2), radius: 10.5, beta: 1.22, alpha: -Math.PI / 2 - 0.42 },
      cards: { target: new B.Vector3(0, 1.5, -6.2), radius: 8.5, beta: 1.2, alpha: -Math.PI / 2 },
    };
    let follow = 0, viewMode = 'follow', autoCam = true, camGoal = VIEWS.follow;
    canvas.addEventListener('pointerdown', () => { autoCam = false; });

    // Kamera schräg hinter der Figur: außen, um ~35° gegen die Laufrichtung versetzt
    const followAlpha = (p) => {
      let best = 0, bd = 1e9;
      tiles.forEach((t, n) => { const d = (t.x - p.x) ** 2 + (t.z - p.z) ** 2; if (d < bd) { bd = d; best = n; } });
      const t = tiles[best];
      const out = Math.atan2(p.z * 0.55, p.x);
      // Laufrichtung (Tangente) als Winkel; Kamera rückt zur Gegenrichtung
      const back = Math.atan2(-Math.sin(t.ang), -Math.cos(t.ang));
      let d = back - out; d = Math.atan2(Math.sin(d), Math.cos(d));
      return out + Math.max(-0.65, Math.min(0.65, d)) ;
    };
    const t0 = performance.now();
    scene.onBeforeRenderObservable.add(() => {
      const t = (performance.now() - t0) / 1000;
      const k = Math.min(1, engine.getDeltaTime() / 1000 * 3.5);
      const tok = tokens[follow];
      const goal = (viewMode === 'follow' && !tok) ? VIEWS.overview : camGoal;   // noch keine Figuren
      const overview = viewMode !== 'follow' || !tok;
      const goalTarget = overview ? goal.target : tok.root.position.add(new B.Vector3(0, 0.4, 0));
      cam.target = B.Vector3.Lerp(cam.target, goalTarget, k);
      cam.radius += (goal.radius - cam.radius) * k;
      if (autoCam) {
        if (goal.beta !== undefined) cam.beta += (goal.beta - cam.beta) * k * 0.6;
        const p = tok ? tok.root.position : B.Vector3.Zero();
        const goalA = overview ? (goal.alpha ?? cam.alpha) : followAlpha(p);
        let d = goalA - cam.alpha; d = Math.atan2(Math.sin(d), Math.cos(d));
        cam.alpha += d * k * 0.8;
      }
      if (exterior) exterior.update(t, cam);
      if (Math.floor(t * 12) !== Math.floor((t - engine.getDeltaTime() / 1000) * 12)) { drawEq(t); drawWall(t); }
      spots.forEach((s, i) => { s.direction.x = Math.sin(t * 0.7 + i * 1.7) * 0.7; s.direction.z = -0.3 + Math.cos(t * 0.5 + i) * 0.5; });
      tokens.forEach((tk, i) => {
        tk.ring.scaling.setAll(i === follow ? 1 + 0.12 * Math.sin(t * 6) : 1);
        if (tk.body && !tk.walking) tk.body.position.y = i === follow ? Math.abs(Math.sin(t * 130 / 60 * Math.PI)) * 0.045 : 0;
      });
    });
    engine.runRenderLoop(() => scene.render());

    const hop = (tok, from, to, ms) => new Promise(res => {
      const start = performance.now();
      const obs = scene.onBeforeRenderObservable.add(() => {
        const f = Math.min(1, (performance.now() - start) / ms);
        const p = B.Vector3.Lerp(from, to, f); p.y += Math.sin(f * Math.PI) * (0.3 + Math.abs(to.y - from.y));
        if (tok.body && Math.hypot(to.x - from.x, to.z - from.z) > 0.01) tok.body.rotation.y = Math.atan2(to.x - from.x, to.z - from.z);
        tok.root.position.copyFrom(p);
        if (f >= 1) { scene.onBeforeRenderObservable.remove(obs); res(); }
      });
    });

    await scene.whenReadyAsync();

    return {
      scene, engine, paLoaded, rigLoaded, figuresLoaded, crowdLoaded, tiles, drawCard,
      sync(players, active) {
        while (tokens.length < players.length) tokens.push(makeToken(tokens.length, players));
        tokens.forEach((tk, i) => {
          // Kopfbedeckung geändert (z. B. Lobby): Figur neu aufbauen
          const want = players[i] && players[i].hat;
          if (want && want !== tk.hat && charC) {
            const nb = spawnFig('tokFig' + i + '_' + want, TOK_SCALE, COLORS[i % COLORS.length], want, SKINS[i % SKINS.length]);
            if (nb) { nb.parent = tk.root; nb.rotation.y = tk.body.rotation.y; tk.body.dispose(false, true); tk.body = nb; tk.hat = want; }
          }
          tk.root.setEnabled(i < players.length);
          if (i < players.length && !tk.walking) { tk.root.position.copyFrom(slotPos(players[i].position, i)); tk.body.rotation.y = restYaw(players[i].position); }
        });
        if (typeof active === 'number' && active !== follow) { follow = active; autoCam = true; }
      },
      async walk(idx, fromAbs, toAbs) {
        const tk = tokens[idx]; if (!tk || fromAbs === toAbs) return;
        follow = idx; autoCam = true; if (viewMode !== 'follow') this.setView('follow');
        tk.walking = true;
        const dir = toAbs > fromAbs ? 1 : -1, steps = Math.min(40, Math.abs(toAbs - fromAbs));
        let cur = fromAbs;
        for (let k = 0; k < steps; k++) {
          cur += dir;
          await hop(tk, tk.root.position.clone(), slotPos(cur, idx), steps > 14 ? 150 : 230);
        }
        tk.walking = false;
        tk.body.rotation.y = restYaw(cur);
      },
      setView(mode) { viewMode = VIEWS[mode] ? mode : 'follow'; camGoal = VIEWS[viewMode]; cam.upperRadiusLimit = viewMode === 'city' ? 120 : 42; autoCam = true; return viewMode; },
      get view() { return viewMode; },
      resize() { engine.resize(); },
      dispose() { engine.stopRenderLoop(); scene.dispose(); engine.dispose(); },
    };
  }

  root.ClubCircuitScene = { create };
}(typeof self !== 'undefined' ? self : this));
