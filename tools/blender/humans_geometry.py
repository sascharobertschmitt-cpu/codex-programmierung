"""
Realistischere Menschen fuer "Aal You Ready?" (eigenes Design, prozedural, keine Marken).

Proportionen ca. 7,5 Kopflaengen, Koerper aus Querschnitt-Sweeps (Rumpf, Glieder),
Kopf aus Schaedel + Kiefer + Nase + Ohren, Frisuren und Kleidung als eigene Materialien.
Masse in Metern (Blender: Z oben, Front -Y), Ursprung Mitte zwischen den Fuessen.
"""
import math

import numpy as np

from assetlib import frame_matrix, hint_from_point, lathe, rounded_box, tube
from figures_geometry import Kit, capsule, ellipsoid, ground, rot_x, rot_y, rot_z


# ---------------------------------------------------------------------------
# Werkzeuge
# ---------------------------------------------------------------------------
def sweep_ell(part, pts, rx, ry, ref=(1.0, 0.0, 0.0), seg=20, n=2.0, cap0=True, cap1=True, yoff=None):
    """Schlauch mit elliptischem (Super-)Querschnitt. ref legt die Breitenachse fest."""
    pts = [np.asarray(p, float) for p in pts]
    k = len(pts)
    ref = np.asarray(ref, float)
    tang = []
    for i in range(k):
        d = pts[min(i + 1, k - 1)] - pts[max(i - 1, 0)]
        tang.append(d / np.linalg.norm(d))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    c, s = np.cos(a), np.sin(a)
    cx = np.sign(c) * np.abs(c) ** (2.0 / n)
    sy = np.sign(s) * np.abs(s) ** (2.0 / n)
    rings, centers = [], []
    for i, p in enumerate(pts):
        t = tang[i]
        x = ref - t * np.dot(ref, t)
        x /= np.linalg.norm(x)
        y = np.cross(t, x)
        off = 0.0 if yoff is None else yoff[i]
        ctr = p + y * off
        centers.append(ctr)
        rings.append([ctr + rx[i] * cx[j] * x + ry[i] * sy[j] * y for j in range(seg)])
    if cap0:
        rings.insert(0, [centers[0] - tang[0] * min(rx[0], ry[0]) * 0.35])
    if cap1:
        rings.append([centers[-1] + tang[-1] * min(rx[-1], ry[-1]) * 0.35])
    allc = centers

    def hint(q):
        d = [np.linalg.norm(q - cc) for cc in allc]
        return q - allc[int(np.argmin(d))]
    part.grid(rings, closed=True, smooth=True, hint=hint)


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def chain(a, b, c, n1=4, n2=4):
    """Punkte entlang Schulter-Ellbogen-Hand (bzw. Huefte-Knie-Knoechel)."""
    out = [lerp(a, b, t) for t in np.linspace(0, 1, n1, endpoint=False)]
    out += [lerp(b, c, t) for t in np.linspace(0, 1, n2 + 1)]
    return out


def look_axes(direction, up=(0.0, 0.0, 1.0)):
    """3x3-Matrix: Spalten = (quer, dicke, laengs) fuer ein Ellipsoid entlang direction."""
    z = np.asarray(direction, float)
    z /= np.linalg.norm(z)
    u = np.asarray(up, float)
    if abs(np.dot(u, z)) > 0.95:
        u = np.array([0.0, -1.0, 0.0])
    x = np.cross(u, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)


# ---------------------------------------------------------------------------
# Koerperbau
# ---------------------------------------------------------------------------
class Body:
    def __init__(self, sex="m", build=1.0, height=1.0):
        self.sex = sex
        self.b = build          # Breite (Tuersteher ~1.25)
        self.h = height         # Gesamtskalierung Hoehe
        H = height
        self.hip_z = 0.92 * H
        self.sh_z = 1.42 * H
        self.sh_x = (0.185 if sex == "m" else 0.165) * build
        self.head_c = np.array([0.0, 0.004, 1.64 * H])
        self.hip_x = (0.088 if sex == "m" else 0.095) * build

    def S(self, v):
        return v * self.h


