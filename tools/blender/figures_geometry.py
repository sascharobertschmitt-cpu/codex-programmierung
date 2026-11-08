"""
Spielfiguren und Club-Figuren fuer "Aal You Ready?" (eigenes Design, stilisiert, keine Marken).

Stil: Vinyl-Toy / Brettspielfigur. Grosser Kopf, kurzer Koerper, klare Silhouette.
Masse: Blender-Meter, Z oben, Front -Y. Ursprung Mitte Fussunterseite.
Spielfiguren sind ca. 0.8 m hoch modelliert und werden in der Szene skaliert.

Materialien:
  M_Accent  Spielerfarbe. Babylon faerbt dieses Material pro Spieler um.
  M_Cloth   dunkler Stoff, M_Skin1..3 Hauttoene, M_Eel Aalhaut, M_White Augen/Schnuere,
  M_DustCap glaenzend schwarz (Brillen, Pupillen), M_Glow Leuchtstab, M_LED Visier.

Aufruf ueber die Wrapper-Module fig_*_geometry.py (je eine GLB pro Figur).
"""
import math

import numpy as np

from assetlib import Part, cylinder, frame_matrix, hint_from_point, lathe, rounded_box, tube

UV = 1 / 0.10
KINDS = ("raver", "dj", "tuersteher", "aal", "robo", "gasmaske")


class Kit:
    """Sammelt Parts pro Material (ein Mesh pro Material)."""

    def __init__(self, prefix, group=None):
        self.prefix = prefix
        self.group = group
        self.parts = {}

    def __getitem__(self, mat):
        if mat not in self.parts:
            p = Part(f"{self.prefix}_{mat[2:]}", mat, UV)
            p.group = self.group
            self.parts[mat] = p
        return self.parts[mat]

    def list(self):
        return [p for p in self.parts.values() if p.faces]


# ---------------------------------------------------------------------------
# Grundformen
# ---------------------------------------------------------------------------
def ellipsoid(part, c, r, seg=20, rings=12, axes=None):
    """Ellipsoid um Mittelpunkt c mit Halbachsen r=(rx, ry, rz). axes: optionale Drehung (3x3)."""
    rx, ry, rz = (r, r, r) if np.isscalar(r) else r
    R = np.eye(3) if axes is None else np.asarray(axes, float)
    M = frame_matrix(c, R[:, 0] * rx, R[:, 1] * ry, R[:, 2] * rz)
    prof = [(math.sin(t), -math.cos(t)) for t in np.linspace(0, math.pi, rings + 1)]
    prof[0] = (0.0, -1.0)
    prof[-1] = (0.0, 1.0)
    lathe(part, M, prof, seg=seg, hint=hint_from_point(c))


def capsule(part, a, b, r, seg=14):
    a, b = np.asarray(a, float), np.asarray(b, float)
    tube(part, a, b, r, seg=seg, caps=False)
    ellipsoid(part, a, r, seg=seg, rings=8)
    ellipsoid(part, b, r, seg=seg, rings=8)


