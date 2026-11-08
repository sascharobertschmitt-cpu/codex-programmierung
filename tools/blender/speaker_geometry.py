"""
Geometrie des Club-PA-Topteils "AYR-212" (eigenes Design, keine Marke).

2-Wege-Topteil im MTM-Layout: 2 x 12"-Tieftoener, dazwischen ein
Rechteck-Waveguide (Horn) fuer den Hochtonbereich. Trapezfoermiges Gehaeuse
(hinten schmaler, typisch fuer Club-/Touring-Tops), Lochblechgitter mit
umgekantetem Rand, Stahl-Buegelgriffe, Flugschienen oben, Anschlussfeld hinten.

Masse in Metern. Blender-Achsen: Z oben, Front nach -Y, Ursprung = Bodenmitte.
Diese Datei ist reines Python/numpy und laeuft auch ohne Blender.
"""
import math

import numpy as np

from assetlib import (Part, apply, box, cylinder, frame_matrix, hint_dir,
                      hint_from_axis, hint_from_point, hint_toward_point, lathe,
                      rounded_box, superellipse)

# ---------------------------------------------------------------------------
# Hauptmasse
# ---------------------------------------------------------------------------
FOOT_H = 0.008                 # Gummifuesse
H = 0.980                      # Gehaeusehoehe
WF = 0.600                     # Breite vorne
WR = 0.400                     # Breite hinten
D = 0.500                      # Tiefe
Z0 = FOOT_H                    # Gehaeuseunterkante
Z1 = FOOT_H + H                # Gehaeuseoberkante
YF = -D / 2                    # Frontebene
YB = D / 2                     # Rueckwand
BEVEL = 0.014                  # Gehaeusekantenradius

WOOFER_Z = (Z0 + 0.205, Z0 + 0.775)
HORN_Z = Z0 + 0.490
HORN_W, HORN_H = 0.215, 0.100  # halbe Mundoeffnung
GRILLE_Y = YF - 0.016          # Gitterflaeche vor der Front

UV_CAB = 1 / 0.10              # Kornstruktur: 256 px auf 10 cm
UV_GRILLE = 1 / 0.024          # 4 x 4 Loecher pro 24 mm -> 6 mm Teilung


def half_width_at(y):
    """Halbe Gehaeusebreite in Abhaengigkeit von y (Trapez)."""
    t = (y - YF) / (YB - YF)
    return (WF + (WR - WF) * t) / 2


def front_frame(x, z, out=0.0):
    """Lokaler Rahmen auf der Front: lokal Z zeigt nach vorne (-Y)."""
    return frame_matrix((x, YF - out, z), (1, 0, 0), (0, 0, 1), (0, -1, 0))


# ---------------------------------------------------------------------------
# Bauteile
# ---------------------------------------------------------------------------
def build_cabinet():
    p = Part("AYR212_Cabinet", "M_Cabinet", UV_CAB)
    hf, hb = WF / 2, WR / 2
    pts = [(-hf, YF, Z0), (hf, YF, Z0), (hb, YB, Z0), (-hb, YB, Z0),
           (-hf, YF, Z1), (hf, YF, Z1), (hb, YB, Z1), (-hb, YB, Z1)]
    ids = p.add_verts(pts)
    c = np.array([0, 0, (Z0 + Z1) / 2])
    h = hint_from_point(c)
    for f in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        p.face([ids[i] for i in f], True, h)
    return p


def build_cutters():
    """Boolean-Schneidkoerper fuer Tieftoener- und Hornausschnitte."""
    cutters = []
    for i, z in enumerate(WOOFER_Z):
        c = Part(f"CUT_Woofer{i}", None)
        cylinder(c, front_frame(0, z), 0.142, -0.085, 0.03, seg=48, caps=True, smooth=False)
        cutters.append(c)
    c = Part("CUT_Horn", None)
    M = front_frame(0, HORN_Z)
    M2 = M.copy()
    M2[:3, 3] = apply(M, [(0, 0, -0.07)])[0]
    box(c, M2, (HORN_W, HORN_H, 0.10))
    cutters.append(c)
    return cutters


