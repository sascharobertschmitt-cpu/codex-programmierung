"""
Geometrie des Club-Subwoofers "AYR-118" (eigenes Design, keine Marke).

1 x 18"-Tieftoener, frontgeladen, Bassreflex mit breitem Schlitzport unten.
Gleiche Bauteilsprache wie das Topteil AYR-212 (Gitter, Schrauben, Griffe,
Anschlussfeld), damit beide als Stack zusammenpassen. Oben M20-Stativflansch
und Stapelpads, hinten Transportrollen.

Masse in Metern. Blender-Achsen: Z oben, Front nach -Y, Ursprung = Bodenmitte.
"""
import math

import numpy as np

import speaker_geometry as sg
from assetlib import (Part, apply, box, cylinder, frame_matrix, hint_from_axis,
                      hint_from_point, hint_toward_point, lathe, rounded_box,
                      superellipse)

FOOT_H = 0.008
H = 0.640
W = 0.600
D = 0.720
Z0 = FOOT_H
Z1 = FOOT_H + H
YF = -D / 2
YB = D / 2
BEVEL = 0.014

WOOFER_SCALE = 1.5                    # 18"
WOOFER_Z = Z0 + 0.365
SLOT_Z = Z0 + 0.078
SLOT_W, SLOT_H = 0.235, 0.030         # halbe Schlitzoeffnung
SLOT_DEPTH = 0.32


def front(x, z, out=0.0):
    return frame_matrix((x, YF - out, z), (1, 0, 0), (0, 0, 1), (0, -1, 0))


def rear(x, z, out=0.0):
    return sg.rear_frame(x, z, out, yb=YB)


def side(sign, y, z):
    return frame_matrix((sign * W / 2, y, z), (0, sign, 0), (0, 0, 1), (sign, 0, 0))


def build_cabinet():
    p = Part("AYR118_Cabinet", "M_Cabinet", sg.UV_CAB)
    hw = W / 2
    pts = [(-hw, YF, Z0), (hw, YF, Z0), (hw, YB, Z0), (-hw, YB, Z0),
           (-hw, YF, Z1), (hw, YF, Z1), (hw, YB, Z1), (-hw, YB, Z1)]
    ids = p.add_verts(pts)
    h = hint_from_point((0, 0, (Z0 + Z1) / 2))
    for f in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        p.face([ids[i] for i in f], True, h)
    return p


def build_cutters():
    c1 = Part("CUT_Woofer", None)
    cylinder(c1, front(0, WOOFER_Z), 0.142 * WOOFER_SCALE, -0.13, 0.03, seg=56, caps=True, smooth=False)
    c2 = Part("CUT_Slot", None)
    M = front(0, SLOT_Z)
    M2 = M.copy()
    M2[:3, 3] = apply(M, [(0, 0, -SLOT_DEPTH / 2 + 0.015)])[0]
    box(c2, M2, (SLOT_W, SLOT_H, SLOT_DEPTH / 2 + 0.02))
    return [c1, c2]


def add_slot_port(parts):
    """Schlitzport mit ausgerundetem Kragen, innen dunkel."""
    M = front(0, SLOT_Z)
    p = parts["M_Horn"]
    n = 48
    rings = []
    x, y = superellipse(SLOT_W - 0.002, SLOT_H - 0.002, 10, n)
    for z in (-SLOT_DEPTH, -0.004):
        rings.append(apply(M, np.stack([x, y, np.full(n, z)], -1)))
    for dw, dz in [(0.003, 0.003), (0.008, 0.006), (0.020, 0.006)]:
        x2, y2 = superellipse(SLOT_W + dw, SLOT_H + dw, 10, n)
        rings.append(apply(M, np.stack([x2, y2, np.full(n, dz)], -1)))
    front_pt = apply(M, [(0, 0, 1.0)])[0]
    p.grid(rings, closed=True, smooth=True, hint=hint_toward_point(front_pt))
    xo, yo = superellipse(SLOT_W + 0.020, SLOT_H + 0.020, 10, n)
    outer = [apply(M, np.stack([xo, yo, np.full(n, z)], -1)) for z in (0.006, -0.001)]
    p.grid(outer, closed=True, smooth=True, hint=hint_from_axis(M[:3, 3], M[:3, 2]))
    back = apply(M, np.stack([x, y, np.full(n, -SLOT_DEPTH)], -1))
    parts["M_Rubber"].poly(back, False, hint_toward_point(front_pt))
    for sx in (-1, 0, 1):
        Ms = M.copy()
        Ms[:3, 3] = apply(M, [(sx * (SLOT_W + 0.004), SLOT_H + 0.011, 0.006)])[0]
        sg.screw_head(parts["M_Steel"], Ms, 0.0032)


