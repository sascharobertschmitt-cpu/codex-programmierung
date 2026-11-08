---
name: club-3d-asset-pipeline
description: Standards und Ablauf, um für "Aal You Ready?" eigene 3D-Clubobjekte per Blender-Python in GitHub Actions als GLB zu bauen, zu prüfen und in Babylon.js zu testen. Nutzen, sobald ein neues Club-Asset (Lautsprecher, DJ-Booth, Moving Head, Möbel, Bar …) entstehen oder ein bestehendes überarbeitet werden soll.
---

# Club-3D-Asset-Pipeline

Ziel: glaubwürdige, mobile-taugliche Club-Assets ohne lokale Blender-Installation und ohne Kosten.

```
Claude schreibt Python  →  GitHub Actions (Ubuntu)  →  Blender 4.2 LTS headless
   →  GLB-Export  →  glb_check.py + Khronos-Validator  →  Cycles-Vorschaubilder
   →  Headless-Chrome-Test der Babylon-Seite  →  Commit ins Repo  →  iPhone-Test
```

## Dateien

| Pfad | Zweck |
|---|---|
| `tools/blender/assetlib.py` | Reines numpy: Mesh-Builder (Lathe, Loft, Rounded Box, Zylinder), kachelbare Texturen, PNG-Writer. Ohne Blender testbar. |
| `tools/blender/speaker_geometry.py` | Topteil AYR-212 und **gemeinsame Bauteile der Familie**: `add_woofer(scale)`, `add_grille`, `bar_handle`, `connector_panel`, `round_port`, `rigging_point`, `screw_head`. |
| `tools/blender/sub_geometry.py` | Subwoofer AYR-118, nutzt die gemeinsamen Bauteile. |
| `tools/blender/build_asset.py` | Generischer Blender-Teil: Texturen, Materialien, Bevel/Boolean/Weighted Normal, Export, Vorschau. `--geometry <modul>` |
| `tools/blender/assets.json` | Liste aller Assets mit GLB-Name, erwarteten Maßen, Front-Material. |
| `tools/glb_check.py` | GLB-Prüfung (stdlib). Setzt bei Bedarf `alphaMode: MASK`. |
| `tools/browser_smoke.mjs` | Lädt eine Testseite in Headless-Chrome, liest `window.TEST_RESULT`, macht Screenshot. |
| `.github/workflows/club-assets-glb.yml` | Baut alle Assets aus `assets.json` (oder eins per `only`), prüft, committet. |
| `aal-you-ready/play/speaker-glb-test.html` | Prüfstand für Babylon.js/iPhone. `?file=…&front=…&expect=x,y,z`, Stack: `?file=club_speaker_pa212.glb&under=club_sub_118.glb`. |
| `aal-you-ready/play/assets/<asset>.glb` | Ergebnis (wird von der Action committet). |
| `aal-you-ready/play/assets/previews/` | Cycles-Renderings, Prüfberichte, Headless-Screenshot. |

Das Hauptspiel (`play/index.html`) wird von dieser Pipeline nie verändert.

## Verbindliche Konventionen

- **Einheiten:** Meter, reale Maße. Kein Skalieren in Babylon.
- **Achsen in Blender:** Z oben, Vorderseite nach **-Y**. Export mit `export_yup=True` ergibt glTF Y oben, Front **+Z**. Babylon zeigt die Front damit zur Kamera bei `alpha = π/2`.
- **Ursprung:** Mitte der Bodenfläche (Unterkante Füße = 0).
- **Ein Mesh pro Material.** Ziel ≤ 10 Draw Calls pro Hero-Asset, ≤ 3 für Deko.
- **Materialnamen** `M_<Rolle>` (z. B. `M_Cabinet`, `M_Steel`), wiederverwendbar über Assets hinweg.
- **Keine Marken, Logos, Typenschilder mit Text, keine Nachbauten geschützter Designs.**
- **Feine Details** (Lochblech, Strukturlack, Riffelung) als Textur/Normal Map, nicht als Geometrie.
- **Normal Maps** im OpenGL-Format (+Y), Farbraum `Non-Color`.
- **Kein reines Schwarz** als Basisfarbe (min. ~0.015 linear), sonst wirkt PBR leblos.
- **Einseitige Materialien:** `use_backface_culling = True`. Nur Bleche/Hörner doppelseitig.
- **Alpha:** Lochbleche als `MASK` (Alpha-Test, Cutoff 0.45), niemals `BLEND` (Sortierprobleme, teuer auf Mobile).

## Budgets (Mobile-Web, iPhone 12 und neuer als Referenz)