def add_woofer(parts, z):
    M = front_frame(0, z)
    behind = apply(M, [(0, 0, -0.5)])[0]
    hint = hint_from_point(behind)

    # Druckguss-Korbrand, liegt 10 mm auf der Schallwand auf
    frame = [(0.153, -0.001), (0.153, 0.006), (0.150, 0.0095), (0.146, 0.0105),
             (0.134, 0.0105), (0.131, 0.0085), (0.129, 0.004)]
    lathe(parts["M_MetalDark"], M, frame, seg=64, hint=hint)

    # Gummisicke (Halbrolle)
    sur = []
    for t in np.linspace(0, np.pi, 9):
        sur.append((0.120 + 0.009 * math.cos(t), 0.004 + 0.0085 * math.sin(t)))
    lathe(parts["M_Rubber"], M, sur, seg=64, hint=hint)

    # Membran: leicht gekruemmter Konus
    cone = []
    for t in np.linspace(0, 1, 11):
        r = 0.111 - 0.065 * t
        cone.append((r, 0.004 - 0.056 * t ** 0.8))
    lathe(parts["M_Cone"], M, cone, seg=64, hint=hint)

    # Staubschutzkalotte
    cap = []
    for t in np.linspace(0, 1, 7):
        r = 0.046 * math.cos(t * math.pi / 2)
        cap.append((r, -0.052 + 0.017 * math.sin(t * math.pi / 2)))
    lathe(parts["M_DustCap"], M, cap, seg=48, hint=hint)

    # 8 Befestigungsschrauben auf dem Korbrand
    for k in range(8):
        a = (k + 0.5) / 8 * 2 * math.pi
        x, y = 0.1405 * math.cos(a), 0.1405 * math.sin(a)
        Ms = M.copy()
        Ms[:3, 3] = apply(M, [(x, y, 0.0105)])[0]
        screw_head(parts["M_Steel"], Ms, 0.0042)


def screw_head(part, M, r):
    """Linsenkopfschraube mit angedeutetem Innensechskant (Vertiefung)."""
    prof = [(r, 0.0), (r, 0.0009), (r * 0.75, 0.0024), (r * 0.42, 0.0027),
            (r * 0.42, 0.0016), (0.0, 0.0016)]
    lathe(part, M, prof, seg=10, smooth=True,
          hint=hint_from_point(apply(M, [(0, 0, -0.05)])[0]))


def add_horn(parts):
    M = front_frame(0, HORN_Z)
    p = parts["M_Horn"]
    n_ring = 40
    rings = []
    steps = 16
    for i in range(steps + 1):
        t = i / steps
        f = t ** 1.7
        w = 0.024 + (HORN_W - 0.024) * f
        h = 0.020 + (HORN_H - 0.020) * f
        n = 2.2 + 4.0 * t
        z = -0.150 * (1 - t) ** 1.15
        x, y = superellipse(w, h, n, n_ring)
        rings.append(apply(M, np.stack([x, y, np.full(n_ring, z)], -1)))
    # Mundkante rollt nach vorn auf den Flansch
    for k, (dw, dz) in enumerate([(0.003, 0.003), (0.008, 0.006), (0.020, 0.006)]):
        x, y = superellipse(HORN_W + dw, HORN_H + dw, 6.2, n_ring)
        rings.append(apply(M, np.stack([x, y, np.full(n_ring, dz)], -1)))
    front_pt = apply(M, [(0, 0, 1.0)])[0]
    p.grid(rings, closed=True, smooth=True, hint=hint_toward_point(front_pt))
    # Aussenkante des Flansches
    x, y = superellipse(HORN_W + 0.020, HORN_H + 0.020, 6.2, n_ring)
    outer = [apply(M, np.stack([x, y, np.full(n_ring, z)], -1)) for z in (0.006, -0.001)]
    p.grid(outer, closed=True, smooth=True,
           hint=hint_from_axis(M[:3, 3], M[:3, 2]))
    # Phasenstopfen am Hals
    x, y = superellipse(0.024, 0.020, 2.2, n_ring)
    plug = apply(M, np.stack([x, y, np.full(n_ring, -0.150)], -1))
    parts["M_MetalDark"].poly(plug, False, hint_dir(M[:3, 2]))
    # Flanschschrauben
    for sx in (-1, 1):
        for sy in (-1, 1):
            Ms = M.copy()
            Ms[:3, 3] = apply(M, [(sx * (HORN_W + 0.010), sy * (HORN_H + 0.010), 0.006)])[0]
            screw_head(parts["M_Steel"], Ms, 0.0035)