def add_top(parts):
    """M20-Stativflansch mittig, vier Stapelpads."""
    M = frame_matrix((0, 0, Z1), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    lathe(parts["M_MetalDark"], M,
          [(0.050, -0.001), (0.050, 0.002), (0.046, 0.0035), (0.022, 0.0035),
           (0.019, 0.001), (0.0175, -0.010), (0.0175, -0.060), (0.0, -0.060)],
          seg=40, hint=hint_from_point((0, 0, Z1 - 0.3)))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        Ms = frame_matrix((0.040 * math.cos(a), 0.040 * math.sin(a), Z1 + 0.0035),
                          (1, 0, 0), (0, 1, 0), (0, 0, 1))
        sg.screw_head(parts["M_Steel"], Ms, 0.0035)
    for x in (-0.22, 0.22):
        for y in (-0.27, 0.27):
            Mp = frame_matrix((x, y, Z1 + 0.001), (1, 0, 0), (0, 1, 0), (0, 0, 1))
            rounded_box(parts["M_Rubber"], Mp, (0.035, 0.035, 0.0035), 0.003, seg=2)


def add_feet(parts):
    for x in (-0.23, 0.23):
        for y in (-0.29, 0.22):
            M = frame_matrix((x, y, 0.0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
            lathe(parts["M_Rubber"], M,
                  [(0.0, 0.0), (0.022, 0.0), (0.026, 0.003), (0.027, FOOT_H + 0.001)],
                  seg=20, hint=hint_from_point((x, y, 0.05)))


def add_casters(parts):
    """Zwei Transportrollen an der unteren Hinterkante (heben beim Kippen an)."""
    r_wheel, half_w = 0.042, 0.016
    zc = Z0 + 0.050
    yc = YB + 0.034
    for x in (-0.20, 0.20):
        # Rad: Lauffläche und Felge, Achse entlang X
        M = frame_matrix((x, yc, zc), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        hint = hint_from_point(apply(M, [(0, 0, 0)])[0])
        tire = [(0.020, -half_w), (0.034, -half_w), (0.040, -half_w + 0.003), (r_wheel, -0.006),
                (r_wheel, 0.006), (0.040, half_w - 0.003), (0.034, half_w), (0.020, half_w)]
        lathe(parts["M_Rubber"], M, tire, seg=32, hint=hint)
        for sgn in (-1, 1):
            lathe(parts["M_MetalDark"], M,
                  [(0.020, sgn * half_w), (0.012, sgn * (half_w + 0.001)), (0.0, sgn * (half_w + 0.001))],
                  seg=24, hint=hint)
        # Gabel: zwei Wangen + Achse + Montageplatte
        for sgn in (-1, 1):
            Mc = frame_matrix((x + sgn * (half_w + 0.006), YB + 0.021, zc + 0.006),
                              (1, 0, 0), (0, 1, 0), (0, 0, 1))
            rounded_box(parts["M_Steel"], Mc, (0.0025, 0.021, 0.030), 0.0015, seg=1)
        Ma = frame_matrix((x, yc, zc), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        cylinder(parts["M_Steel"], Ma, 0.006, -half_w - 0.010, half_w + 0.010, seg=12)
        Mpl = frame_matrix((x, YB + 0.002, zc + 0.012), (-1, 0, 0), (0, 0, 1), (0, 1, 0))
        rounded_box(parts["M_Steel"], Mpl, (0.040, 0.042, 0.0025), 0.002, seg=1)
        for sx in (-1, 1):
            for sz in (-1, 1):
                Ms = frame_matrix((x + sx * 0.031, YB + 0.0045, zc + 0.012 + sz * 0.032),
                                  (-1, 0, 0), (0, 0, 1), (0, 1, 0))
                sg.screw_head(parts["M_Steel"], Ms, 0.003)


MATERIAL_ORDER = sg.MATERIAL_ORDER


def build():
    parts = {m: Part("AYR118_" + m[2:], m, sg.UV_GRILLE if m == "M_Grille" else sg.UV_CAB)
             for m in MATERIAL_ORDER}
    sg.add_woofer(parts, None, scale=WOOFER_SCALE, M=front(0, WOOFER_Z))
    add_slot_port(parts)
    sg.add_grille(parts, z0=Z0, z1=Z1, yf=YF)
    for sign in (-1, 1):
        sg.bar_handle(parts, side(sign, 0.0, Z0 + 0.48))
    add_top(parts)
    add_feet(parts)
    sg.connector_panel(parts, rear, Z0 + 0.44)
    for x in (-0.24, 0.24):
        for z in (Z0 + 0.20, Z1 - 0.06):
            sg.rigging_point(parts, rear(x, z))
    rounded_box(parts["M_MetalDark"], rear(0, Z0 + 0.56, 0.001), (0.070, 0.030, 0.0012), 0.002, seg=1)
    add_casters(parts)
    return {
        "name": "AYR118",
        "cabinet": build_cabinet(),
        "cutters": build_cutters(),
        "parts": [parts[m] for m in MATERIAL_ORDER if parts[m].faces],
        "bevel": BEVEL,
        "dims": {"width": W, "depth": D, "height_total": Z1},
        "shots": {
            "front34": ((-1.45, -2.5, 0.95), (0, 0, 0.33)),
            "front_detail": ((-0.45, -1.35, 0.55), (0, -0.36, 0.30)),
            "rear34": ((1.6, 2.4, 1.0), (0, 0, 0.30)),
        },
    }


if __name__ == "__main__":
    s = build()
    tot = s["cabinet"].triangle_count()
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for p in [s["cabinet"]] + s["parts"]:
        v = np.array(p.verts)
        lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        print(f"{p.name:24s} {p.triangle_count():6d} Dreiecke")
        tot += p.triangle_count()
    print("Summe", tot)
    print("Masse Blender (x, y, z):", (hi - lo).round(4), "-> glTF (x, y, z):", (hi - lo)[[0, 2, 1]].round(4))
