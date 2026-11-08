/*
 * Dystopische Außenwelt für den Club-Rundkurs (Babylon.js, prozedural, mobil-tauglich).
 *
 *   const ext = ClubExterior.build(scene, BABYLON, { hall: {hw:15, hl:22}, rain: true, quality: 1, glow });
 *   scene.onBeforeRenderObservable.add(() => ext.update(seconds, camera));
 *
 * Inhalt: Ruinen-Halle (Brüstung, Stahlstützen, Fensterraster, Dachfachwerk, Tor im Süden),
 * Megacity-Skyline mit Fenstertexturen, Smog, Schlote, Warnlichter, Suchscheinwerfer,
 * Propaganda-Werbetafel, Regen. Viele Teile als Thin Instances (wenige Draw Calls).
 */
(function (root) {
  'use strict';

  function rng(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function build(scene, B, opts) {
    const o = Object.assign({ hall: { hw: 15, hl: 22, h: 8.5 }, rain: true, quality: 1, glow: null }, opts || {});
    const R = rng(1987);
    const Q = Math.max(0.3, Math.min(1.5, o.quality));
    const updaters = [];
    const meshes = [];

    // ---------------------------------------------------------- Himmel + Smog
    scene.clearColor = new B.Color4(0.05, 0.026, 0.05, 1);
    scene.fogMode = B.Scene.FOGMODE_EXP2;
    scene.fogDensity = 0.0075;
    scene.fogColor = new B.Color3(0.11, 0.055, 0.075);

    const mat = (name, hex, metal, rough, emissive) => {
      const m = new B.PBRMaterial(name, scene);
      m.albedoColor = B.Color3.FromHexString(hex).toLinearSpace();
      m.metallic = metal; m.roughness = rough;
      if (emissive) m.emissiveColor = B.Color3.FromHexString(emissive);
      return m;
    };
    const unlit = (name, hex, alpha) => {
      const m = new B.StandardMaterial(name, scene);
      m.disableLighting = true; m.emissiveColor = B.Color3.FromHexString(hex);
      if (alpha !== undefined) { m.alpha = alpha; m.alphaMode = B.Engine.ALPHA_ADD; m.backFaceCulling = false; }
      m.fogEnabled = alpha === undefined;
      return m;
    };
    const thin = (mesh, mats) => { mats.forEach(m => mesh.thinInstanceAdd(m)); mesh.thinInstanceRefreshBoundingInfo(); meshes.push(mesh); return mesh; };
    const M = (x, y, z, sx, sy, sz, ry) => B.Matrix.Compose(new B.Vector3(sx, sy, sz),
      B.Quaternion.RotationAxis(B.Axis.Y, ry || 0), new B.Vector3(x, y, z));

    // Nasser Asphalt draußen
    const ground = B.MeshBuilder.CreateGround('outGround', { width: 900, height: 900 }, scene);
    ground.position.y = -0.02;
    ground.material = mat('asphalt', '#141218', 0.15, 0.38);
    ground.receiveShadows = true;

    // ---------------------------------------------------------- Ruinen-Halle
    const { hw, hl, h } = o.hall;
    const concrete = mat('hallConcrete', '#3a3533', 0, 0.9);
    const rust = mat('hallRust', '#4a2e24', 0.7, 0.55);
    const steel = mat('hallSteel', '#2b2d34', 0.85, 0.4);

    // Brüstung (1,2 m) rundum, im Süden Tor 7 m breit
    const wallBox = B.MeshBuilder.CreateBox('parapet', { size: 1 }, scene);
    wallBox.material = concrete;
    const gate = 3.5, wt = 0.45, ph = 1.2;
    thin(wallBox, [
      M(0, ph / 2, hl, hw * 2 + wt, ph, wt),
      M(hw, ph / 2, 0, wt, ph, hl * 2), M(-hw, ph / 2, 0, wt, ph, hl * 2),
      M((hw + gate) / 2, ph / 2, -hl, hw - gate, ph, wt), M(-(hw + gate) / 2, ph / 2, -hl, hw - gate, ph, wt),
      // Torstürze und Torpfosten
      M(0, h - 1.2, -hl, gate * 2 + 0.8, 0.9, wt + 0.1),
    ]);

    // Stahlstützen rundum alle 4 m
    const colMats = [];
    const addCol = (x, z) => colMats.push(M(x, h / 2, z, 0.38, h, 0.38));
    for (let x = -hw; x <= hw + 0.01; x += hw / 4) { addCol(x, hl); if (Math.abs(x) > gate - 0.1) addCol(x, -hl); }
    addCol(gate, -hl); addCol(-gate, -hl);
    for (let z = -hl + 4; z < hl - 0.1; z += 4) { addCol(hw, z); addCol(-hw, z); }
    thin(B.MeshBuilder.CreateBox('columns', { size: 1 }, scene), colMats).material = rust;

    // Fensterraster: Riegel + Sprossen
    const barMats = [];
    [ph, 4.6, h - 0.05].forEach(y => {
      barMats.push(M(0, y, hl, hw * 2, 0.12, 0.12), M(hw, y, 0, 0.12, 0.12, hl * 2), M(-hw, y, 0, 0.12, 0.12, hl * 2));
      barMats.push(M((hw + gate) / 2, y, -hl, hw - gate, 0.12, 0.12), M(-(hw + gate) / 2, y, -hl, hw - gate, 0.12, 0.12));
    });
    for (let x = -hw; x <= hw; x += 1.25) {
      barMats.push(M(x, (ph + h) / 2, hl, 0.06, h - ph, 0.06));
      if (Math.abs(x) > gate) barMats.push(M(x, (ph + h) / 2, -hl, 0.06, h - ph, 0.06));
    }
    for (let z = -hl; z <= hl; z += 1.25) { barMats.push(M(hw, (ph + h) / 2, z, 0.06, h - ph, 0.06), M(-hw, (ph + h) / 2, z, 0.06, h - ph, 0.06)); }
    thin(B.MeshBuilder.CreateBox('mullions', { size: 1 }, scene), barMats).material = steel;

    // Verbliebene, verschmutzte Glasscheiben (ca. 25 %)
    const glassMat = new B.PBRMaterial('dirtyGlass', scene);
    glassMat.albedoColor = new B.Color3(0.15, 0.17, 0.2); glassMat.alpha = 0.32; glassMat.metallic = 0.1; glassMat.roughness = 0.15;
    glassMat.backFaceCulling = false; glassMat.transparencyMode = B.PBRMaterial.PBRMATERIAL_ALPHABLEND;
    const paneMats = [];
    const pane = (x, y, z, alongX) => { if (R() < 0.25) paneMats.push(M(x, y, z, alongX ? 1.17 : 0.02, 1.6 + R() * 1.6, alongX ? 0.02 : 1.17)); };
    for (let x = -hw + 0.62; x < hw; x += 1.25) { pane(x, 2.9, hl, true); pane(x, 6.4, hl, true); if (Math.abs(x) > gate) { pane(x, 2.9, -hl, true); pane(x, 6.4, -hl, true); } }
    for (let z = -hl + 0.62; z < hl; z += 1.25) { pane(hw, 2.9, z, false); pane(-hw, 2.9, z, false); pane(hw, 6.4, z, false); pane(-hw, 6.4, z, false); }
    if (paneMats.length) thin(B.MeshBuilder.CreateBox('panes', { size: 1 }, scene), paneMats).material = glassMat;

    // Dachfachwerk ohne Dachhaut (Obergurt, Untergurt, Pfosten), dazu ein paar Längsträger
    const trussMats = [];
    const truss = (z, x0, x1) => {
      const cx = (x0 + x1) / 2, w = x1 - x0;
      trussMats.push(M(cx, h + 1.2, z, w, 0.16, 0.16), M(cx, h, z, w, 0.12, 0.12));
      for (let x = x0; x <= x1 + 0.01; x += hw / 5) trussMats.push(M(x, h + 0.6, z, 0.08, 1.2, 0.08));
    };
    // Dach weitgehend eingestürzt: nur Endfelder stehen noch, zwei halbe Träger hängen in der Mitte
    [-hl, hl - 4, hl].forEach(z => truss(z, -hw, hw));
    truss(-hl + 12, -hw, -hw + 6);
    truss(hl - 14, hw - 5, hw);
    trussMats.push(M(-hw, h + 1.2, 0, 0.14, 0.14, hl * 2), M(hw, h + 1.2, 0, 0.14, 0.14, hl * 2));
    // eingestürzter Träger, schräg in der Halle
    const fallen = B.MeshBuilder.CreateBox('fallenBeam', { width: 0.2, height: 0.2, depth: 9 }, scene);
    fallen.material = rust; fallen.position.set(hw - 2.2, 4.4, -hl + 9); fallen.rotation.set(0.9, 0.25, 0);
    thin(B.MeshBuilder.CreateBox('truss', { size: 1 }, scene), trussMats).material = rust;

    // Notlicht über dem Tor
    const exitSign = B.MeshBuilder.CreateBox('exitSign', { width: 1.1, height: 0.32, depth: 0.08 }, scene);
    exitSign.position.set(0, h - 0.55, -hl - 0.3); exitSign.material = unlit('exitMat', '#ff2a3c');

    // ---------------------------------------------------------- Skyline
    function windowTex(name, seed, cols, rows) {
      const r = rng(seed);
      const t = new B.DynamicTexture(name, { width: 512, height: 1024 }, scene, true);
      const g = t.getContext();
      g.fillStyle = '#070609'; g.fillRect(0, 0, 512, 1024);
      const cw = 512 / cols, rh = 1024 / rows;
      const pal = ['#ffb347', '#ffb347', '#ffd27a', '#ffcf8a', '#5ee7ff', '#ff4fd8', '#b6ff6e'];
      for (let y = 0; y < rows; y++) {
        const floorLit = r() < 0.6;
        for (let x = 0; x < cols; x++) {
          const lit = floorLit && r() < 0.42;
          g.fillStyle = lit ? pal[Math.floor(r() * pal.length)] : '#120f17';
          g.globalAlpha = lit ? 0.55 + r() * 0.45 : 1;
          g.fillRect(x * cw + cw * 0.18, y * rh + rh * 0.22, cw * 0.64, rh * 0.5);
        }
      }
      g.globalAlpha = 1;
      t.update(); return t;
    }
    const towerKinds = [
      { w: 14, d: 14, hgt: 60, cols: 8, rows: 40, us: 1, vs: 1 },
      { w: 24, d: 12, hgt: 40, cols: 12, rows: 24, us: 1, vs: 1 },
      { w: 10, d: 10, hgt: 110, cols: 6, rows: 64, us: 1, vs: 1 },
      { w: 30, d: 22, hgt: 22, cols: 16, rows: 12, us: 1, vs: 1 },
    ];
    const towerMeshes = towerKinds.map((k, i) => {
      const m = B.MeshBuilder.CreateBox('towers' + i, { width: k.w, height: k.hgt, depth: k.d }, scene);
      const tm = new B.PBRMaterial('towerMat' + i, scene);
      tm.albedoColor = new B.Color3(0.035, 0.032, 0.04); tm.metallic = 0.3; tm.roughness = 0.6;
      tm.emissiveTexture = windowTex('win' + i, 11 + i * 7, Math.round(k.w / 0.9), Math.round(k.hgt / 1.6));
      tm.emissiveColor = new B.Color3(1, 1, 1); tm.emissiveIntensity = 0.9;
      m.material = tm;
      if (o.glow) o.glow.addExcludedMesh(m);
      return m;
    });
    const nTowers = Math.round(150 * Q);
    const perKind = towerKinds.map(() => []);
    const beacons = [];
    for (let i = 0; i < nTowers; i++) {
      const a = R() * Math.PI * 2;
      const dist = 75 + Math.pow(R(), 0.7) * 230;
      const x = Math.cos(a) * dist, z = Math.sin(a) * dist * 1.1;
      const kind = R() < 0.18 ? 2 : R() < 0.5 ? 0 : R() < 0.6 ? 1 : 3;
      const k = towerKinds[kind];
      const s = 0.7 + R() * 0.6 + dist / 400;
      const sy = s * (0.7 + R() * 0.7);
      perKind[kind].push(M(x, (k.hgt * sy) / 2, z, s, sy, s, R() * Math.PI));
      if (k.hgt * sy > 70 && R() < 0.6) beacons.push(new B.Vector3(x, k.hgt * sy + 1.5, z));
    }
    towerMeshes.forEach((m, i) => thin(m, perKind[i]));

    // Zwei Megatürme
    const megaMat = mat('megaMat', '#0d0c12', 0.6, 0.35);
    [[-140, 210, 230], [190, 170, 260]].forEach(([x, z, hgt], i) => {
      const t = B.MeshBuilder.CreateCylinder('mega' + i, { diameterTop: 22, diameterBottom: 46, height: hgt, tessellation: 8 }, scene);
      t.position.set(x, hgt / 2, z); t.material = megaMat;
      const ring = B.MeshBuilder.CreateTorus('megaRing' + i, { diameter: 34, thickness: 1.2, tessellation: 32 }, scene);
      ring.position.set(x, hgt * 0.62, z); ring.material = unlit('megaRingMat' + i, i ? '#29c6ff' : '#ff4fd8');
      const spire = B.MeshBuilder.CreateCylinder('spire' + i, { diameterTop: 0, diameterBottom: 6, height: 40, tessellation: 6 }, scene);
      spire.position.set(x, hgt + 20, z); spire.material = megaMat;
      beacons.push(new B.Vector3(x, hgt + 41, z));
    });

    // Schlote mit glühender Mündung
    const stackMat = mat('stackMat', '#2a2124', 0.2, 0.8);
    const emberMat = unlit('ember', '#ff5a1f');
    for (let i = 0; i < Math.round(7 * Q); i++) {
      const a = -0.6 + i * 0.32 + R() * 0.1, d = 120 + R() * 80, hgt = 55 + R() * 45;
      const x = Math.cos(a) * d, z = Math.sin(a) * d + 60;
      const c = B.MeshBuilder.CreateCylinder('chimney' + i, { diameterTop: 4, diameterBottom: 7, height: hgt, tessellation: 12 }, scene);
      c.position.set(x, hgt / 2, z); c.material = stackMat;
      const e = B.MeshBuilder.CreateTorus('ember' + i, { diameter: 4.2, thickness: 0.7, tessellation: 16 }, scene);
      e.position.set(x, hgt, z); e.material = emberMat;
    }

    // Blinkende Warnlichter
    const beaconMat = unlit('beaconMat', '#ff1030');
    const bm = B.MeshBuilder.CreateSphere('beacons', { diameter: 2.2, segments: 6 }, scene);
    bm.material = beaconMat;
    thin(bm, beacons.map(p => M(p.x, p.y, p.z, 1, 1, 1)));
    updaters.push(t => { beaconMat.emissiveColor.set(Math.sin(t * 3) > 0.2 ? 1 : 0.12, 0.05, 0.1); });

    // ---------------------------------------------------------- Suchscheinwerfer
    const beams = [];
    [[-90, -150, '#cfe8ff'], [120, -60, '#ffd7f2'], [-60, 140, '#cfe8ff']].forEach(([x, z, col], i) => {
      const pivot = new B.TransformNode('beamPivot' + i, scene);
      pivot.position.set(x, 0, z);
      const cone = B.MeshBuilder.CreateCylinder('beam' + i, { diameterTop: 26, diameterBottom: 1.5, height: 260, tessellation: 24, cap: B.Mesh.NO_CAP }, scene);
      cone.parent = pivot; cone.position.y = 130;
      cone.material = unlit('beamMat' + i, col, 0.055);
      if (o.glow) o.glow.addExcludedMesh(cone);
      beams.push({ pivot, ph: R() * 6, sp: 0.18 + R() * 0.15 });
    });
    updaters.push(t => beams.forEach(b => {
      b.pivot.rotation.z = Math.sin(t * b.sp + b.ph) * 0.45;
      b.pivot.rotation.x = Math.cos(t * b.sp * 0.8 + b.ph) * 0.3;
    }));

    // ---------------------------------------------------------- Propaganda-Werbetafel
    const slogans = [
      ['TANZEN IST PFLICHT', '#ff4fd8'], ['AUSGANGSSPERRE AB 05:00', '#29c6ff'],
      ['DEIN PULS GEHÖRT UNS', '#ffb627'], ['BLEIB IM TAKT. BLEIB GEHORSAM.', '#2ee6b0'],
      ['KEIN GEFÜHL OHNE GENEHMIGUNG', '#ff4fd8'], ['AAL YOU READY?', '#ffffff'],
    ];
    const bbTex = new B.DynamicTexture('billboardTex', { width: 1024, height: 360 }, scene, true);
    const bb = B.MeshBuilder.CreatePlane('billboard', { width: 54, height: 19 }, scene);
    bb.position.set(-40, 52, 120); bb.rotation.y = -0.33;   // Vorderseite zeigt zur Halle
    const bbm = new B.StandardMaterial('billboardMat', scene);
    bbm.disableLighting = true; bbm.emissiveTexture = bbTex; bbm.fogEnabled = false; bb.material = bbm;
    const frame = B.MeshBuilder.CreateBox('billboardFrame', { width: 56, height: 21, depth: 1.2 }, scene);
    frame.position.set(bb.position.x - 0.22, bb.position.y, bb.position.z + 0.66);
    frame.rotation.y = bb.rotation.y; frame.material = steel;
    const legs = B.MeshBuilder.CreateBox('billboardLegs', { width: 2, height: 42, depth: 2 }, scene);
    legs.position.set(bb.position.x, 21, bb.position.z + 1); legs.material = steel;
    let lastSlot = -1;
    const drawBB = (t) => {
      const slot = Math.floor(t / 4.5) % slogans.length;
      const flick = Math.random() < 0.06;
      if (slot === lastSlot && !flick) return;
      lastSlot = flick ? -1 : slot;
      const [txt, col] = slogans[slot];
      const g = bbTex.getContext();
      g.fillStyle = '#050307'; g.fillRect(0, 0, 1024, 360);
      for (let y = 0; y < 360; y += 6) { g.fillStyle = 'rgba(255,255,255,0.035)'; g.fillRect(0, y, 1024, 2); }
      g.globalAlpha = flick ? 0.25 : 1;
      g.strokeStyle = col; g.lineWidth = 10; g.strokeRect(18, 18, 988, 324);
      g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle';
      let size = 104; g.font = `900 ${size}px system-ui,sans-serif`;
      while (g.measureText(txt).width > 930 && size > 40) { size -= 6; g.font = `900 ${size}px system-ui,sans-serif`; }
      g.fillText(txt, 512, 172);
      g.font = '600 30px system-ui,sans-serif'; g.fillStyle = '#d8d2e8';
      g.fillText('MINISTERIUM FÜR NACHTRUHE · BEZIRK 9', 512, 300);
      g.globalAlpha = 1;
      bbTex.update();
    };
    drawBB(0);
    updaters.push(drawBB);

    // ---------------------------------------------------------- Regen
    let rain = null;
    if (o.rain) {
      const dropTex = new B.DynamicTexture('drop', { width: 8, height: 64 }, scene, false);
      const g = dropTex.getContext();
      const grad = g.createLinearGradient(0, 0, 0, 64);
      grad.addColorStop(0, 'rgba(255,255,255,0)'); grad.addColorStop(1, 'rgba(210,225,255,0.9)');
      g.fillStyle = grad; g.fillRect(3, 0, 2, 64); dropTex.hasAlpha = true; dropTex.update();
      rain = new B.ParticleSystem('rain', Math.round(1400 * Q), scene);
      rain.particleTexture = dropTex;
      rain.emitter = new B.Vector3(0, 18, 0);
      rain.minEmitBox = new B.Vector3(-22, 0, -22); rain.maxEmitBox = new B.Vector3(22, 6, 22);
      rain.direction1 = new B.Vector3(1.5, -30, 0.5); rain.direction2 = new B.Vector3(2.5, -36, 1);
      rain.minEmitPower = 1; rain.maxEmitPower = 1.1;
      rain.minLifeTime = 0.55; rain.maxLifeTime = 0.8;
      rain.minSize = 0.035; rain.maxSize = 0.055; rain.minScaleY = 9; rain.maxScaleY = 14;
      rain.emitRate = 1700 * Q;
      rain.billboardMode = B.ParticleSystem.BILLBOARDMODE_STRETCHED;
      rain.blendMode = B.ParticleSystem.BLENDMODE_ADD;
      rain.color1 = new B.Color4(0.6, 0.65, 0.8, 0.35); rain.color2 = new B.Color4(0.8, 0.6, 0.9, 0.25);
      rain.colorDead = new B.Color4(0, 0, 0, 0);
      rain.start();
    }

    return {
      meshes,
      rain,
      update(t, camera) {
        updaters.forEach(f => f(t));
        if (rain && camera) { rain.emitter.x = camera.target.x; rain.emitter.z = camera.target.z; rain.emitter.y = camera.target.y + 16; }
      },
    };
  }

  root.ClubExterior = { build };
}(typeof self !== 'undefined' ? self : this));