def torso(k, B, shirt="M_Accent", pants="M_Cloth", top_style="tee", seg=22):
    H, b = B.h, B.b
    f = B.sex == "f"
    # z, Breite, Tiefe, Versatz nach hinten (Ruecken/Bauch)
    prof = [
        (0.84, 0.150, 0.100, 0.000),
        (0.92, 0.172 + (0.022 if f else 0), 0.112, 0.004),
        (1.00, 0.165 + (0.012 if f else 0), 0.106, 0.002),
        (1.07, 0.150 - (0.018 if f else 0), 0.098, -0.002),
        (1.15, 0.155 - (0.012 if f else 0), 0.103, -0.004),
        (1.26, 0.172 - (0.012 if f else 0), 0.115, -0.004),
        (1.35, 0.188 - (0.018 if f else 0), 0.112, 0.000),
        (1.41, 0.180 - (0.018 if f else 0), 0.098, 0.006),
        (1.455, 0.120, 0.075, 0.010),
        (1.48, 0.060, 0.050, 0.010),
    ]
    split = 1.00 if top_style != "crop" else 1.10
    low = [p for p in prof if p[0] <= split + 1e-6]
    high = [p for p in prof if p[0] >= split - 1e-6]
    for mat, rows, c0, c1 in ((pants, low, True, False), (shirt, high, False, True)):
        pts = [(0.0, r[3] * H, r[0] * H) for r in rows]
        sweep_ell(k[mat], pts, [r[1] * b * H for r in rows], [r[2] * b * H for r in rows],
                  seg=seg, n=2.3, cap0=c0, cap1=c1)
    if top_style == "crop":         # Bauch frei: Hautstueck zwischen Hose und Top
        rows = [p for p in prof if 0.99 <= p[0] <= 1.11]
        pts = [(0.0, r[3] * H, r[0] * H) for r in rows]
        sweep_ell(k[B.skin], pts, [r[1] * b * H * 0.985 for r in rows], [r[2] * b * H * 0.985 for r in rows],
                  seg=seg, n=2.3, cap0=False, cap1=False)
    if f:                            # Brust
        for s in (-1, 1):
            ellipsoid(k[shirt], (s * 0.062 * b * H, -0.085 * H, 1.255 * H), (0.058 * H, 0.05 * H, 0.052 * H), seg=14, rings=8)


