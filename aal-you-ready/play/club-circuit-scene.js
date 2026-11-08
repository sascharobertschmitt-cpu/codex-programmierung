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
    glow.intensity = 0.85;

    const pbr = (name, hex, metal, rough, emissive) => {
      const m = new B.PBRMaterial(name, scene);
      m.albedoColor = B.Color3.FromHexString(hex).toLinearSpace();
      m.metallic = metal; m.roughness = rough;
      if (emissive) { m.emissiveColor = B.Color3.FromHexString(emissive); }
      return m;
    };

    // Raum: Betonboden, dunkle Ziegelwände, Säulen
    const floor = B.MeshBuilder.CreateGround('floor', { width: 30, height: 44 }, scene);
    floor.material = pbr('concrete', '#24232b', 0, 0.42);
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
      if (type === 'activity') {           // Blitz
        g.beginPath(); g.moveTo(146, 52); g.lineTo(92, 136); g.lineTo(128, 136); g.lineTo(108, 206); g.lineTo(168, 116); g.lineTo(132, 116); g.closePath(); g.stroke();
      } else if (type === 'event') {        // Sprechblase
        g.beginPath(); g.ellipse(128, 118, 66, 48, 0, 0, Math.PI * 2); g.stroke();
        g.beginPath(); g.moveTo(98, 160); g.lineTo(82, 196); g.lineTo(124, 166); g.stroke();
      } else if (type === 'special') {      // Stern
        g.beginPath();
        for (let i = 0; i < 10; i++) { const r = i % 2 ? 30 : 74, a = -Math.PI / 2 + i * Math.PI / 5; g.lineTo(128 + r * Math.cos(a), 132 + r * Math.sin(a)); }
        g.closePath(); g.stroke();
      } else if (type === 'slf') {
        g.font = 'bold 76px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('SLF', 128, 132);
      } else if (type === 'gate') {
        g.font = 'bold 44px system-ui,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
        g.fillText('START', 128, 104); g.fillText('ZIEL', 128, 156);
      }
      t.update(); t.hasAlpha = false;
      return t;
    }

    const base = B.MeshBuilder.CreateBox('tileBase', { width: 0.90, height: 0.16, depth: 1.24 }, scene);
    base.material = pbr('tileBody', '#3a3a48', 0.75, 0.32);
    base.receiveShadows = true;
    const tops = {};
    for (const type of Object.keys(TYPE_COLOR)) {
      const top = B.MeshBuilder.CreateGround('tileTop_' + type, { width: 0.80, height: 1.12 }, scene);
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
      const e = B.MeshBuilder.CreateBox('tileEdge_' + type, { width: 0.92, height: 0.025, depth: 1.26 }, scene);
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

    // Einlass-Tor (Start/Ziel) über Feld 0
    const gateRoot = new B.TransformNode('gate', scene);
    gateRoot.position.set(tiles[0].x, 0, tiles[0].z);
    const truss = pbr('truss', '#3a3a44', 0.9, 0.3);
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
    sm.disableLighting = true; sm.emissiveTexture = signTex; sign.material = sm;

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
    const eqm = new B.StandardMaterial('eqm', scene); eqm.disableLighting = true; eqm.emissiveTexture = eqTex; eq.material = eqm;
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
    const wm = new B.StandardMaterial('wallm', scene); wm.disableLighting = true; wm.emissiveTexture = wallTex; wall.material = wm;
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


    // ------------------------------------------------------------ Spieler
    const SLOTS = [[-0.2, -0.32], [0.2, 0.32], [0.2, -0.32], [-0.2, 0.32], [0, 0], [-0.3, 0], [0.3, 0], [0, 0.45]];
    const tokens = [];
    const makeToken = (i) => {
      const rootN = new B.TransformNode('tok' + i, scene);
      const col = COLORS[i % COLORS.length];
      const mat = pbr('tokm' + i, col, 0.3, 0.35); mat.emissiveColor = B.Color3.FromHexString(col).scale(0.25);
      const body = B.MeshBuilder.CreateCylinder('body' + i, { diameterTop: 0.2, diameterBottom: 0.34, height: 0.5, tessellation: 24 }, scene);
      body.parent = rootN; body.position.y = 0.25; body.material = mat;
      const head = B.MeshBuilder.CreateSphere('head' + i, { diameter: 0.26, segments: 16 }, scene);
      head.parent = rootN; head.position.y = 0.62; head.material = mat;
      const ring = B.MeshBuilder.CreateTorus('ring' + i, { diameter: 0.46, thickness: 0.035, tessellation: 32 }, scene);
      ring.parent = rootN; ring.position.y = 0.02; ring.material = pbr('ringm' + i, '#000000', 0, 1, col);
      [body, head].forEach(m => shadows.addShadowCaster(m));
      return { root: rootN, ring, walking: false };
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
      follow: { radius: 8.5, beta: 1.0 },
      overview: { target: new B.Vector3(0, 2.0, 1.5), radius: 31, beta: 1.16, alpha: -Math.PI / 2 - 0.35 },
      city: { target: new B.Vector3(0, 20, 20), radius: 70, beta: 1.47, alpha: -Math.PI / 2 - 0.45 },
    };
    let follow = 0, viewMode = 'follow', autoCam = true, camGoal = VIEWS.follow;
    canvas.addEventListener('pointerdown', () => { autoCam = false; });

    const t0 = performance.now();
    scene.onBeforeRenderObservable.add(() => {
      const t = (performance.now() - t0) / 1000;
      const k = Math.min(1, engine.getDeltaTime() / 1000 * 3.5);
      const tok = tokens[follow];
      const overview = viewMode !== 'follow' || !tok;
      const goalTarget = overview ? camGoal.target : tok.root.position.add(new B.Vector3(0, 0.4, 0));
      cam.target = B.Vector3.Lerp(cam.target, goalTarget, k);
      cam.radius += (camGoal.radius - cam.radius) * k;
      if (autoCam) {
        if (camGoal.beta !== undefined) cam.beta += (camGoal.beta - cam.beta) * k * 0.6;
        const p = tok ? tok.root.position : B.Vector3.Zero();
        const goalA = overview ? camGoal.alpha : Math.atan2(p.z * 0.55, p.x);
        let d = goalA - cam.alpha; d = Math.atan2(Math.sin(d), Math.cos(d));
        cam.alpha += d * k * 0.8;
      }
      if (exterior) exterior.update(t, cam);
      if (Math.floor(t * 12) !== Math.floor((t - engine.getDeltaTime() / 1000) * 12)) { drawEq(t); drawWall(t); }
      spots.forEach((s, i) => { s.direction.x = Math.sin(t * 0.7 + i * 1.7) * 0.7; s.direction.z = -0.3 + Math.cos(t * 0.5 + i) * 0.5; });
      tokens.forEach((tk, i) => { tk.ring.scaling.setAll(i === follow ? 1 + 0.12 * Math.sin(t * 6) : 1); });
    });
    engine.runRenderLoop(() => scene.render());

    const hop = (tok, from, to, ms) => new Promise(res => {
      const start = performance.now();
      const obs = scene.onBeforeRenderObservable.add(() => {
        const f = Math.min(1, (performance.now() - start) / ms);
        const p = B.Vector3.Lerp(from, to, f); p.y += Math.sin(f * Math.PI) * (0.3 + Math.abs(to.y - from.y));
        tok.root.position.copyFrom(p);
        if (f >= 1) { scene.onBeforeRenderObservable.remove(obs); res(); }
      });
    });

    await scene.whenReadyAsync();

    return {
      scene, engine, paLoaded, tiles,
      sync(players, active) {
        while (tokens.length < players.length) tokens.push(makeToken(tokens.length));
        tokens.forEach((tk, i) => {
          tk.root.setEnabled(i < players.length);
          if (i < players.length && !tk.walking) tk.root.position.copyFrom(slotPos(players[i].position, i));
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
      },
      setView(mode) { viewMode = VIEWS[mode] ? mode : 'follow'; camGoal = VIEWS[viewMode]; cam.upperRadiusLimit = viewMode === 'city' ? 120 : 42; autoCam = true; return viewMode; },
      get view() { return viewMode; },
      resize() { engine.resize(); },
      dispose() { engine.stopRenderLoop(); scene.dispose(); engine.dispose(); },
    };
  }

  root.ClubCircuitScene = { create };
}(typeof self !== 'undefined' ? self : this));