def add_grille(parts):
    """Lochblech mit massivem Rahmen, Fase und nach hinten gekantetem Rand."""
    g = parts["M_Grille"]
    fr = parts["M_MetalDark"]
    xi, zi0, zi1 = 0.262, Z0 + 0.034, Z1 - 0.034         # Lochfeld
    xo, zo0, zo1 = 0.274, Z0 + 0.022, Z1 - 0.022         # Aussenkante Front
    xc, zc0, zc1 = 0.278, Z0 + 0.018, Z1 - 0.018         # nach Fase
    yg = GRILLE_Y
    fwd = hint_dir((0, -1, 0))

    g.poly([(-xi, yg, zi0), (xi, yg, zi0), (xi, yg, zi1), (-xi, yg, zi1)], False, fwd)

    def rect(x, z0, z1, y):
        return [(-x, y, z0), (x, y, z0), (x, y, z1), (-x, y, z1)]

    inner = rect(xi, zi0, zi1, yg)
    outer = rect(xo, zo0, zo1, yg)
    for k in range(4):
        k2 = (k + 1) % 4
        fr.poly([inner[k], inner[k2], outer[k2], outer[k]], False, fwd)

    # Fase + Ruecksprung zum Gehaeuse
    center = np.array([0, YF, (Z0 + Z1) / 2])
    out_hint = hint_from_axis(center, (0, 1, 0))
    rings = [outer, rect(xc, zc0, zc1, yg + 0.004), rect(xc, zc0, zc1, YF + 0.002)]
    hints = [lambda c: out_hint(c) * 0.5 + np.array([0, -1, 0]), out_hint]
    for a, b, hh in zip(rings[:-1], rings[1:], hints):
        for k in range(4):
            k2 = (k + 1) % 4
            fr.poly([a[k], a[k2], b[k2], b[k]], False, hh)

    # Rahmenschrauben
    xm = (xi + xo) / 2
    zm0, zm1 = (zi0 + zo0) / 2, (zi1 + zo1) / 2
    for x, z in [(-xm, zm0), (xm, zm0), (-xm, zm1), (xm, zm1), (0, zm0), (0, zm1),
                 (-xm, (Z0 + Z1) / 2), (xm, (Z0 + Z1) / 2)]:
        M = frame_matrix((x, yg, z), (1, 0, 0), (0, 0, 1), (0, -1, 0))
        screw_head(parts["M_Steel"], M, 0.0042)


def side_frame(sign, y, z, out=0.0):
    """Lokaler Rahmen auf einer Seitenwand: X entlang der Wand nach hinten,
    Y nach oben, Z = Aussennormale."""
    d = np.array([sign * (WR - WF) / 2, D, 0.0])
    d /= np.linalg.norm(d)
    n = np.array([sign * D, (WF - WR) / 2, 0.0])
    n /= np.linalg.norm(n)
    x = sign * half_width_at(y)
    o = np.array([x, y, z]) + n * out
    yax = np.array([0, 0, 1.0])
    xax = d if sign > 0 else -d       # rechtshaendig halten
    if np.dot(np.cross(xax, yax), n) < 0:
        xax = -xax
    return frame_matrix(o, xax, yax, n)


def add_handles(parts):
    for sign in (-1, 1):
        M = side_frame(sign, 0.0, Z0 + 0.66)
        # flache Griffschale
        Mp = M.copy()
        Mp[:3, 3] = apply(M, [(0, 0, 0.0)])[0]
        rounded_box(parts["M_MetalDark"], Mp, (0.085, 0.034, 0.004), 0.0035, seg=2)
        # Buegel: zwei Stuetzen + Stange
        for sx in (-1, 1):
            Ms = M.copy()
            Ms[:3, 3] = apply(M, [(sx * 0.058, 0, 0.0)])[0]
            cylinder(parts["M_Steel"], Ms, 0.0075, 0.0, 0.030, seg=16)
        Mb = frame_matrix(apply(M, [(0, 0, 0.030)])[0], M[:3, 1], M[:3, 2], M[:3, 0])
        cylinder(parts["M_Steel"], Mb, 0.0085, -0.066, 0.066, seg=16)
        for sx in (-1, 1):
            Ms = M.copy()
            Ms[:3, 3] = apply(M, [(sx * 0.074, 0, 0.004)])[0]
            screw_head(parts["M_Steel"], Ms, 0.004)


def add_fly_tracks(parts):
    """Zwei Flugschienen oben mit Anschlagpunkten."""
    for x in (-0.13, 0.13):
        M = frame_matrix((x, -0.01, Z1 + 0.0025), (0, 1, 0), (-1, 0, 0), (0, 0, 1))
        rounded_box(parts["M_Steel"], M, (0.170, 0.022, 0.0035), 0.003, seg=2)
        for yy in (-0.13, 0.0, 0.13):
            Mh = frame_matrix((x, -0.01 + yy, Z1 + 0.006), (1, 0, 0), (0, 1, 0), (0, 0, 1))
            cylinder(parts["M_MetalDark"], Mh, 0.008, -0.0004, 0.0003, seg=16)
            lathe(parts["M_MetalDark"], Mh, [(0.0105, -0.0002), (0.0105, 0.0006), (0.0080, 0.0006)],
                  seg=16, hint=hint_dir((0, 0, 1)))


