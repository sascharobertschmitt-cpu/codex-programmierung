"""
Ueberspitzte Club-Charaktere fuer "Aal You Ready?" (eigenes Design, keine Marken).

Stil: Karikatur. Kleiner Kopf mit markantem Gesicht (grosse Nase, Kinn, Brauen),
breite Schultern, schmale Huefte, duenne lange Beine, grosse Haende und Sneaker.
Ein Koerper fuer alle Spieler; unterscheiden tun sich die Figuren ueber
Spielerfarbe (M_Accent) und eine waehlbare Kopfbedeckung (club_hats.glb).

Masse: Blender-Meter, Z oben, Front -Y, Ursprung Mitte Fussunterseite, Hoehe ca. 0.9.
Kopfmitte liegt bei HEAD (Huete sind in denselben Koordinaten modelliert).
"""
import math

import numpy as np

from assetlib import Part, cylinder, frame_matrix, hint_from_point, lathe, rounded_box, superellipse, tube
from figures_geometry import Kit, capsule, ellipsoid, ground, limb, rot_x, rot_y, rot_z

LOW = {"on": False}               # Menge: weniger Segmente


def E(part, c, r, seg=20, rings=12, axes=None):
    if LOW["on"]:
        seg, rings = max(6, seg // 2), max(4, rings // 2)
    ellipsoid(part, c, r, seg=seg, rings=rings, axes=axes)


def Lm(part, pts, r, seg=14):
    if not LOW["on"]:
        return limb(part, pts, r, seg)
    for a, b in zip(pts[:-1], pts[1:]):
        tube(part, a, b, r, seg=6)
        E(part, b, r, seg=8, rings=4)


HEAD = np.array([0.0, 0.0, 0.775])
HR = 0.082                       # Kopfradius (Breite)
HATS = ("fischerhut", "cap", "kopfhoerer", "beanie", "gasmaske", "aalmuetze", "hasenohren", "ledhelm")


def loft(part, sections, seg=24, n=2.6, cap=True):
    """Koerper aus Superellipsen-Querschnitten: sections = [(z, rx, ry, dy), ...]."""
    rings = []
    for z, rx, ry, dy in sections:
        x, y = superellipse(rx, ry, n, seg)
        rings.append(np.stack([x, y + dy, np.full(seg, z)], -1))
    if cap:
        z0, _, _, dy0 = sections[0]
        z1, _, _, dy1 = sections[-1]
        rings.insert(0, np.array([[0.0, dy0, z0 - 0.004]]))
        rings.append(np.array([[0.0, dy1, z1 + 0.004]]))
    zc = np.mean([s[0] for s in sections])
    part.grid(rings, closed=True, smooth=True, hint=lambda c: np.array([c[0], c[1], (c[2] - zc) * 0.3]))


# ---------------------------------------------------------------------------
# Koerper
# ---------------------------------------------------------------------------
def body(k, skin="M_Skin1", pose="stand", top="M_Accent", pants="M_Cloth", hair="M_HairDark", seg=1.0):
    S = lambda v: max(6, int(v * seg))
    # Sneaker: gross, klobig, weisse Sohle
    for s in (-1, 1):
        x = s * (0.058 if s < 0 else 0.075)
        rounded_box(k["M_Accent"] if seg >= 1 else k[top], frame_matrix((x, -0.03, 0.038), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.052, 0.098, 0.03), 0.022, seg=2)
        rounded_box(k["M_White"], frame_matrix((x, -0.032, 0.01), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.056, 0.104, 0.01), 0.008, seg=1)
        # duenne lange Beine (Hose), leicht nach unten verjuengt
        tube(k[pants], (x, 0.0, 0.05), (s * 0.05, 0.0, 0.36), 0.029, seg=S(12))
        E(k[pants], ((x + s * 0.05) / 2, -0.004, 0.2), (0.034, 0.034, 0.05), seg=S(12), rings=6)   # Knie
        E(k[pants], (x, 0.0, 0.055), (0.032, 0.032, 0.02), seg=S(12), rings=6)
    # Huefte
    E(k[pants], (0, 0.0, 0.37), (0.088, 0.058, 0.048), seg=S(18), rings=8)
    # Oberkoerper: schmale Taille, breite Brust und Schultern (V-Form), leichter Bauch nach vorn
    loft(k[top], [(0.36, 0.08, 0.056, 0.0), (0.41, 0.078, 0.058, -0.004), (0.49, 0.13, 0.074, -0.012),
                  (0.56, 0.178, 0.082, -0.01), (0.61, 0.19, 0.072, 0.0), (0.64, 0.14, 0.056, 0.006),
                  (0.66, 0.05, 0.04, 0.008)], seg=S(28))
    # Kordeln / Reissverschluss-Streifen vorne
    if seg >= 1:
        tube(k["M_White"], (0.0, -0.074, 0.40), (0.0, -0.088, 0.6), 0.006, seg=6)
    # Hals und Kopf
    tube(k[skin], (0, 0.008, 0.64), (0, 0.004, 0.72), 0.03, seg=S(12))
    head(k, skin, hair, seg)
    # Arme (lang) mit grossen Haenden
    arms(k, pose, top, skin, seg)


def head(k, skin, hair, seg=1.0):
    S = lambda v: max(6, int(v * seg))
    hx, hy, hz = HEAD
    E(k[skin], HEAD + [0, 0.004, 0.012], (HR, HR * 1.08, HR * 1.2), seg=S(26), rings=S(14))   # Schaedel, hoch
    E(k[skin], HEAD + [0, -0.034, -0.06], (0.066, 0.054, 0.046), seg=S(18), rings=S(8))       # Kinn/Kiefer vor
    E(k[skin], HEAD + [0, -0.096, -0.004], (0.024, 0.04, 0.03), seg=S(14), rings=S(8),     # Nase, gross
              axes=rot_x(-0.35))
    for s in (-1, 1):
        E(k[skin], HEAD + [s * 0.082, 0.004, 0.0], (0.012, 0.022, 0.03), seg=S(10), rings=6)   # Ohren
        if seg >= 1:
            e = HEAD + [s * 0.033, -0.072, 0.03]
            E(k["M_White"], e, (0.019, 0.012, 0.016), seg=12, rings=6)
            E(k["M_DustCap"], e + [s * 0.002, -0.009, -0.002], (0.008, 0.006, 0.009), seg=10, rings=5)
            # dicke Augenbrauen, leicht schraeg (verschmitzt)
            tube(k[hair], e + [-s * 0.017, -0.006, 0.026 - 0.004 * s], e + [s * 0.018, -0.004, 0.03 + 0.004 * s], 0.0065, seg=6, caps=True)
    if seg >= 1:
        # schiefes Grinsen
        pts = [HEAD + [math.sin(t) * 0.03, -0.083 + abs(math.sin(t)) * 0.012, -0.045 + 0.012 * math.sin(t) ** 2 + 0.006 * math.sin(t)]
               for t in np.linspace(-1.1, 1.2, 7)]
        for a, b in zip(pts[:-1], pts[1:]):
            tube(k["M_DustCap"], a, b, 0.005, seg=6)
    # kurze Haare (unter Huete), etwas hinten und oben
    E(k[hair], HEAD + [0, 0.014, 0.04], (HR * 1.04, HR * 1.06, HR * 0.95), seg=S(22), rings=S(10))


def arms(k, pose, top, skin, seg=1.0):
    S = lambda v: max(6, int(v * seg))
    for s in (-1, 1):
        sh = np.array([s * 0.19, 0.0, 0.6])
        if pose == "stand":
            el = sh + [s * 0.045, 0.02, -0.15]
            ha = el + [s * 0.005, -0.045, -0.14]
        elif pose == "up":                    # beide Haende hoch
            el = sh + [s * 0.08, -0.01, 0.12]
            ha = el + [-s * 0.02, -0.02, 0.15]
        elif pose == "one":                   # rechts hoch zeigen, links angewinkelt
            if s > 0:
                el = sh + [0.06, -0.06, 0.12]
                ha = el + [-0.01, -0.08, 0.13]
            else:
                el = sh + [-0.05, 0.0, -0.14]
                ha = el + [0.06, -0.11, 0.02]
        else:                                 # "swag": Haende in die Hueften
            el = sh + [s * 0.1, 0.03, -0.12]
            ha = np.array([s * 0.1, -0.01, 0.4])
        E(k[top], sh + [-s * 0.012, 0, 0.006], (0.05, 0.05, 0.042), seg=S(14), rings=7)   # Schulter
        Lm(k[top], [sh, el], 0.031, seg=S(12))
        Lm(k[skin], [el, ha], 0.026, seg=S(12))
        # grosse Hand: Faustballen + Daumen
        d = ha - el; d /= np.linalg.norm(d)
        hand = ha + d * 0.035
        E(k[skin], hand, (0.044, 0.034, 0.054), seg=S(14), rings=7)
        E(k[skin], hand + [-s * 0.036, -0.018, 0.016], (0.016, 0.016, 0.026), seg=S(10), rings=5)


# ---------------------------------------------------------------------------
# Kopfbedeckungen (in Koerperkoordinaten, Kopfmitte = HEAD)
# ---------------------------------------------------------------------------
def hat(k, kind):
    H = HEAD
    top = H[2] + HR * 1.2 + 0.012               # Scheitel
    M0 = frame_matrix((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    if kind == "fischerhut":
        prof = [(0.0, top + 0.035), (0.075, top + 0.03), (0.092, top - 0.035), (0.098, top - 0.06),
                (0.15, top - 0.085), (0.148, top - 0.095), (0.09, top - 0.075), (0.0, top - 0.07)]
        lathe(k["M_Accent"], M0, prof, seg=32, hint=hint_from_point((0, 0, top - 0.03)))
        lathe(k["M_Cloth"], M0, [(0.0, top - 0.054), (0.0935, top - 0.054), (0.0955, top - 0.04), (0.0, top - 0.04)], seg=32,
              hint=lambda c: np.array([c[0], c[1], 0.0]))
    elif kind == "cap":                          # verkehrt herum, Schirm hinten
        prof = [(0.0, top + 0.012), (0.06, top + 0.006), (0.088, top - 0.03), (0.092, top - 0.06), (0.0, top - 0.06)]
        lathe(k["M_Accent"], M0, prof, seg=28, hint=hint_from_point((0, 0, top - 0.03)))
        rounded_box(k["M_Accent"], frame_matrix((0, 0.115, top - 0.055), (1, 0, 0), (0, 0.97, -0.24), (0, 0.24, 0.97)),
                    (0.06, 0.055, 0.006), 0.005, seg=1)
        ellipsoid(k["M_White"], (0, 0, top + 0.01), 0.011, seg=10, rings=5)
    elif kind == "kopfhoerer":
        pts = [(math.cos(t) * 0.1, 0.0, H[2] + 0.01 + math.sin(t) * 0.112) for t in np.linspace(0.12, math.pi - 0.12, 14)]
        for a, b in zip(pts[:-1], pts[1:]):
            tube(k["M_Accent"], a, b, 0.011, seg=8)
        for s in (-1, 1):
            Mc = frame_matrix((s * 0.084, 0, H[2] + 0.0), (0, 1, 0), (0, 0, 1), (s, 0, 0))
            cylinder(k["M_Rubber"], Mc, 0.045, 0.0, 0.03, seg=20)
            cylinder(k["M_Accent"], Mc, 0.032, 0.03, 0.036, seg=20)
    elif kind == "beanie":
        prof = [(0.0, top + 0.03), (0.06, top + 0.02), (0.088, top - 0.02), (0.094, top - 0.065), (0.098, top - 0.07),
                (0.098, top - 0.095), (0.0, top - 0.095)]
        lathe(k["M_Accent"], M0, prof, seg=28, hint=hint_from_point((0, 0, top - 0.04)))
        ellipsoid(k["M_Accent"], (0, 0, top + 0.04), 0.024, seg=12, rings=6)       # Bommel
    elif kind == "gasmaske":
        c = H + [0, -0.06, -0.025]
        ellipsoid(k["M_Rubber"], c, (0.072, 0.055, 0.07), seg=22, rings=10)
        for s in (-1, 1):
            Me = frame_matrix(H + [s * 0.032, -0.104, 0.028], (1, 0, 0), (0, 0, 1), (0, -1, 0))
            cylinder(k["M_Steel"], Me, 0.022, 0.0, 0.008, seg=16)
            cylinder(k["M_DustCap"], Me, 0.018, 0.008, 0.011, seg=16)
        Mf = frame_matrix(H + [0, -0.11, -0.055], (1, 0, 0), (0, 0.5, 0.87), (0, -0.87, 0.5))
        cylinder(k["M_Accent"], Mf, 0.03, 0.0, 0.05, seg=18)
        for s in (-1, 1):
            tube(k["M_Rubber"], H + [s * 0.07, -0.03, 0.03], H + [s * 0.085, 0.05, 0.035], 0.008, seg=6)
    elif kind == "aalmuetze":                    # ein Aal ringelt sich um den Kopf
        pts, rad = [], []
        for t in np.linspace(0, 2.15 * math.pi, 40):
            r = 0.094 - 0.012 * t / (2.15 * math.pi)
            pts.append((r * math.cos(t - 1.2), r * math.sin(t - 1.2), top - 0.075 + 0.04 * t / (2.15 * math.pi)))
            rad.append(0.01 + 0.012 * math.sin(min(1.0, t / 5.5) * math.pi * 0.95))
        from figures_geometry import sweep
        sweep(k["M_Eel"], pts, rad, seg=12)
        hd = np.array(pts[-1]) + np.array([0.0, -0.012, 0.022])
        ellipsoid(k["M_Eel"], hd, (0.028, 0.036, 0.026), seg=14, rings=8)
        for s in (-1, 1):
            e = hd + [s * 0.016, -0.02, 0.014]
            ellipsoid(k["M_White"], e, 0.011, seg=10, rings=5)
            ellipsoid(k["M_DustCap"], e + [0, -0.008, 0], 0.005, seg=8, rings=4)
        ellipsoid(k["M_Accent"], hd + [0, 0.02, 0.028], (0.005, 0.022, 0.014), seg=8, rings=4)
    elif kind == "hasenohren":
        # Haarreif
        pts = [(math.cos(t) * 0.092, 0.012, H[2] + 0.02 + math.sin(t) * 0.108) for t in np.linspace(0.2, math.pi - 0.2, 12)]
        for a, b in zip(pts[:-1], pts[1:]):
            tube(k["M_Accent"], a, b, 0.008, seg=6)
        for s in (-1, 1):
            base = np.array([s * 0.04, 0.0, top - 0.01])
            ax = rot_y(s * 0.28) @ rot_x(0.12)
            ellipsoid(k["M_Accent"], base + ax @ [0, 0, 0.075], (0.024, 0.012, 0.08), seg=14, rings=8, axes=ax)
            ellipsoid(k["M_White"], base + ax @ [0, -0.008, 0.075], (0.014, 0.006, 0.062), seg=12, rings=6, axes=ax)
    elif kind == "ledhelm":                      # Helm mit LED-Visier (generisch)
        ellipsoid(k["M_Plastic"], H + [0, 0.006, 0.014], (HR * 1.22, HR * 1.28, HR * 1.42), seg=28, rings=14)
        Mv = frame_matrix(H + [0, -0.088, 0.012], (1, 0, 0), (0, 1, 0), (0, 0, 1))
        rounded_box(k["M_LED"], Mv, (0.07, 0.012, 0.022), 0.01, seg=2)
        tube(k["M_Accent"], H + [0, -0.04, top + 0.0], H + [0, 0.07, top - 0.03], 0.01, seg=8, caps=True)
    else:
        raise ValueError(kind)


# ---------------------------------------------------------------------------
# Spezifikationen fuer build_asset.py
# ---------------------------------------------------------------------------
def make_character():
    k = Kit("CHAR")
    body(k, pose="stand")
    parts = k.list()
    ground(parts)
    return {"name": "CHAR", "cabinet": None, "cutters": [], "parts": parts, "bevel": 0.0,
            "dims": {"height": 0.9},
            "shots": {"front34": ((-0.95, -1.75, 0.95), (0, 0, 0.45))}}


def make_hats(names=HATS, tag="HATS"):
    """Kopfbedeckungen in einer GLB, je Hut eine Gruppe HAT_<name> mit Ursprung 0."""
    parts, groups = [], {}
    for name in names:
        k = Kit("HAT_" + name, group="HAT_" + name)
        hat(k, name)
        parts += k.list()
        groups["HAT_" + name] = {"parent": None, "origin": (0.0, 0.0, 0.0)}
    return {"name": tag, "cabinet": None, "cutters": [], "parts": parts, "groups": groups, "bevel": 0.0,
            "dims": {"height": 0.3},
            "shots": {"front34": ((-0.55, -0.95, 1.2), (0, 0, 0.8))}}


# Club-Gaeste: 6 Varianten, Farben als Vertex-Farben (M_Crowd), je eine Gruppe CrowdV<i>
CROWD = [  # Pose, Shirt, Hose, Haut, Haare, Kopfbedeckung
    ("up",    (0.55, 0.08, 0.85), (0.03, 0.03, 0.04), (0.73, 0.41, 0.27), (0.02, 0.012, 0.008), "cap"),
    ("one",   (0.04, 0.45, 0.85), (0.10, 0.10, 0.12), (0.35, 0.155, 0.074), (0.01, 0.008, 0.006), None),
    ("swag",  (0.02, 0.02, 0.025), (0.05, 0.08, 0.20), (0.106, 0.043, 0.022), (0.01, 0.008, 0.006), "beanie"),
    ("up",    (0.85, 0.12, 0.45), (0.03, 0.03, 0.04), (0.60, 0.33, 0.20), (0.45, 0.25, 0.08), None),
    ("one",   (0.10, 0.70, 0.45), (0.04, 0.04, 0.05), (0.73, 0.41, 0.27), (0.20, 0.06, 0.03), "fischerhut"),
    ("stand", (0.90, 0.55, 0.10), (0.03, 0.03, 0.04), (0.35, 0.155, 0.074), (0.01, 0.008, 0.006), "kopfhoerer"),
]


def make_crowd2():
    parts = []
    for i, (pose, shirt, pants, skin, hair, hat_kind) in enumerate(CROWD):
        k = Kit(f"CROWD_V{i}")
        LOW["on"] = True
        body(k, pose=pose, seg=0.5)
        LOW["on"] = False
        if hat_kind:
            hat(k, hat_kind)
        if pose == "up":
            hand = np.array([0.19 + 0.08 - 0.02, -0.03, 0.6 + 0.12 + 0.15 + 0.035])
            tube(k["M_Glow"], hand + [0, -0.01, 0.0], hand + [0.01, -0.02, 0.16], 0.01, seg=6, caps=True)
        cols = {"M_Accent": shirt, "M_Cloth": pants, "M_Skin1": skin, "M_HairDark": hair, "M_White": (0.7, 0.7, 0.7),
                "M_DustCap": (0.01, 0.01, 0.01), "M_Rubber": (0.015, 0.015, 0.015), "M_Glow": (1.0, 0.25, 0.75),
                "M_Steel": (0.5, 0.5, 0.5), "M_Plastic": (0.05, 0.05, 0.06), "M_LED": (0.2, 0.8, 1.0), "M_Eel": (0.04, 0.1, 0.06)}
        merged = Part(f"CROWD_V{i}_Body", "M_Crowd")
        merged.colors = []
        merged.group = f"CrowdV{i}"
        for p in k.list():
            n0 = len(merged.verts)
            merged.extend(p)
            merged.colors += [cols[p.material]] * (len(merged.verts) - n0)
        parts.append(merged)
    ground(parts)
    return {"name": "CROWD", "cabinet": None, "cutters": [], "parts": parts,
            "groups": {f"CrowdV{i}": {"parent": None, "origin": (0.0, 0.0, 0.0)} for i in range(len(CROWD))},
            "bevel": 0.0, "dims": {"height": 1.0},
            "shots": {"front34": ((-0.95, -1.75, 0.95), (0, 0, 0.45))}}


if __name__ == "__main__":
    from figures_geometry import stats
    for name, s in (("character", make_character()), ("hats", make_hats()), ("crowd", make_crowd2())):
        tot, size, lo, hi = stats(s)
        print(f"{name:10s} {tot:6d} Dreiecke  {len(s['parts'])} Meshes  glTF {size.round(3)}  minz {lo[2]:.3f}")
