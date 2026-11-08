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
| `tools/blender/<asset>_geometry.py` | Geometrie eines Assets als Daten (ohne bpy). |
| `tools/blender/<asset>.py` | Blender-Teil: Materialien, Modifier (Bevel, Boolean, Weighted Normal), Export, Vorschau. |
| `tools/glb_check.py` | GLB-Prüfung (stdlib). Setzt bei Bedarf `alphaMode: MASK`. |
| `tools/browser_smoke.mjs` | Lädt eine Testseite in Headless-Chrome, liest `window.TEST_RESULT`, macht Screenshot. |
| `.github/workflows/club-<asset>-glb.yml` | Build, Prüfung, Commit. |
| `aal-you-ready/play/<asset>-glb-test.html` | Prüfstand für Babylon.js/iPhone. Generisch über `?file=…&front=…&expect=x,y,z`. |
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

1. `tools/blender/<asset>_geometry.py` nach Vorbild `speaker_geometry.py` schreiben. Maße als Konstanten oben.
2. Lokal ohne Blender prüfen: `python3 tools/blender/<asset>_geometry.py` (Dreiecke je Material).
3. Blender-Skript nach Vorbild `club_speaker_pa212.py`, Workflow kopieren und Pfade/`--expect-size` anpassen.
4. Pushen. Die Action baut, prüft und committet GLB plus Vorschaubilder.
5. Vorschaubilder im Repo ansehen (`assets/previews/*.jpg`), dann auf dem iPhone die Testseite öffnen.

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

Ein Asset gilt erst als fertig, wenn 9 und 10 von einem Menschen bestätigt sind.

## Sicherheit bei fremden Skills, MCP-Servern und Add-ons

Vor Übernahme lesen und prüfen: Netzwerkzugriffe, `subprocess`/`os.system`, `exec`/`eval` von Fremdcode, Zugriff auf Tokens/Secrets, unnötige Workflow-Rechte. Workflows bekommen nur `contents: write`. Keine Secrets nötig.