def add_feet_and_pole_cup(parts):
    for x in (-0.22, 0.22):
        for y in (-0.18, 0.17):
            M = frame_matrix((x, y, 0.0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
            lathe(parts["M_Rubber"], M,
                  [(0.0, 0.0), (0.020, 0.0), (0.024, 0.003), (0.025, FOOT_H + 0.001)],
                  seg=20, hint=hint_from_point((x, y, 0.05)))
    M = frame_matrix((0, 0, Z0 - 0.002), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    lathe(parts["M_MetalDark"], M,
          [(0.045, 0.003), (0.045, 0.0), (0.020, 0.0), (0.0185, 0.001), (0.0, 0.001)],
          seg=32, hint=hint_from_point((0, 0, 0.3)))


def add_rear_panel(parts):
    """Anschlussfeld: Alu-Platte, zwei Lautsprecherbuchsen (generisch), Schrauben."""
    def rear(x, z, out=0.0):
        return frame_matrix((x, YB + out, z), (-1, 0, 0), (0, 0, 1), (0, 1, 0))

    zc = Z0 + 0.30
    rounded_box(parts["M_Panel"], rear(0, zc, 0.0015), (0.100, 0.062, 0.0025), 0.004, seg=2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            screw_head(parts["M_Steel"], rear(sx * 0.088, zc + sz * 0.050, 0.004), 0.0035)
    for x in (-0.042, 0.042):
        M = rear(x, zc + 0.004, 0.004)
        hint = hint_from_point(apply(M, [(0, 0, -0.05)])[0])
        # Flansch, Ring, Einsatz
        lathe(parts["M_Horn"], M,
              [(0.026, 0.0), (0.026, 0.0025), (0.0215, 0.0045), (0.0185, 0.0090),
               (0.0160, 0.0090), (0.0160, 0.0030), (0.0110, 0.0030)], seg=32, hint=hint)
        lathe(parts["M_Rubber"], M, [(0.0110, 0.0030), (0.0060, 0.0050), (0.0, 0.0050)],
              seg=24, hint=hint)
        # Verriegelungslasche
        Mt = M.copy()
        Mt[:3, 3] = apply(M, [(0, -0.030, 0.003)])[0]
        rounded_box(parts["M_Horn"], Mt, (0.0045, 0.006, 0.003), 0.0015, seg=1)
        # Befestigungsschrauben der Buchse
        for a in (math.radians(45), math.radians(225)):
            Ms = M.copy()
            Ms[:3, 3] = apply(M, [(0.0225 * math.cos(a), 0.0225 * math.sin(a), 0.0025)])[0]
            screw_head(parts["M_Steel"], Ms, 0.0022)
    # leeres Typenschild (keine Marke, nur Flaeche)
    rounded_box(parts["M_MetalDark"], rear(0, Z0 + 0.46, 0.001), (0.070, 0.030, 0.0012), 0.002, seg=1)


# ---------------------------------------------------------------------------
MATERIAL_ORDER = ["M_Grille", "M_MetalDark", "M_Steel", "M_Rubber", "M_Cone",
                  "M_DustCap", "M_Horn", "M_Panel"]


def build_speaker():
    parts = {m: Part("AYR212_" + m[2:], m, UV_GRILLE if m == "M_Grille" else UV_CAB)
             for m in MATERIAL_ORDER}
    for z in WOOFER_Z:
        add_woofer(parts, z)
    add_horn(parts)
    add_grille(parts)
    add_handles(parts)
    add_fly_tracks(parts)
    add_feet_and_pole_cup(parts)
    add_rear_panel(parts)
    return {
        "cabinet": build_cabinet(),
        "cutters": build_cutters(),
        "parts": [parts[m] for m in MATERIAL_ORDER if parts[m].faces],
        "bevel": BEVEL,
        "dims": {"width_front": WF, "width_rear": WR, "depth": D, "height_total": Z1},
    }


if __name__ == "__main__":
    s = build_speaker()
    tot = s["cabinet"].triangle_count()
    for p in s["parts"]:
        print(f"{p.name:24s} {p.triangle_count():6d} Dreiecke")
        tot += p.triangle_count()
    print("Summe (ohne Bevel/Boolean)", tot)
