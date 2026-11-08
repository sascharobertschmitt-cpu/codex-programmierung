"""
Traverse "AYR-TR1": 3 m Vierpunkt-Alutraverse (eigenes Design, generisch).

Gurtrohre 50 mm, Diagonalen 20 mm im Zickzack auf allen vier Seiten, Endplatten
mit Konusverbindern. Ursprung: Mitte der Unterseite. Länge entlang X.
In Babylon wird sie als Instanz mehrfach gesetzt (Rigg über dem DJ).
"""
import numpy as np

import speaker_geometry as sg
from assetlib import Part, frame_matrix, lathe, rounded_box, tube

L = 3.0          # Segmentlänge
S = 0.29         # Außenmaß Querschnitt
RC = 0.025       # Gurtrohr-Radius
RD = 0.010       # Diagonalen-Radius
BAY = 0.5        # Feldteilung der Diagonalen


def build():
    alu = Part("TR1_Alu", "M_Alu", sg.UV_CAB)
    steel = Part("TR1_Steel", "M_Steel", sg.UV_CAB)
    h = S / 2 - RC
    chords = [(-h, RC), (h, RC), (-h, S - RC), (h, S - RC)]     # (y, z)
    x0, x1 = -L / 2 + 0.04, L / 2 - 0.04
    for y, z in chords:
        tube(alu, (x0, y, z), (x1, y, z), RC, seg=16)
    # Zickzack-Diagonalen auf den vier Seiten
    faces = [((-h, RC), (h, RC)), ((-h, S - RC), (h, S - RC)),     # unten, oben
             ((-h, RC), (-h, S - RC)), ((h, RC), (h, S - RC))]     # links, rechts
    n = int(round((x1 - x0) / BAY))
    for fi, (a, b) in enumerate(faces):
        for k in range(n):
            xa = x0 + k * (x1 - x0) / n
            xb = x0 + (k + 1) * (x1 - x0) / n
            pa, pb = (a, b) if (k + fi) % 2 == 0 else (b, a)
            tube(alu, (xa, pa[0], pa[1]), (xb, pb[0], pb[1]), RD, seg=8)
        # Querstreben an den Enden
        tube(alu, (x0, a[0], a[1]), (x0, b[0], b[1]), RD, seg=8)
        tube(alu, (x1, a[0], a[1]), (x1, b[0], b[1]), RD, seg=8)
    # Konusverbinder an den Enden
    for sgn in (-1, 1):
        for y, z in chords:
            M = frame_matrix((sgn * (L / 2 - 0.04), y, z), (0, 1, 0), (0, 0, 1), (sgn, 0, 0))
            lathe(steel, M, [(RC * 1.05, 0.0), (RC * 1.05, 0.03), (RC * 0.6, 0.04), (0.0, 0.04)], seg=12)
        rounded_box(steel, frame_matrix((sgn * (L / 2 - 0.02), 0, S / 2), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.004, h * 0.8, h * 0.8), 0.003, seg=1)
    return {
        "name": "TR1",
        "cabinet": None, "cutters": [],
        "parts": [alu, steel],
        "bevel": 0.0,
        "dims": {"length": L, "section": S},
        "shots": {
            "front34": ((-2.2, -3.6, 1.6), (0, 0, 0.15)),
            "front_detail": ((-1.0, -0.9, 0.55), (-1.2, 0, 0.15)),
        },
    }


if __name__ == "__main__":
    s = build()
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    tot = 0
    for p in s["parts"]:
        v = np.array(p.verts); lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        print(f"{p.name:16s} {p.triangle_count():6d} Dreiecke"); tot += p.triangle_count()
    print("Summe", tot, "glTF-Maße", (hi - lo)[[0, 2, 1]].round(4), "min z", lo[2].round(4))
