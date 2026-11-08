"""
DJ-Booth "AYR-DJ1" (eigenes Design, generisch, keine Marken).

Pult 2,4 x 0,8 m, Höhe 1,0 m plus Deckplatte. Front (zum Publikum, -Y) mit
eingelassenem Lochblech und LED-Leisten dahinter, Rückseite (DJ-Seite, +Y) mit
offenem Staufach. Auf der Platte zwei Media-Player und ein 4-Kanal-Mixer.
Ursprung: Mitte der Unterseite.
"""
import math

import numpy as np

import speaker_geometry as sg
from assetlib import (Part, apply, box, cylinder, frame_matrix, hint_dir, hint_from_point,
                      lathe, rounded_box)

W, D, H = 2.40, 0.80, 1.00
FOOT = 0.03
Z0, Z1 = FOOT, FOOT + H
YF, YB = -D / 2, D / 2
TOP = Z1 + 0.04                       # Oberkante Deckplatte
MATS = ["M_Grille", "M_MetalDark", "M_Steel", "M_Rubber", "M_Plastic", "M_LED", "M_Screen", "M_Panel"]


def up(x, y, z, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return frame_matrix((x, y, z), (c, s, 0), (-s, c, 0), (0, 0, 1))


def build_cabinet():
    p = Part("DJ1_Cabinet", "M_Cabinet", sg.UV_CAB)
    hw = W / 2
    ids = p.add_verts([(-hw, YF, Z0), (hw, YF, Z0), (hw, YB, Z0), (-hw, YB, Z0),
                       (-hw, YF, Z1), (hw, YF, Z1), (hw, YB, Z1), (-hw, YB, Z1)])
    h = hint_from_point((0, 0, (Z0 + Z1) / 2))
    for f in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        p.face([ids[i] for i in f], True, h)
    return p


def build_cutters():
    front = Part("CUT_Front", None)
    box(front, up(0, YF, Z0 + 0.50), (1.08, 0.03, 0.36))           # Vertiefung für Lochblech
    shelf = Part("CUT_Shelf", None)
    box(shelf, up(0, YB - 0.15, Z0 + 0.37), (1.0, 0.17, 0.25))     # Staufach DJ-Seite
    return [front, shelf]


def media_player(parts, x):
    """Generischer Media-Player mit Jogwheel, Display und Tasten. DJ steht bei +Y."""
    zt = TOP + 0.10
    rounded_box(parts["M_MetalDark"], up(x, 0.02, TOP + 0.05), (0.16, 0.205, 0.05), 0.012, seg=2)
    # Jogwheel
    M = up(x, 0.06, zt)
    lathe(parts["M_Steel"], M, [(0.108, 0.0), (0.108, 0.006), (0.098, 0.008), (0.098, 0.004)], seg=48,
          hint=hint_dir((0, 0, 1)))
    lathe(parts["M_Plastic"], M, [(0.098, 0.004), (0.094, 0.012), (0.035, 0.012), (0.033, 0.006)], seg=48,
          hint=hint_dir((0, 0, 1)))
    lathe(parts["M_Screen"], M, [(0.033, 0.006), (0.0, 0.007)], seg=32, hint=hint_dir((0, 0, 1)))
    # Display, zum DJ geneigt
    tilt = math.radians(18)
    Md = frame_matrix((x, -0.135, zt + 0.012), (1, 0, 0), (0, math.cos(tilt), math.sin(tilt)),
                      (0, -math.sin(tilt), math.cos(tilt)))
    rounded_box(parts["M_MetalDark"], Md, (0.095, 0.045, 0.012), 0.004, seg=1)
    Ms = Md.copy(); Ms[:3, 3] = apply(Md, [(0, 0, 0.012)])[0]
    rounded_box(parts["M_Screen"], Ms, (0.085, 0.038, 0.0015), 0.0015, seg=1)
    # Play/Cue (Cue mit LED-Ring) links vorn, Tastenreihe oben
    for k, (yy, led) in enumerate([(0.17, True), (0.12, False)]):
        Mb = up(x - 0.12, yy, zt)
        cylinder(parts["M_Plastic"], Mb, 0.017, 0.0, 0.008, seg=16)
        if led:
            lathe(parts["M_LED"], Mb, [(0.019, 0.0), (0.019, 0.006), (0.017, 0.006)], seg=16, hint=hint_dir((0, 0, 1)))
    for k in range(6):
        rounded_box(parts["M_Rubber"], up(x - 0.08 + k * 0.032, -0.072, zt + 0.004), (0.011, 0.007, 0.004), 0.002, seg=1)
    # Pitch-Fader rechts
    rounded_box(parts["M_Rubber"], up(x + 0.135, 0.06, zt + 0.001), (0.006, 0.07, 0.002), 0.001, seg=1)
    rounded_box(parts["M_Plastic"], up(x + 0.135, 0.07, zt + 0.008), (0.012, 0.008, 0.007), 0.003, seg=1)


def mixer(parts):
    zt = TOP + 0.10
    rounded_box(parts["M_MetalDark"], up(0, 0.02, TOP + 0.05), (0.15, 0.205, 0.05), 0.012, seg=2)
    rounded_box(parts["M_Panel"], up(0, 0.02, zt + 0.0005), (0.14, 0.195, 0.0012), 0.003, seg=1)
    xs = [-0.09, -0.03, 0.03, 0.09]
    for i, xx in enumerate(xs):
        for r in range(4):                                     # EQ- und Gain-Regler
            Mk = up(xx, -0.15 + r * 0.045, zt + 0.001)
            cylinder(parts["M_Plastic"], Mk, 0.0105, 0.0, 0.016, seg=12)
            cylinder(parts["M_Steel"], Mk, 0.006, 0.016, 0.019, seg=10)
        rounded_box(parts["M_Rubber"], up(xx, 0.08, zt + 0.001), (0.004, 0.055, 0.002), 0.001, seg=1)   # Faderschlitz
        fy = 0.08 + [0.03, -0.01, 0.045, 0.0][i]
        rounded_box(parts["M_Plastic"], up(xx, fy, zt + 0.009), (0.012, 0.008, 0.008), 0.003, seg=1)
        rounded_box(parts["M_LED"], up(xx + 0.022, 0.06, zt + 0.0015), (0.002, 0.03, 0.001), 0.0008, seg=1)
    rounded_box(parts["M_Rubber"], up(0, 0.18, zt + 0.001), (0.05, 0.004, 0.002), 0.001, seg=1)          # Crossfader
    rounded_box(parts["M_Plastic"], up(0.012, 0.18, zt + 0.009), (0.008, 0.012, 0.008), 0.003, seg=1)


def build():
    parts = {m: Part("DJ1_" + m[2:], m, sg.UV_GRILLE if m == "M_Grille" else sg.UV_CAB) for m in MATS}
    # Lochblech-Front in der Vertiefung, LED-Leisten dahinter
    sg.add_grille(parts, xi=1.058, xo=1.07, xc=1.074, z0=Z0 + 0.14 - 0.018, z1=Z0 + 0.86 + 0.018,
                  yf=YF + 0.03, yg=YF - 0.004)
    for zz in (Z0 + 0.30, Z0 + 0.70):
        rounded_box(parts["M_LED"], frame_matrix((0, YF + 0.026, zz), (1, 0, 0), (0, 0, 1), (0, -1, 0)),
                    (1.0, 0.012, 0.003), 0.002, seg=1)
    # Deckplatte mit Überstand, Kantenschutz
    rounded_box(parts["M_MetalDark"], up(0, 0, Z1 + 0.02), (W / 2 + 0.04, D / 2 + 0.03, 0.02), 0.008, seg=2)
    rounded_box(parts["M_Rubber"], up(0, YB + 0.03, Z1 + 0.02), (W / 2 + 0.03, 0.006, 0.022), 0.005, seg=1)
    # Stellfüße
    for x in (-1.1, 1.1):
        for y in (-0.32, 0.32):
            lathe(parts["M_Steel"], up(x, y, 0.0), [(0.0, 0.0), (0.03, 0.0), (0.032, 0.006), (0.012, 0.012),
                                                    (0.012, FOOT + 0.002)], seg=16,
                  hint=hint_from_point((x, y, 0.2)))
    media_player(parts, -0.42)
    media_player(parts, 0.42)
    mixer(parts)
    # Kabelkanal hinten auf der Platte
    rounded_box(parts["M_Rubber"], up(0, -0.25, TOP + 0.015), (0.7, 0.02, 0.015), 0.008, seg=1)
    return {
        "name": "DJ1",
        "cabinet": build_cabinet(),
        "cutters": build_cutters(),
        "parts": [parts[m] for m in MATS if parts[m].faces],
        "bevel": 0.012,
        "dims": {"width": W, "depth": D, "height_total": TOP + 0.12},
        "shots": {
            "front34": ((-1.7, -3.0, 1.6), (0, 0, 0.6)),
            "front_detail": ((0.9, 1.3, 1.9), (0.1, 0.0, 1.1)),
            "rear34": ((1.9, 2.6, 1.5), (0, 0, 0.6)),
        },
    }


if __name__ == "__main__":
    s = build()
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    tot = s["cabinet"].triangle_count()
    for p in [s["cabinet"]] + s["parts"]:
        v = np.array(p.verts); lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        print(f"{p.name:16s} {p.triangle_count():6d} Dreiecke"); tot += p.triangle_count() if p is not s["cabinet"] else 0
    print("Summe", tot, "glTF-Maße", (hi - lo)[[0, 2, 1]].round(4), "min z", lo[2].round(4))
