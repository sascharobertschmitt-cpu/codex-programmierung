"""
Moving Head "AYR-MH1" (eigenes Design, generisch, keine Marke).

Aufbau in drei Gruppen, damit Babylon Pan und Tilt animieren kann:
  Sockel (fest)  ->  MH_Pan (dreht um Hochachse)  ->  MH_Tilt (kippt um X)
Stehend modelliert, Kopf zeigt in Ruhe nach oben (+Z Blender = +Y glTF).
Im Rigg wird er kopfüber unter die Traverse gehängt.
Ursprung: Mitte der Sockelunterseite.
"""
import math

import numpy as np

import speaker_geometry as sg
from assetlib import (Part, apply, cylinder, frame_matrix, hint_from_point, lathe,
                      rounded_box)

PAN_Z = 0.150          # Drehpunkt Pan (Oberkante Sockel)
TILT_Z = 0.395         # Drehachse Tilt


def P(name, mat, group=None):
    p = Part("MH1_" + name, mat, sg.UV_CAB)
    p.group = group
    return p


def up(x, y, z):
    return frame_matrix((x, y, z), (1, 0, 0), (0, 1, 0), (0, 0, 1))


def build():
    base_dark = P("BaseDark", "M_MetalDark")
    base_rubber = P("BaseRubber", "M_Rubber")
    base_screen = P("BaseScreen", "M_Screen")
    pan_dark = P("PanDark", "M_MetalDark", "MH_Pan")
    pan_steel = P("PanSteel", "M_Steel", "MH_Pan")
    tilt_dark = P("TiltDark", "M_MetalDark", "MH_Tilt")
    tilt_plastic = P("TiltPlastic", "M_Plastic", "MH_Tilt")
    tilt_lens = P("TiltLens", "M_Lens", "MH_Tilt")
    tilt_steel = P("TiltSteel", "M_Steel", "MH_Tilt")

    # --- Sockel: Gehäuse mit Display, Griffen, Gummifüßen
    rounded_box(base_dark, up(0, 0, 0.075), (0.19, 0.155, 0.075), 0.025, seg=3)
    disp = frame_matrix((0.0, -0.156, 0.085), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    rounded_box(base_screen, disp, (0.045, 0.022, 0.002), 0.002, seg=1)
    for sx in (-1, 1):                                   # Tragegriffe seitlich
        rounded_box(base_rubber, frame_matrix((sx * 0.192, 0, 0.075), (0, 1, 0), (0, 0, 1), (sx, 0, 0)),
                    (0.07, 0.02, 0.008), 0.006, seg=1)
        for sy in (-1, 1):
            lathe(base_rubber, up(sx * 0.15, sy * 0.115, 0.0),
                  [(0.0, -0.001), (0.018, -0.001), (0.02, 0.006), (0.0, 0.006)], seg=8,
                  hint=hint_from_point((sx * 0.15, sy * 0.115, 0.05)))
    # Lüftungsschlitze auf der Front
    for k in range(3):
        rounded_box(base_rubber, frame_matrix((0.095, -0.156, 0.045 + k * 0.016), (1, 0, 0), (0, 0, 1), (0, -1, 0)),
                    (0.04, 0.003, 0.0015), 0.0012, seg=1)

    # --- Pan-Gruppe: Drehteller + U-Bügel
    lathe(pan_steel, up(0, 0, PAN_Z), [(0.0, 0.0), (0.085, 0.0), (0.09, 0.008), (0.085, 0.014), (0.0, 0.014)], seg=32,
          hint=hint_from_point((0, 0, PAN_Z + 0.007)))
    rounded_box(pan_dark, up(0, 0, PAN_Z + 0.032), (0.175, 0.07, 0.018), 0.012, seg=2)
    for sx in (-1, 1):
        rounded_box(pan_dark, up(sx * 0.155, 0, PAN_Z + 0.16), (0.022, 0.065, 0.15), 0.014, seg=1)
        # Tilt-Lager außen am Bügel
        cylinder(pan_steel, frame_matrix((sx * 0.177, 0, TILT_Z), (0, 1, 0), (0, 0, 1), (sx, 0, 0)),
                 0.03, 0.0, 0.012, seg=20)

    # --- Tilt-Gruppe: Kopf (Rotationskörper entlang Z), Linse, Kühlrippen, Achsstummel
    M = up(0, 0, TILT_Z)
    body = [(0.0, -0.13), (0.07, -0.13), (0.095, -0.115), (0.11, -0.08), (0.115, 0.04),
            (0.13, 0.10), (0.135, 0.13)]
    lathe(tilt_dark, M, body, seg=40, hint=hint_from_point(apply(M, [(0, 0, 0)])[0]))
    bezel = [(0.135, 0.13), (0.138, 0.142), (0.128, 0.150), (0.112, 0.146), (0.108, 0.138)]
    lathe(tilt_plastic, M, bezel, seg=40, hint=hint_from_point(apply(M, [(0, 0, 0)])[0]))
    lens = [(0.108, 0.136), (0.07, 0.143), (0.0, 0.146)]
    lathe(tilt_lens, M, lens, seg=40, hint=hint_from_point(apply(M, [(0, 0, 0)])[0]))
    for k in range(4):                                   # Kühlrippen hinten
        z = -0.10 + k * 0.03
        lathe(tilt_plastic, M, [(0.114, z), (0.122, z + 0.004), (0.122, z + 0.010), (0.114, z + 0.014)], seg=24,
              hint=hint_from_point(apply(M, [(0, 0, z + 0.007)])[0]))
    for sx in (-1, 1):
        cylinder(tilt_steel, frame_matrix((sx * 0.112, 0, TILT_Z), (0, 1, 0), (0, 0, 1), (sx, 0, 0)),
                 0.018, 0.0, 0.03, seg=16)

    parts = [base_dark, base_rubber, base_screen, pan_dark, pan_steel,
             tilt_dark, tilt_plastic, tilt_lens, tilt_steel]
    return {
        "name": "MH1",
        "cabinet": None, "cutters": [],
        "parts": parts,
        "groups": {
            "MH_Pan": {"parent": None, "origin": (0.0, 0.0, PAN_Z)},
            "MH_Tilt": {"parent": "MH_Pan", "origin": (0.0, 0.0, TILT_Z)},
        },
        "bevel": 0.0,
        "dims": {"width": 0.40, "height": 0.55},
        "shots": {
            "front34": ((-0.75, -1.15, 0.65), (0, 0, 0.30)),
            "front_detail": ((-0.35, -0.45, 0.75), (0, 0, 0.45)),
        },
    }


if __name__ == "__main__":
    s = build()
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    tot = 0
    for p in s["parts"]:
        v = np.array(p.verts); lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        print(f"{p.name:16s} {p.group or '-':8s} {p.triangle_count():6d} Dreiecke"); tot += p.triangle_count()
    print("Summe", tot, "glTF-Maße", (hi - lo)[[0, 2, 1]].round(4), "min z", lo[2].round(4))