| | Hero-Asset (Lautsprecher, DJ-Booth) | Mittel (Möbel, Moving Head) | Klein/Deko |
|---|---|---|---|
| Dreiecke | ≤ 25k (hart 40k) | ≤ 8k | ≤ 2k |
| Draw Calls | ≤ 10 | ≤ 5 | ≤ 2 |
| GLB-Größe | ≤ 1 MB (hart 2 MB) | ≤ 500 KB | ≤ 150 KB |
| Texturen | 256–512 px, kachelnd | 256–512 px | geteilt |

Mehrfach vorkommende Objekte (Lautsprecher-Stacks, Stühle) in Babylon instanziieren (`instantiateModelsToScene` bzw. `createInstance`), nicht mehrfach laden.

## Modellier-Regeln (gegen den "Diorama-Look")

1. Silhouette zuerst: echte Proportionen recherchieren, nicht schätzen. Trapez, Fasen, Überstände.
2. Jede Kante, die in echt gerundet ist, bekommt Bevel (Gehäuse 10–15 mm, Bleche 1–3 mm).
3. Materialkontrast ist Detail: Strukturlack vs. Pulverlack vs. Stahl vs. Gummi.
4. Mechanische Logik: Schrauben dort, wo etwas befestigt ist; Griffe dort, wo man anfasst.
5. Hard-Surface-Shading: Bevel + `WEIGHTED_NORMAL` (Face Area, Keep Sharp).
6. Wenn ein Ergebnis klobig wirkt: Proportionen und Fasen korrigieren, nicht mehr Boxen anbauen.

## Neues Asset anlegen

1. `tools/blender/<name>_geometry.py` mit `build()` schreiben (Vorbild `sub_geometry.py`). Rückgabe: `name`, `cabinet` (Part mit geteilten Vertices), `cutters`, `parts`, `bevel`, `dims`, `shots`. Gemeinsame Bauteile aus `speaker_geometry` wiederverwenden.
2. Lokal ohne Blender prüfen: `python3 tools/blender/<name>_geometry.py` (Dreiecke, Maße in glTF-Achsen).
3. Eintrag in `assets.json` mit den Maßen aus Schritt 2.
4. Pushen. Die Action baut, prüft und committet GLB plus Vorschaubilder (`assets/previews/<id>_*.jpg`).
5. Vorschaubilder ansehen, dann auf dem iPhone die Testseite öffnen.

Gemeinsame Bauteile nie still ändern: vorher Geometrie aller Assets als Referenz speichern und nach dem Umbau vergleichen.

## Testen auf dem iPhone

Das Repo hat kein GitHub Pages. Seiten laufen über raw.githack.com:

`https://raw.githack.com/sascharobertschmitt-cpu/codex-programmierung/main/aal-you-ready/play/<seite>.html`

githack cached einige Minuten. Für einen garantiert frischen Stand den Commit-Hash statt `main` einsetzen. Die Dateigröße per HEAD-Request kann dort fehlen (Prüfstand zeigt dann ⚠️, kein Modellfehler).

## Qualitätssicherung: was automatisch ist und was nicht

| # | Prüfung | Wie | Art |
|---|---|---|---|
| 1 | Skript läuft fehlerfrei | `--python-exit-code 1`, Log als Artifact | automatisch |
| 2 | GLB-Export | Datei existiert, > 1 KB | automatisch |
| 3 | Sichtbare Geometrie | `glb_check.py` (Dreiecke > 0) | automatisch |
| 4 | Materialien/Texturen eingebettet | `glb_check.py`, Khronos-Validator | automatisch |
| 5 | Maße/Ursprung | `glb_check.py --expect-size` | automatisch |
| 6 | Ausrichtung | `--front-material`, Babylon-Seite prüft +Z | automatisch |
| 7 | Laden in Babylon | Headless-Chrome mit SwiftShader | automatisch, Software-GPU |
| 8 | Dateigröße | Budget in `glb_check.py` | automatisch |
| 9 | Optik | Cycles-Renderings im Repo | **manuell ansehen** |
| 10 | iPhone | Testseite auf echtem Gerät | **manuell** |

Gebrauchsspuren: `texture_wear()` (Rauheit + Kratzer, zweite UV `UVWear`, 60 cm Kachel). Dezent halten, sonst wirkt es wie ein Muster.

Ein Asset gilt erst als fertig, wenn 9 und 10 von einem Menschen bestätigt sind.

## Sicherheit bei fremden Skills, MCP-Servern und Add-ons

Vor Übernahme lesen und prüfen: Netzwerkzugriffe, `subprocess`/`os.system`, `exec`/`eval` von Fremdcode, Zugriff auf Tokens/Secrets, unnötige Workflow-Rechte. Workflows bekommen nur `contents: write`. Keine Secrets nötig.