def neck_head(k, B, hair=None, hair_mat="M_HairDark", beard=False, face=True):
    H = B.h
    hc = B.head_c
    sk = k[B.skin]
    capsule(sk, (0, 0.012 * H, 1.44 * H), (0, 0.004 * H, 1.585 * H), 0.05 * H, seg=14)
    f = 0.93 if B.sex == "f" else 1.0
    ellipsoid(sk, hc, (0.077 * H * f, 0.097 * H * f, 0.107 * H * f), seg=26, rings=16)            # Schaedel
    ellipsoid(sk, hc + np.array([0, -0.03, -0.062]) * H, (0.06 * H * f, 0.07 * H * f, 0.058 * H * f),
              seg=20, rings=10)                                                                  # Kiefer/Kinn
    if face:
        ellipsoid(sk, hc + np.array([0, -0.093, -0.012]) * H * f, (0.012 * H, 0.022 * H, 0.03 * H),
                  seg=10, rings=6, axes=rot_x(-0.25))                                            # Nase
        for s in (-1, 1):
            ellipsoid(sk, hc + np.array([s * 0.076 * f, 0.004, -0.004]) * H, (0.011 * H, 0.022 * H, 0.032 * H),
                      seg=10, rings=6)                                                           # Ohren
            ellipsoid(k["M_Eye"], hc + np.array([s * 0.032, -0.083, 0.012]) * H * f, (0.012 * H, 0.006 * H, 0.008 * H),
                      seg=10, rings=6)                                                           # Augen
            ellipsoid(k[hair_mat if hair != "bald" else B.skin], hc + np.array([s * 0.034, -0.086, 0.034]) * H * f,
                      (0.019 * H, 0.006 * H, 0.005 * H), seg=8, rings=4, axes=rot_y(s * 0.15))   # Brauen
        ellipsoid(k["M_Lips"], hc + np.array([0, -0.082, -0.058]) * H * f, (0.02 * H, 0.008 * H, 0.006 * H),
                  seg=10, rings=4)
    hm = k[hair_mat]
    if hair in ("short", "long", "bun", "ponytail", "mohawk_side"):
        # Haarkappe: Teilschale ueber dem Schaedel, hinten tiefer
        M = frame_matrix(hc + np.array([0, 0.006, 0.006]) * H, (0.083 * H * f, 0, 0), (0, 0.103 * H * f, 0), (0, 0, 0.113 * H * f))
        M[:3, :3] = M[:3, :3] @ rot_x(-0.35)
        prof = [(math.sin(t), math.cos(t)) for t in np.linspace(0, 1.75, 10)]
        prof = [(0.0, 1.0)] + prof[1:] + [(math.sin(1.75) * 0.9, math.cos(1.75) * 0.9), (0.0, 0.9)]
        lathe(hm, M, prof, seg=24, hint=hint_from_point(hc))
    if hair == "long":
        pts = [hc + np.array([0, 0.07, -0.02]) * H, hc + np.array([0, 0.085, -0.12]) * H, hc + np.array([0, 0.09, -0.25]) * H]
        sweep_ell(hm, pts, [0.075 * H, 0.08 * H, 0.07 * H], [0.035 * H, 0.03 * H, 0.02 * H], seg=14)
    if hair == "bun":
        ellipsoid(hm, hc + np.array([0, 0.06, 0.1]) * H, 0.045 * H, seg=14, rings=8)
    if hair == "ponytail":
        pts = [hc + np.array([0, 0.095, 0.03]) * H, hc + np.array([0, 0.13, -0.05]) * H, hc + np.array([0, 0.12, -0.2]) * H]
        sweep_ell(hm, pts, [0.03 * H, 0.032 * H, 0.012 * H], [0.03 * H, 0.03 * H, 0.012 * H], seg=12)
    if hair == "afro":
        ellipsoid(hm, hc + np.array([0, 0.05, 0.06]) * H, (0.108 * H, 0.112 * H, 0.1 * H), seg=24, rings=14)
    if hair == "buzz":
        M = frame_matrix(hc + np.array([0, 0.003, 0.004]) * H, (0.08 * H, 0, 0), (0, 0.1 * H, 0), (0, 0, 0.11 * H))
        M[:3, :3] = M[:3, :3] @ rot_x(-0.3)
        prof = [(0.0, 1.0)] + [(math.sin(t), math.cos(t)) for t in np.linspace(0.15, 1.6, 8)] + [(0.0, 0.95)]
        lathe(hm, M, prof, seg=22, hint=hint_from_point(hc))
    if beard:
        ellipsoid(hm, hc + np.array([0, -0.035, -0.07]) * H, (0.063 * H, 0.068 * H, 0.05 * H), seg=20, rings=10)