def limb(part, pts, r, seg=14):
    """Gelenkkette (Schulter, Ellbogen, Hand) aus Kapseln."""
    for a, b in zip(pts[:-1], pts[1:]):
        capsule(part, a, b, r, seg)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def sweep(part, pts, radii, seg=16, cap_start=True, cap_end=True):
    """Schlauch entlang einer Punktfolge mit variablem Radius (Aalkoerper)."""
    pts = [np.asarray(p, float) for p in pts]
    n = len(pts)
    tang = []
    for i in range(n):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tang.append(d / np.linalg.norm(d))
    # Parallel Transport der Rahmen, damit sich der Schlauch nicht verdreht
    up = np.array([0.0, 0.0, 1.0]) if abs(tang[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(up, tang[0]); x /= np.linalg.norm(x)
    frames = []
    for i in range(n):
        if i:
            x = x - tang[i] * np.dot(x, tang[i])
            x /= np.linalg.norm(x)
        y = np.cross(tang[i], x)
        frames.append((x.copy(), y))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    rings = []
    for p, (fx, fy), r in zip(pts, frames, radii):
        rings.append([p + r * (math.cos(t) * fx + math.sin(t) * fy) for t in a])
    if cap_start:
        rings.insert(0, [pts[0] - tang[0] * radii[0] * 0.6])
    if cap_end:
        rings.append([pts[-1] + tang[-1] * radii[-1] * 0.6])

    # Normalen: radial weg von der Mittellinie
    centers = list(pts)

    def hint(c):
        d = [np.linalg.norm(c - q) for q in centers]
        return c - centers[int(np.argmin(d))]
    part.grid(rings, closed=True, smooth=True, hint=hint)


# ---------------------------------------------------------------------------
# Gemeinsamer Koerper (Beine, Rumpf, Kopf)
# ---------------------------------------------------------------------------
HEAD_Z = 0.615
HEAD_R = 0.148
SH_Z = 0.425          # Schulterhoehe


def legs(k, shoe="M_Rubber", pants="M_Cloth", spread=0.062, boots=False):
    for s in (-1, 1):
        x = s * spread
        capsule(k[pants], (x, 0.0, 0.075), (x, 0.0, 0.235), 0.047)
        h = 0.045 if boots else 0.032
        rounded_box(k[shoe], frame_matrix((x, -0.016, h), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.048, 0.072, h), 0.022, seg=2)
        if not boots:          # weisse Sohle wie Sneaker
            rounded_box(k["M_White"], frame_matrix((x, -0.016, 0.009), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                        (0.051, 0.075, 0.009), 0.006, seg=1)


def torso(k, mat="M_Accent", wide=1.0, z0=0.20, z1=0.47):
    M = frame_matrix((0, 0, 0), (wide, 0, 0), (0, 0.78, 0), (0, 0, 1))
    h = z1 - z0
    prof = [(0.0, z0), (0.105, z0), (0.122, z0 + h * 0.15), (0.13, z0 + h * 0.5),
            (0.128, z0 + h * 0.8), (0.105, z1 - 0.008), (0.06, z1), (0.0, z1 + 0.004)]
    lathe(k[mat], M, prof, seg=28, hint=hint_from_point((0, 0, (z0 + z1) / 2)))


def head(k, skin, eyes=True, z=HEAD_Z, r=HEAD_R):
    ellipsoid(k[skin], (0, 0, z), (r, r * 0.95, r * 0.97), seg=28, rings=16)
    capsule(k[skin], (0, 0, 0.45), (0, 0, z - r * 0.7), 0.05, seg=12)          # Hals
    if eyes:
        for s in (-1, 1):
            ellipsoid(k["M_DustCap"], (s * 0.052, -r * 0.9, z + 0.012), (0.019, 0.012, 0.026), seg=12, rings=6)


def arm(k, side, elbow, hand, sleeve="M_Accent", skin="M_Skin1", r=0.036, wide=1.0, hand_r=0.04):
    sh = (side * 0.128 * wide, 0.0, SH_Z)
    limb(k[sleeve], [sh, elbow], r)
    limb(k[sleeve], [elbow, hand], r * 0.92)
    ellipsoid(k[skin], hand, hand_r, seg=14, rings=8)


def shades(k, z=HEAD_Z + 0.02, r=HEAD_R):
    M = frame_matrix((0, -r * 0.88, z), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    rounded_box(k["M_DustCap"], M, (0.105, 0.022, 0.03), 0.018, seg=2)
    for s in (-1, 1):                                     # Buegel
        tube(k["M_DustCap"], (s * 0.103, -r * 0.82, z + 0.01), (s * 0.142, -0.02, z + 0.01), 0.006, seg=6)


# ---------------------------------------------------------------------------
# Figuren
# ---------------------------------------------------------------------------
def fig_raver(k):
    legs(k)
    torso(k)
    head(k, "M_Skin1", eyes=False)
    shades(k)
    # Kapuze hinten, Kordeln vorne
    ellipsoid(k["M_Accent"], (0, 0.085, 0.50), (0.125, 0.07, 0.065), seg=20, rings=10)
    for s in (-1, 1):
        tube(k["M_White"], (s * 0.035, -0.098, 0.455), (s * 0.04, -0.104, 0.37), 0.006, seg=6, caps=True)
    # Fischerhut
    hat = [(0.0, 0.786), (0.105, 0.781), (0.135, 0.735), (0.15, 0.700), (0.215, 0.672),
           (0.212, 0.660), (0.14, 0.680), (0.0, 0.700)]
    lathe(k["M_Cloth"], frame_matrix((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), hat, seg=32,
          hint=hint_from_point((0, 0, 0.72)))
    # rechter Arm hoch mit Leuchtstab, linker locker unten
    arm(k, 1, (0.205, -0.02, 0.55), (0.19, -0.035, 0.675))
    tube(k["M_Glow"], (0.19, -0.035, 0.63), (0.205, -0.045, 0.83), 0.013, seg=10, caps=True)
    arm(k, -1, (-0.165, 0.0, 0.325), (-0.168, -0.03, 0.235))


def fig_dj(k):
    legs(k)
    torso(k)
    head(k, "M_Skin2")
    # Kopfhoerer: Buegel ueber den Kopf, Muscheln an den Ohren
    pts = [(math.cos(t) * 0.168, 0.0, HEAD_Z + math.sin(t) * 0.168) for t in np.linspace(0.15, math.pi - 0.15, 14)]
    for a, b in zip(pts[:-1], pts[1:]):
        tube(k["M_Plastic"], a, b, 0.012, seg=8)
    for s in (-1, 1):
        M = frame_matrix((s * 0.145, 0, HEAD_Z), (0, 1, 0), (0, 0, 1), (s, 0, 0))
        cylinder(k["M_Rubber"], M, 0.058, 0.0, 0.038, seg=20)
        cylinder(k["M_Accent"], M, 0.04, 0.038, 0.044, seg=20)
    # Cap verkehrt herum
    cap = [(0.0, 0.775), (0.09, 0.77), (0.135, 0.735), (0.152, 0.69), (0.148, 0.68), (0.0, 0.70)]
    lathe(k["M_Cloth"], frame_matrix((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), cap, seg=28,
          hint=hint_from_point((0, 0, 0.72)))
    rounded_box(k["M_Cloth"], frame_matrix((0, 0.17, 0.688), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.075, 0.06, 0.008), 0.007, seg=1)
    # rechte Hand am Kopfhoerer, linke Hand vorne am Mixer
    arm(k, 1, (0.245, 0.0, 0.455), (0.2, -0.01, 0.585), skin="M_Skin2")
    arm(k, -1, (-0.17, -0.07, 0.33), (-0.11, -0.17, 0.37), skin="M_Skin2")


def fig_tuersteher(k):
    W = 1.28
    legs(k, shoe="M_Rubber", spread=0.07, boots=True)
    torso(k, "M_Cloth", wide=W, z0=0.20, z1=0.48)
    head(k, "M_Skin3", eyes=False, z=HEAD_Z + 0.01)
    shades(k, z=HEAD_Z + 0.03)
    # Muetze in Spielerfarbe
    beanie = [(0.0, 0.783), (0.1, 0.775), (0.142, 0.735), (0.153, 0.672), (0.0, 0.672)]
    lathe(k["M_Accent"], frame_matrix((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), beanie, seg=28,
          hint=hint_from_point((0, 0, 0.72)))
    # Brustband in Spielerfarbe
    lathe(k["M_Accent"], frame_matrix((0, 0, 0), (W * 1.02, 0, 0), (0, 0.8, 0), (0, 0, 1)),
          [(0.0, 0.343), (0.131, 0.343), (0.134, 0.37), (0.131, 0.397), (0.0, 0.397)], seg=28,
          hint=lambda c: np.array([c[0], c[1], c[2] - 0.37]))
    # Arme verschraenkt
    arm(k, 1, (0.17, -0.11, 0.33), (-0.07, -0.16, 0.36), sleeve="M_Cloth", skin="M_Skin3", r=0.043, wide=W, hand_r=0.044)
    arm(k, -1, (-0.17, -0.10, 0.355), (0.07, -0.15, 0.39), sleeve="M_Cloth", skin="M_Skin3", r=0.043, wide=W, hand_r=0.044)
    # Funk-Ohrstoepsel mit Spiralkabel
    tube(k["M_Plastic"], (0.15, 0.02, 0.615), (0.135, 0.07, 0.47), 0.006, seg=6)


def fig_aal(k):
    # Koerper: Spirale am Boden, dann S-Kurve nach oben zum Kopf
    pts, radii = [], []
    for t in np.linspace(0, 1.6 * math.pi, 26):              # Schwanzspirale
        r = 0.06 + 0.09 * t / (1.6 * math.pi)
        pts.append((r * math.cos(t + 1.2), r * math.sin(t + 1.2), 0.05 + 0.012 * t))
        radii.append(0.016 + 0.042 * t / (1.6 * math.pi))
    last = np.array(pts[-1])
    for u in np.linspace(0.06, 1, 20):                       # S-Kurve hoch
        x = last[0] * (1 - u) + 0.03 * math.sin(u * math.pi * 1.6)
        y = last[1] * (1 - u) + 0.05 * math.sin(u * math.pi)
        pts.append((x, y, last[2] + u * 0.42))
        radii.append(0.058 + 0.02 * math.sin(u * math.pi * 0.9))
    sweep(k["M_Eel"], pts, radii, seg=18, cap_end=False)
    top = np.array(pts[-1])
    hc = top + np.array([0.0, -0.04, 0.1])
    ellipsoid(k["M_Eel"], hc, (0.13, 0.155, 0.12), seg=28, rings=14)   # Kopf, nach vorne laenglich
    # Mund (dunkler Schlitz) und grosse Augen
    lathe(k["M_DustCap"], frame_matrix(hc + np.array([0, -0.142, -0.04]), (1, 0, 0), (0, 0, 1), (0, -1, 0)),
          [(0.0, 0.0), (0.045, 0.0), (0.045, 0.006), (0.0, 0.006)], seg=16, hint=None)
    for s in (-1, 1):
        e = hc + np.array([s * 0.058, -0.105, 0.05])
        ellipsoid(k["M_White"], e, 0.046, seg=16, rings=10)
        ellipsoid(k["M_DustCap"], e + np.array([s * 0.004, -0.033, 0.004]), 0.021, seg=12, rings=8)
    # Sonnenbrille hochgeschoben
    rounded_box(k["M_DustCap"], frame_matrix(hc + np.array([0, -0.025, 0.118]), (1, 0, 0), (0, 0.6, 0.8), (0, -0.8, 0.6)),
                (0.09, 0.02, 0.024), 0.014, seg=2)
    # Flossen in Spielerfarbe: Rueckenkamm und zwei Brustflossen
    for i, u in enumerate(np.linspace(0.25, 0.85, 5)):
        j = int(26 + u * 19)
        p = np.array(pts[j]); r = radii[j]
        ellipsoid(k["M_Accent"], p + np.array([0, 0.75 * r, 0.0]), (0.01, 0.04, 0.035), seg=10, rings=6)
    ellipsoid(k["M_Accent"], hc + np.array([0, 0.035, 0.125]), (0.012, 0.07, 0.045), seg=12, rings=6)
    for s in (-1, 1):
        ellipsoid(k["M_Accent"], hc + np.array([s * 0.135, 0.03, -0.07]), (0.05, 0.028, 0.013),
                  seg=12, rings=6, axes=rot_y(s * 0.5))


def fig_robo(k):
    for s in (-1, 1):
        x = s * 0.062
        tube(k["M_Alu"], (x, 0, 0.05), (x, 0, 0.24), 0.026, seg=12)
        rounded_box(k["M_Plastic"], frame_matrix((x, -0.014, 0.03), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.05, 0.07, 0.03), 0.015, seg=2)
    rounded_box(k["M_Plastic"], frame_matrix((0, 0, 0.235), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.1, 0.07, 0.035), 0.02, seg=2)
    rounded_box(k["M_Accent"], frame_matrix((0, 0, 0.35), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.125, 0.09, 0.105), 0.035, seg=3)
    rounded_box(k["M_LED"], frame_matrix((0, -0.091, 0.37), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.05, 0.004, 0.03), 0.003, seg=1)
    tube(k["M_Alu"], (0, 0, 0.45), (0, 0, 0.5), 0.03, seg=12)
    rounded_box(k["M_Plastic"], frame_matrix((0, 0, 0.6), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.145, 0.12, 0.115), 0.045, seg=3)
    rounded_box(k["M_LED"], frame_matrix((0, -0.118, 0.615), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                (0.112, 0.01, 0.032), 0.009, seg=2)
    for s in (-1, 1):                                      # Ohren
        cylinder(k["M_Accent"], frame_matrix((s * 0.145, 0, 0.6), (0, 1, 0), (0, 0, 1), (s, 0, 0)),
                 0.04, 0.0, 0.025, seg=16)
    tube(k["M_Alu"], (0.05, 0, 0.71), (0.07, 0, 0.8), 0.007, seg=8)
    ellipsoid(k["M_Glow"], (0.07, 0, 0.81), 0.02, seg=12, rings=8)
    # Arme: rechts Faust hoch, links angewinkelt
    sh = SH_Z - 0.01
    limb(k["M_Alu"], [(0.13, 0, sh), (0.2, -0.02, 0.52), (0.18, -0.03, 0.65)], 0.024)
    ellipsoid(k["M_Plastic"], (0.18, -0.03, 0.665), 0.042, seg=14, rings=8)
    limb(k["M_Alu"], [(-0.13, 0, sh), (-0.18, -0.02, 0.32), (-0.13, -0.11, 0.3)], 0.024)
    ellipsoid(k["M_Plastic"], (-0.13, -0.12, 0.3), 0.042, seg=14, rings=8)
    for s in (-1, 1):
        ellipsoid(k["M_Accent"], (s * 0.13, 0, sh), 0.04, seg=14, rings=8)


def fig_gasmaske(k):
    legs(k, boots=True)
    torso(k)
    head(k, "M_Skin2", eyes=False)
    # Maske: Gummi-Gesichtsteil, Glasaugen, Filter
    ellipsoid(k["M_Rubber"], (0, -0.075, HEAD_Z - 0.01), (0.13, 0.095, 0.125), seg=24, rings=12)
    for s in (-1, 1):
        M = frame_matrix((s * 0.052, -0.155, HEAD_Z + 0.03), (1, 0, 0), (0, 0, 1), (0, -1, 0))
        cylinder(k["M_Steel"], M, 0.036, 0.0, 0.012, seg=18)
        cylinder(k["M_DustCap"], M, 0.03, 0.012, 0.016, seg=18)
    Mf = frame_matrix((0, -0.165, HEAD_Z - 0.065), (1, 0, 0), (0, 0.45, 0.89), (0, -0.89, 0.45))
    cylinder(k["M_Rubber"], Mf, 0.032, 0.0, 0.03, seg=16)
    cylinder(k["M_Steel"], Mf, 0.045, 0.03, 0.085, seg=18)
    for s in (-1, 1):                                       # Riemen
        tube(k["M_Rubber"], (s * 0.12, -0.05, HEAD_Z + 0.03), (s * 0.15, 0.04, HEAD_Z + 0.04), 0.01, seg=6)
    # Irokese in Spielerfarbe
    for i, a in enumerate(np.linspace(-0.5, 1.9, 7)):
        y = -HEAD_R * math.cos(a + 0.6) * 0.95
        z = HEAD_Z + HEAD_R * math.sin(a + 0.6) * 0.95
        ellipsoid(k["M_Accent"], (0, y, z + 0.02), (0.014, 0.03, 0.05 - abs(a - 0.7) * 0.012),
                  seg=10, rings=6, axes=rot_x(-(a + 0.6 - math.pi / 2)))
    # Arme beide hoch, Haende offen
    arm(k, 1, (0.2, -0.01, 0.54), (0.215, -0.02, 0.69), skin="M_Skin2")
    arm(k, -1, (-0.2, -0.01, 0.54), (-0.215, -0.02, 0.69), skin="M_Skin2")


FIGS = {"raver": fig_raver, "dj": fig_dj, "tuersteher": fig_tuersteher, "aal": fig_aal,
        "robo": fig_robo, "gasmaske": fig_gasmaske}


def make(kind):
    k = Kit("FIG_" + kind)
    FIGS[kind](k)
    ground(k.list())
    return {
        "name": "FIG_" + kind.upper(),
        "cabinet": None, "cutters": [],
        "parts": k.list(),
        "bevel": 0.0,
        "dims": {"height": 0.8},
        "shots": {
            "front34": ((-0.95, -1.75, 0.95), (0, 0, 0.40)),
        },
    }


# ---------------------------------------------------------------------------
# Tanzende Menge: eine Figur in zwei Posen, sehr wenige Dreiecke (Thin Instances)
# ---------------------------------------------------------------------------
def crowd_pose(k, pose):
    S = 10  # Segmente
    for s in (-1, 1):
        x = s * 0.06
        capsule(k["M_Crowd"], (x, 0, 0.05), (x + s * 0.01, 0, 0.24), 0.045, seg=S)
    M = frame_matrix((0, 0, 0), (1, 0, 0), (0, 0.78, 0), (0, 0, 1))
    lathe(k["M_Crowd"], M, [(0.0, 0.2), (0.105, 0.2), (0.13, 0.33), (0.115, 0.46), (0.0, 0.47)], seg=S,
          hint=hint_from_point((0, 0, 0.33)))
    ellipsoid(k["M_Crowd"], (0, 0, 0.6), 0.135, seg=S + 2, rings=7)
    if pose == "A":            # beide Arme hoch, Leuchtstab
        for s in (-1, 1):
            limb(k["M_Crowd"], [(s * 0.12, 0, 0.42), (s * 0.2, -0.02, 0.56), (s * 0.17, -0.02, 0.71)], 0.034, seg=8)
        tube(k["M_Glow"], (0.17, -0.02, 0.69), (0.19, -0.03, 0.86), 0.012, seg=6, caps=True)
    else:                      # ein Arm hoch zeigend, einer angewinkelt
        limb(k["M_Crowd"], [(0.12, 0, 0.42), (0.17, -0.06, 0.55), (0.15, -0.14, 0.68)], 0.034, seg=8)
        limb(k["M_Crowd"], [(-0.12, 0, 0.42), (-0.17, 0, 0.32), (-0.1, -0.1, 0.33)], 0.034, seg=8)


def make_crowd():
    parts = []
    for pose in ("A", "B"):
        k = Kit("CROWD_" + pose, group="Crowd" + pose)
        crowd_pose(k, pose)
        parts += k.list()
    ground(parts)
    return {
        "name": "CROWD",
        "cabinet": None, "cutters": [],
        "parts": parts,
        "groups": {"CrowdA": {"parent": None, "origin": (0.0, 0.0, 0.0)},
                   "CrowdB": {"parent": None, "origin": (0.0, 0.0, 0.0)}},
        "bevel": 0.0,
        "dims": {"height": 0.86},
        "shots": {"front34": ((-0.95, -1.75, 0.95), (0, 0, 0.42))},
    }


def ground(parts):
    """Ursprung = Fussunterseite: tiefster Punkt auf z = 0."""
    zmin = min(np.array(p.verts)[:, 2].min() for p in parts)
    for p in parts:
        p.verts = [v - np.array([0.0, 0.0, zmin]) for v in p.verts]


def stats(spec):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    tot = 0
    for p in spec["parts"]:
        v = np.array(p.verts)
        lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        tot += p.triangle_count()
    return tot, (hi - lo)[[0, 2, 1]], lo, hi


if __name__ == "__main__":
    for kind in KINDS:
        s = make(kind)
        tot, size, lo, hi = stats(s)
        print(f"{kind:11s} {tot:6d} Dreiecke  {len(s['parts'])} Meshes  glTF {size.round(3)}  minz {lo[2]:.3f}")
    s = make_crowd()
    tot, size, lo, hi = stats(s)
    print(f"{'crowd':11s} {tot:6d} Dreiecke  {len(s['parts'])} Meshes  glTF {size.round(3)}  minz {lo[2]:.3f}")