def legs(k, B, stance=0.0, pants="M_Cloth", shoe="M_Rubber", sole="M_White", boots=False, kick=None, seg=16):
    H = B.h
    for s in (-1, 1):
        hip = np.array([s * B.hip_x * H, 0.0, 0.93 * H])
        knee = np.array([s * (B.hip_x + 0.006 + stance * 0.5) * H, -0.012 * H, 0.50 * H])
        ank = np.array([s * (B.hip_x + 0.012 + stance) * H, 0.012 * H, 0.085 * H])
        if kick is not None and s == kick[0]:
            knee = knee + np.array(kick[1]) * H
            ank = ank + np.array(kick[2]) * H
        pts = [hip, lerp(hip, knee, 0.33), lerp(hip, knee, 0.7), knee, lerp(knee, ank, 0.3), lerp(knee, ank, 0.65), ank]
        rad = np.array([0.088, 0.08, 0.066, 0.056, 0.06, 0.047, 0.04]) * H * (1.06 if B.b > 1.1 else 1.0)
        rad = rad + 0.008 * H          # Hosenweite
        sweep_ell(k[pants], pts, rad, rad * 0.97, ref=(1, 0, 0), seg=seg, cap0=False)
        foot = ank + np.array([0, -0.05, -0.04]) * H
        hh = 0.06 if boots else 0.045
        rounded_box(k[shoe], frame_matrix(foot + np.array([0, 0, hh - 0.045]) * H, (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    (0.047 * H, 0.125 * H, hh * H), 0.035 * H, seg=3)
        if sole:
            rounded_box(k[sole], frame_matrix(foot + np.array([0, 0, -0.035]) * H, (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                        (0.05 * H, 0.128 * H, 0.012 * H), 0.008 * H, seg=1)


def arm(k, B, side, elbow, hand, sleeve="M_Accent", sleeve_len=1.0, seg=14, mitt=False):
    """sleeve_len: 0.4 = T-Shirt, 1.0 = langer Aermel (bis zum Handgelenk)."""
    H = B.h
    sh = np.array([side * B.sh_x * H, 0.01 * H, B.sh_z])
    el = np.asarray(elbow, float) * np.array([side, 1, 1]) * H
    wr = np.asarray(hand, float) * np.array([side, 1, 1]) * H
    pts = chain(sh, el, wr, 4, 4)
    r_sh, r_el, r_wr = 0.056 * B.b, 0.042 * B.b, 0.031
    rad = [r_sh, 0.053 * B.b, 0.048 * B.b, 0.045 * B.b, r_el, 0.042, 0.039, 0.034, r_wr]
    rad = np.array(rad) * H
    n = len(pts)
    cut = max(2, int(round(sleeve_len * (n - 1))))
    sl = 0.012 * H
    sweep_ell(k[sleeve], pts[:cut + 1], rad[:cut + 1] + sl, rad[:cut + 1] + sl, ref=(0, 1, 0), seg=seg, cap0=False,
              cap1=cut < n - 1)
    if cut < n - 1:
        sweep_ell(k[B.skin], pts[cut - 1:], rad[cut - 1:], rad[cut - 1:], ref=(0, 1, 0), seg=seg, cap0=False, cap1=False)
    ellipsoid(k[sleeve], sh + np.array([0, 0, -0.012]) * H, r_sh * H * 0.98 + sl, seg=seg, rings=8)                           # Schulterkugel
    ellipsoid(k[sleeve if cut >= 4 else B.skin], el, r_el * H + (sl if cut >= 4 else 0), seg=12, rings=8)
    # Hand: Handflaeche + Daumen entlang Unterarm
    d = wr - el
    ax = look_axes(d)
    palm = wr + ax[:, 2] * 0.055 * H
    ellipsoid(k[B.skin], palm, (0.042 * H, 0.02 * H, 0.06 * H), seg=12, rings=8, axes=ax)
    ellipsoid(k[B.skin], wr + ax[:, 2] * 0.04 * H + ax[:, 0] * (-side) * 0.035 * H - ax[:, 1] * 0.012 * H,
              (0.013 * H, 0.013 * H, 0.032 * H), seg=8, rings=6, axes=ax @ rot_y(-side * 0.5))
    return wr, palm


# ---------------------------------------------------------------------------
# Accessoires
# ---------------------------------------------------------------------------
def bucket_hat(k, B, mat="M_Cloth"):
    H = B.h
    hc = B.head_c
    prof = [(0.0, 0.118), (0.075, 0.115), (0.093, 0.075), (0.1, 0.035), (0.15, 0.0), (0.148, -0.01), (0.095, 0.015), (0.0, 0.02)]
    M = frame_matrix(hc + np.array([0, 0.012, 0.048]) * H, (H, 0, 0), (0, H * 1.12, 0), (0, 0, H * 0.85))
    lathe(k[mat], M, prof, seg=30, hint=hint_from_point(hc + np.array([0, 0, 0.06]) * H))


def cap_back(k, B, mat="M_Cloth"):
    H = B.h
    hc = B.head_c
    prof = [(0.0, 0.112), (0.06, 0.108), (0.085, 0.08), (0.092, 0.04), (0.09, 0.03), (0.0, 0.04)]
    M = frame_matrix(hc + np.array([0, 0.008, 0.028]) * H, (H, 0, 0), (0, H * 1.12, 0), (0, 0, H * 0.9))
    lathe(k[mat], M, prof, seg=28, hint=hint_from_point(hc + np.array([0, 0, 0.07]) * H))
    rounded_box(k[mat], frame_matrix(hc + np.array([0, 0.135, 0.06]) * H, (1, 0, 0), (0, 0.97, -0.24), (0, 0.24, 0.97)),
                (0.07 * H, 0.055 * H, 0.006 * H), 0.006 * H, seg=1)


def headphones(k, B, on=True):
    H = B.h
    hc = B.head_c
    r = 0.112 * H
    c = hc + np.array([0, 0.0, 0.012]) * H
    pts = [c + np.array([math.cos(t) * r * 0.86, 0, math.sin(t) * r * 1.02]) for t in np.linspace(0.1, math.pi - 0.1, 14)]
    for a, b in zip(pts[:-1], pts[1:]):
        tube(k["M_Plastic"], a, b, 0.009 * H, seg=8)
    for s in (-1, 1):
        M = frame_matrix(hc + np.array([s * 0.078, 0.004, -0.004]) * H, (0, 1, 0), (0, 0, 1), (s, 0, 0))
        lathe(k["M_Rubber"], M, [(0.0, 0.0), (0.04 * H, 0.0), (0.042 * H, 0.018 * H), (0.035 * H, 0.03 * H), (0.0, 0.032 * H)],
              seg=18, hint=hint_from_point(M[:3, 3] + np.array([s, 0, 0]) * 0.02))
        M2 = frame_matrix(hc + np.array([s * 0.078, 0.004, -0.004]) * H, (0, 1, 0), (0, 0, 1), (s, 0, 0))
        lathe(k["M_Accent"], M2, [(0.0, 0.031 * H), (0.026 * H, 0.031 * H), (0.026 * H, 0.035 * H), (0.0, 0.035 * H)], seg=16,
              hint=hint_from_point(M2[:3, 3]))


def shades(k, B):
    H = B.h
    hc = B.head_c
    f = 0.93 if B.sex == "f" else 1.0
    for s in (-1, 1):
        ellipsoid(k["M_DustCap"], hc + np.array([s * 0.033, -0.088, 0.012]) * H * f, (0.027 * H, 0.008 * H, 0.019 * H), seg=12, rings=6)
        tube(k["M_DustCap"], hc + np.array([s * 0.058, -0.084, 0.018]) * H * f, hc + np.array([s * 0.078, -0.01, 0.02]) * H * f,
             0.003 * H, seg=6)
    tube(k["M_DustCap"], hc + np.array([-0.008, -0.094, 0.016]) * H * f, hc + np.array([0.008, -0.094, 0.016]) * H * f, 0.003 * H, seg=6)


def hood(k, B, mat="M_Accent"):
    H = B.h
    pts = [np.array([-0.1, 0.06, 1.47]) * H, np.array([0, 0.11, 1.5]) * H, np.array([0.1, 0.06, 1.47]) * H]
    sweep_ell(k[mat], [np.array([0, 0.085, 1.455]) * H, np.array([0, 0.105, 1.52]) * H],
              [0.12 * H, 0.09 * H], [0.045 * H, 0.03 * H], seg=16)


# ---------------------------------------------------------------------------
# Figuren
# ---------------------------------------------------------------------------
def hum_raver(k):
    B = Body("f", 1.0, 0.97)
    B.skin = "M_Skin1"
    legs(k, B, stance=0.02, pants="M_Denim")
    torso(k, B, shirt="M_Accent", pants="M_Denim")
    hood(k, B)
    for s in (-1, 1):
        tube(k["M_White"], np.array([s * 0.03, -0.11, 1.42]) * B.h, np.array([s * 0.034, -0.125, 1.3]) * B.h, 0.004, seg=6, caps=True)
    neck_head(k, B, hair="long", hair_mat="M_HairLight")
    bucket_hat(k, B)
    wr, palm = arm(k, B, 1, (0.29, -0.02, 1.6), (0.26, -0.05, 1.86), sleeve_len=1.0)
    tube(k["M_Glow"], palm + np.array([0, -0.01, -0.06]), palm + np.array([0.015, -0.02, 0.2]), 0.011, seg=10, caps=True)
    arm(k, B, -1, (0.23, -0.02, 1.15), (0.25, -0.1, 0.95), sleeve_len=1.0)


def hum_dj(k):
    B = Body("m", 1.0, 1.0)
    B.skin = "M_Skin2"
    legs(k, B, stance=0.03, pants="M_Denim")
    torso(k, B, shirt="M_Accent", pants="M_Denim")
    neck_head(k, B, hair="short", hair_mat="M_HairDark")
    cap_back(k, B)
    headphones(k, B)
    arm(k, B, 1, (0.29, 0.02, 1.36), (0.1, 0.0, 1.6), sleeve_len=0.42)
    arm(k, B, -1, (0.22, -0.08, 1.12), (0.16, -0.3, 1.1), sleeve_len=0.42)


def hum_tuersteher(k):
    B = Body("m", 1.22, 1.04)
    B.skin = "M_Skin3"
    legs(k, B, stance=0.05, pants="M_Cloth", boots=True, sole=None)
    torso(k, B, shirt="M_Cloth", pants="M_Cloth")
    neck_head(k, B, hair="bald", hair_mat="M_HairDark", beard=True)
    shades(k, B)
    # Arme verschraenkt vor der Brust
    arm(k, B, 1, (0.2, -0.17, 1.17), (-0.06, -0.2, 1.24), sleeve="M_Cloth", sleeve_len=1.0)
    arm(k, B, -1, (0.2, -0.15, 1.2), (-0.08, -0.23, 1.29), sleeve="M_Cloth", sleeve_len=1.0)
    # Armbinde und Ohrstoepsel in Spielerfarbe
    H = B.h
    for s in (-1, 1):
        sh = np.array([s * B.sh_x * H, 0.01 * H, B.sh_z])
        el = np.array([s * 0.2, -0.17, 1.17]) * H
        c = lerp(sh, el, 0.45)
        sweep_ell(k["M_Accent"], [c - (el - sh) * 0.06, c + (el - sh) * 0.06], [0.068 * B.b * H] * 2, [0.068 * B.b * H] * 2,
                  ref=(0, 1, 0), seg=16, cap0=False, cap1=False)
        break
    tube(k["M_Plastic"], B.head_c + np.array([0.079, 0.0, -0.01]) * H, np.array([0.06, 0.07, 1.42]) * H, 0.003 * H, seg=6)


def hum_gasmaske(k):
    B = Body("m", 1.0, 1.0)
    B.skin = "M_Skin1"
    legs(k, B, stance=0.04, pants="M_Cloth", boots=True, sole=None)
    torso(k, B, shirt="M_Accent", pants="M_Cloth")
    neck_head(k, B, hair=None, hair_mat="M_Accent", face=False)
    H = B.h
    hc = B.head_c
    # Irokese
    for t in np.linspace(-0.4, 2.2, 11):
        p = hc + np.array([0, -math.cos(t) * 0.1, math.sin(t) * 0.11 + 0.01]) * H
        if t < 0.3:
            continue
        ellipsoid(k["M_Accent"], p, (0.011 * H, 0.024 * H, 0.04 * H), seg=8, rings=5, axes=rot_x(-(t - math.pi / 2)))
    # Gasmaske
    ellipsoid(k["M_Rubber"], hc + np.array([0, -0.06, -0.03]) * H, (0.08 * H, 0.06 * H, 0.08 * H), seg=20, rings=10)
    for s in (-1, 1):
        M = frame_matrix(hc + np.array([s * 0.034, -0.105, 0.012]) * H, (1, 0, 0), (0, 0, 1), (0, -1, 0))
        lathe(k["M_Steel"], M, [(0.0, 0.0), (0.024 * H, 0.0), (0.024 * H, 0.008 * H), (0.0, 0.008 * H)], seg=16, hint=hint_from_point(M[:3, 3]))
        lathe(k["M_DustCap"], M, [(0.0, 0.008 * H), (0.019 * H, 0.008 * H), (0.0, 0.011 * H)], seg=16, hint=hint_from_point(M[:3, 3]))
    Mf = frame_matrix(hc + np.array([0, -0.12, -0.06]) * H, (1, 0, 0), (0, 0.5, 0.87), (0, -0.87, 0.5))
    lathe(k["M_Steel"], Mf, [(0.0, 0.0), (0.03 * H, 0.0), (0.03 * H, 0.05 * H), (0.0, 0.05 * H)], seg=18, hint=hint_from_point(Mf[:3, 3]))
    # Arme hoch
    arm(k, B, 1, (0.3, -0.02, 1.62), (0.24, -0.03, 1.88), sleeve_len=1.0)
    arm(k, B, -1, (0.3, -0.02, 1.62), (0.24, -0.03, 1.88), sleeve_len=1.0)


def hum_taenzerin(k):
    B = Body("f", 0.98, 0.95)
    B.skin = "M_Skin2"
    legs(k, B, stance=0.03, pants="M_Cloth", kick=(-1, (0.02, -0.06, 0.08), (0.02, -0.02, 0.12)))
    torso(k, B, shirt="M_Accent", pants="M_Cloth", top_style="crop")
    neck_head(k, B, hair="afro", hair_mat="M_HairDark")
    arm(k, B, 1, (0.27, -0.04, 1.55), (0.12, -0.08, 1.78), sleeve_len=0.15)
    arm(k, B, -1, (0.3, -0.03, 1.36), (0.42, -0.06, 1.5), sleeve_len=0.15)
    # Kreolen
    H = B.h
    for s in (-1, 1):
        c = B.head_c + np.array([s * 0.075, -0.004, -0.05]) * H
        lathe(k["M_Steel"], frame_matrix(c, (0, 1, 0), (0, 0, 1), (1, 0, 0)),
              [(0.016 * H, -0.002), (0.019 * H, 0.0), (0.016 * H, 0.002)], seg=14, hint=None)


HUMANS = {"raver": hum_raver, "dj": hum_dj, "tuersteher": hum_tuersteher, "gasmaske": hum_gasmaske,
          "taenzerin": hum_taenzerin}


def make(kind):
    k = Kit("HUM_" + kind)
    HUMANS[kind](k)
    ground(k.list())
    return {
        "name": "HUM_" + kind.upper(),
        "cabinet": None, "cutters": [],
        "parts": k.list(),
        "bevel": 0.0,
        "dims": {"height": 1.8},
        "shots": {"front34": ((-1.6, -3.0, 1.55), (0, 0, 0.92))},
    }


if __name__ == "__main__":
    from figures_geometry import stats
    for kind in HUMANS:
        s = make(kind)
        tot, size, lo, hi = stats(s)
        print(f"{kind:11s} {tot:6d} Dreiecke  {len(s['parts'])} Meshes  glTF {size.round(3)}")


# ---------------------------------------------------------------------------
# Club-Gaeste: 6 Varianten, wenig Dreiecke, Farben als Vertex-Farben (1 Material)
# ---------------------------------------------------------------------------
CROWD_PAL = {   # linear RGB
    "skin": [(0.73, 0.41, 0.27), (0.35, 0.155, 0.074), (0.106, 0.043, 0.022), (0.6, 0.33, 0.2)],
    "top": [(0.02, 0.02, 0.025), (0.5, 0.08, 0.85), (0.03, 0.45, 0.9), (0.8, 0.8, 0.8), (0.9, 0.15, 0.45), (0.02, 0.6, 0.35)],
    "bottom": [(0.02, 0.02, 0.025), (0.06, 0.1, 0.2), (0.12, 0.12, 0.13)],
    "hair": [(0.02, 0.012, 0.008), (0.35, 0.2, 0.06), (0.012, 0.01, 0.01), (0.6, 0.05, 0.4)],
}
CROWD_VARIANTS = [
    # sex, build, height, skin, top, bottom, hair-style, hair-col, sleeve, pose, top_style
    ("m", 1.0, 1.0, 0, 0, 1, "short", 0, 0.42, "both_up", "tee"),
    ("f", 0.97, 0.95, 1, 1, 0, "ponytail", 2, 1.0, "one_up", "tee"),
    ("m", 1.08, 1.03, 2, 3, 0, "buzz", 2, 0.42, "groove", "tee"),
    ("f", 0.95, 0.94, 3, 4, 2, "long", 1, 0.15, "both_up", "crop"),
    ("m", 1.0, 0.98, 1, 5, 2, "afro", 2, 1.0, "one_up", "tee"),
    ("f", 0.97, 0.96, 0, 2, 0, "bun", 3, 0.42, "groove", "tee"),
]
POSES = {
    "both_up": [((0.3, -0.02, 1.6), (0.24, -0.03, 1.86)), ((0.3, -0.02, 1.6), (0.24, -0.03, 1.86))],
    "one_up": [((0.27, -0.06, 1.58), (0.18, -0.12, 1.82)), ((0.22, -0.02, 1.13), (0.2, -0.16, 1.02))],
    "groove": [((0.25, -0.1, 1.2), (0.16, -0.3, 1.3)), ((0.25, -0.1, 1.18), (0.14, -0.3, 1.24))],
}


class _LowPoly:
    """Reduziert Segmentzahlen aller Bausteine, solange aktiv."""
    def __init__(self, q):
        self.q = q

    def __enter__(self):
        g = globals()
        self.saved = {n: g[n] for n in ("ellipsoid", "sweep_ell", "lathe", "capsule", "tube", "rounded_box")}
        q = self.q
        red = lambda v, lo: max(lo, int(round(v * q)))
        e0, s0, l0, c0, t0, r0 = (self.saved[n] for n in ("ellipsoid", "sweep_ell", "lathe", "capsule", "tube", "rounded_box"))
        g["ellipsoid"] = lambda part, c, r, seg=20, rings=12, axes=None: e0(part, c, r, red(seg, 6), red(rings, 4), axes)
        g["sweep_ell"] = lambda part, pts, rx, ry, ref=(1.0, 0.0, 0.0), seg=20, **kw: s0(part, pts, rx, ry, ref, red(seg, 6), **kw)
        g["lathe"] = lambda part, M, prof, seg=48, smooth=True, hint=None: l0(part, M, prof, red(seg, 6), smooth, hint)
        g["capsule"] = lambda part, a, b, r, seg=14: c0(part, a, b, r, red(seg, 6))
        g["tube"] = lambda part, a, b, r, seg=10, caps=False, smooth=True: t0(part, a, b, r, red(seg, 5), caps, smooth)
        g["rounded_box"] = lambda part, M, half, radius, seg=3: r0(part, M, half, radius, 1)
        return self

    def __exit__(self, *a):
        globals().update(self.saved)


def crowd_person(k, v):
    sex, build, height, skin, top, bottom, hair, hcol, sleeve, pose, style = v
    B = Body(sex, build, height)
    B.skin = "M_Skin1"
    legs(k, B, stance=0.03, pants="M_Bottom", shoe="M_Bottom", sole=None, seg=10)
    torso(k, B, shirt="M_Top", pants="M_Bottom", top_style=style, seg=14)
    neck_head(k, B, hair=hair, hair_mat="M_Hair", face=False)
    for side, (el, ha) in zip((1, -1), POSES[pose]):
        wr, palm = arm(k, B, side, el, ha, sleeve="M_Top", sleeve_len=sleeve, seg=9)
        if pose == "both_up" and side == 1:
            tube(k["M_GlowV"], palm + np.array([0, -0.01, -0.05]), palm + np.array([0.01, -0.02, 0.17]), 0.011, seg=6, caps=True)
    cols = {"M_Skin1": CROWD_PAL["skin"][skin], "M_Top": CROWD_PAL["top"][top], "M_Bottom": CROWD_PAL["bottom"][bottom],
            "M_Hair": CROWD_PAL["hair"][hcol], "M_GlowV": (1.0, 0.25, 0.75)}
    return cols


def make_crowd():
    from assetlib import Part
    parts = []
    with _LowPoly(0.5):
        for i, v in enumerate(CROWD_VARIANTS):
            k = Kit(f"CROWD_V{i}")
            cols = crowd_person(k, v)
            ground(k.list())
            merged = Part(f"CROWD_V{i}_Body", "M_Crowd")
            merged.colors = []
            merged.group = f"CrowdV{i}"
            for p in k.list():
                n0 = len(merged.verts)
                merged.extend(p)
                merged.colors += [cols[p.material]] * (len(merged.verts) - n0)
            parts.append(merged)
    return {
        "name": "CROWD",
        "cabinet": None, "cutters": [],
        "parts": parts,
        "groups": {f"CrowdV{i}": {"parent": None, "origin": (0.0, 0.0, 0.0)} for i in range(len(CROWD_VARIANTS))},
        "bevel": 0.0,
        "dims": {"height": 1.9},
        "shots": {"front34": ((-1.6, -3.0, 1.55), (0, 0, 0.92))},
    }
