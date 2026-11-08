"""
assetlib: reine Python/numpy-Bausteine fuer die Club-Asset-Pipeline.

Bewusst OHNE bpy, damit Geometrie und Texturen auch ausserhalb von Blender
getestet werden koennen (lokal, in CI, in Unit-Tests). Blender-spezifischer
Code liegt in den jeweiligen Asset-Skripten.

Koordinaten: Blender-Konvention, Meter, Z oben, Vorderseite zeigt nach -Y.
Der glTF-Exporter (export_yup=True) macht daraus Y oben, Front nach +Z.
"""
import math
import struct
import zlib

import numpy as np


# ---------------------------------------------------------------------------
# PNG schreiben (ohne PIL, Blender bringt kein PIL mit)
# ---------------------------------------------------------------------------
def write_png(path, arr):
    """arr: uint8, Form (H, W, 3|4), Zeile 0 = oben."""
    arr = np.ascontiguousarray(arr, dtype=np.uint8)
    h, w, c = arr.shape
    color_type = {3: 2, 4: 6}[c]
    # Filter "Sub" (1) pro Zeile, komprimiert Muster deutlich besser als 0
    rows = arr.reshape(h, w * c).astype(np.int16)
    sub = rows.copy()
    sub[:, c:] = (rows[:, c:] - rows[:, :-c]) % 256
    raw = np.empty((h, w * c + 1), dtype=np.uint8)
    raw[:, 0] = 1
    raw[:, 1:] = sub.astype(np.uint8)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw.tobytes(), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------------------
# Kachelbare Texturen
# ---------------------------------------------------------------------------
def periodic_noise(size, sigma_px, rng):
    """Gauss-gefiltertes Rauschen, per FFT automatisch nahtlos kachelbar."""
    n = rng.standard_normal((size, size))
    f = np.fft.fftfreq(size)
    fx, fy = np.meshgrid(f, f)
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * np.pi * sigma_px) ** 2 / 2)
    h = np.real(np.fft.ifft2(np.fft.fft2(n) * g))
    h -= h.mean()
    h /= h.std() + 1e-9
    return h


def height_to_normal(h, strength):
    """Hoehenfeld -> Tangent-Space-Normal-Map im glTF/OpenGL-Format (+Y = V hoch)."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5   # Zeilen laufen nach unten
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones_like(h)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    n = np.stack([nx / ln, ny / ln, nz / ln], -1)
    return ((n * 0.5 + 0.5) * 255 + 0.5).clip(0, 255).astype(np.uint8)


def texture_grain_normal(size=256, seed=7):
    """Feine Struktur fuer Polyurea-/Strukturlack-Gehaeuse und Papiermembran."""
    rng = np.random.default_rng(seed)
    fine = periodic_noise(size, 1.1, rng)
    mid = periodic_noise(size, 3.5, rng)
    h = np.tanh(fine * 1.3) * 0.65 + mid * 0.35
    return height_to_normal(h, 0.55)


def texture_grille(size=256, cols=4, hole_frac=0.38, edge_px=5.0):
    """Gelochtes Stahlgitter, versetzte Rundlochung, nahtlos kachelbar.

    Liefert (color_rgba, normal_rgb). Alpha = 1 Metall, 0 Loch.
    cols muss gerade sein, sonst ist die versetzte Reihe nicht periodisch.
    """
    assert cols % 2 == 0
    pitch = size / cols
    yy, xx = np.mgrid[0:size, 0:size] + 0.5
    d = np.full((size, size), 1e9)
    for r in range(-1, cols + 1):
        for c in range(-1, cols + 2):
            cy = (r + 0.5) * pitch
            cx = (c + 0.5 + 0.5 * (r % 2)) * pitch
            d = np.minimum(d, np.hypot(xx - cx, yy - cy))
    radius = hole_frac * pitch
    alpha = np.clip((d - radius) / 1.5 + 0.5, 0.0, 1.0)
    t = np.clip((d - radius) / edge_px, 0.0, 1.0)
    height = t * t * (3 - 2 * t)                        # smoothstep -> runde Lochkante
    normal = height_to_normal(height * 3.0, 1.0)
    rng = np.random.default_rng(3)
    speck = periodic_noise(size, 1.0, rng) * 1.5
    rgb = np.clip(9 + speck, 0, 255)                    # sehr dunkles Pulverbeschichtungs-Schwarz
    color = np.zeros((size, size, 4), dtype=np.uint8)
    color[..., 0] = rgb
    color[..., 1] = rgb
    color[..., 2] = np.clip(rgb + 1, 0, 255)
    color[..., 3] = (alpha * 255 + 0.5).astype(np.uint8)
    return color, normal


def _draw_segments(field, segs, value, rng_w):
    """Periodisch umbrechende, weiche Linien in ein Feld (min-Blend) zeichnen."""
    size = field.shape[0]
    for (x0, y0, x1, y1, w) in segs:
        pad = int(w * 3) + 2
        xa, xb = int(min(x0, x1)) - pad, int(max(x0, x1)) + pad
        ya, yb = int(min(y0, y1)) - pad, int(max(y0, y1)) + pad
        ys, xs = np.mgrid[ya:yb, xa:xb] + 0.5
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy + 1e-9
        t = np.clip(((xs - x0) * dx + (ys - y0) * dy) / L2, 0, 1)
        d = np.hypot(xs - (x0 + t * dx), ys - (y0 + t * dy))
        a = np.clip(1.0 - d / w, 0, 1) ** 1.5
        # Kratzer laufen an den Enden aus
        a *= np.clip(np.minimum(t, 1 - t) * 6, 0, 1)
        iy = np.mod(np.arange(ya, yb), size)
        ix = np.mod(np.arange(xa, xb), size)
        sub = field[np.ix_(iy, ix)]
        field[np.ix_(iy, ix)] = sub * (1 - a) + value * a


def texture_wear(size=512, seed=11):
    """Gebrauchsspuren fuer Gehaeuselack: liefert (roughness_orm_rgb, base_rgb).

    ORM nach glTF: R = Occlusion (1), G = Roughness, B = Metallic (0).
    Abrieb: glattere Flecken (Haende, Transport). Kratzer: helle, glatte Linien,
    ueberwiegend waagerecht (Schieben, Stapeln).
    """
    rng = np.random.default_rng(seed)
    rough = 0.64 + 0.035 * periodic_noise(size, 10, rng)
    patch = periodic_noise(size, 30, rng)
    rubbed = np.clip((patch - 0.9) / 0.9, 0, 1)
    rough = rough * (1 - rubbed) + 0.47 * rubbed
    shade = np.zeros((size, size))
    shade += rubbed * 0.010

    segs = []
    for _ in range(45):
        x0, y0 = rng.uniform(0, size, 2)
        ang = rng.normal(0, 0.35) + (np.pi if rng.random() < 0.5 else 0)
        if rng.random() < 0.2:
            ang = rng.uniform(0, np.pi)
        ln = rng.uniform(15, 140)
        segs.append((x0, y0, x0 + ln * np.cos(ang), y0 + ln * np.sin(ang), rng.uniform(0.7, 1.6)))
    _draw_segments(rough, segs, 0.36, rng)
    sc = np.zeros((size, size))
    _draw_segments(sc, segs, 1.0, rng)
    shade += sc * 0.035

    # quantisieren, damit PNG gut komprimiert
    g = (np.round(np.clip(rough, 0, 1) * 255 / 2) * 2).clip(0, 255).astype(np.uint8)
    orm = np.zeros((size, size, 3), dtype=np.uint8)
    orm[..., 0] = 255
    orm[..., 1] = g
    # Basisfarbe: Lack ~0.020 linear (sRGB ~ 40/255 nach Umrechnung erledigt Blender)
    lin = 0.020 + shade
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    b8 = np.round(srgb * 255).clip(0, 255).astype(np.uint8)
    base = np.stack([b8, b8, np.clip(b8.astype(int) + 1, 0, 255).astype(np.uint8)], -1)
    return orm, base


# ---------------------------------------------------------------------------
# Mesh-Builder
# ---------------------------------------------------------------------------
def newell_normal(pts):
    n = np.zeros(3)
    m = len(pts)
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % m]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    ln = np.linalg.norm(n)
    return n / ln if ln > 1e-12 else n


def hint_from_point(p):
    """Normale soll vom Punkt p weg zeigen (z.B. Mittelpunkt eines Koerpers)."""
    p = np.asarray(p, float)
    return lambda c: c - p


def hint_toward_point(p):
    p = np.asarray(p, float)
    return lambda c: p - c


def hint_dir(d):
    d = np.asarray(d, float)
    return lambda c: d


def hint_from_axis(origin, axis):
    """Normale soll radial von einer Achse weg zeigen."""
    o = np.asarray(origin, float)
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)

    def f(c):
        v = c - o
        return v - a * np.dot(v, a)
    return f


class Part:
    """Sammelt Vertices/Faces fuer ein Material. Wird spaeter ein Blender-Mesh."""

    def __init__(self, name, material, uv_scale=1.0):
        self.name = name
        self.material = material
        self.uv_scale = uv_scale
        self.verts = []
        self.faces = []
        self.smooth = []

    # -- Grundfunktionen ----------------------------------------------------
    def add_verts(self, pts):
        start = len(self.verts)
        for p in pts:
            self.verts.append(np.asarray(p, float))
        return list(range(start, start + len(pts)))

    def face(self, idx, smooth=False, hint=None):
        idx = list(idx)
        if len(set(idx)) < 3:
            return
        if hint is not None:
            pts = [self.verts[i] for i in idx]
            n = newell_normal(pts)
            c = np.mean(pts, axis=0)
            if np.dot(n, hint(c)) < 0:
                idx.reverse()
        self.faces.append(idx)
        self.smooth.append(bool(smooth))

    def poly(self, pts, smooth=False, hint=None):
        self.face(self.add_verts(pts), smooth, hint)

    def grid(self, rings, closed=True, smooth=True, hint=None):
        """Verbindet aufeinanderfolgende Ringe (gleiche Punktzahl) mit Quads.
        Ein Ring mit genau einem Punkt wird als Pol (Dreiecksfaecher) behandelt."""
        ids = [self.add_verts(r) for r in rings]
        for a, b in zip(ids[:-1], ids[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            m = max(len(a), len(b))
            for j in range(m if closed else m - 1):
                j2 = (j + 1) % m
                if len(a) == 1:
                    self.face([a[0], b[j], b[j2]], smooth, hint)
                elif len(b) == 1:
                    self.face([a[j], a[j2], b[0]], smooth, hint)
                else:
                    self.face([a[j], a[j2], b[j2], b[j]], smooth, hint)
        return ids

    def extend(self, other):
        off = len(self.verts)
        self.verts.extend(other.verts)
        self.faces.extend([[i + off for i in f] for f in other.faces])
        self.smooth.extend(other.smooth)

    # -- Ausgabe ------------------------------------------------------------
    def triangle_count(self):
        return sum(len(f) - 2 for f in self.faces)

    def box_uvs(self):
        """Box-Projektion pro Face-Loop (Reihenfolge = faces/loops)."""
        uvs = []
        s = self.uv_scale
        for f in self.faces:
            pts = [self.verts[i] for i in f]
            n = newell_normal(pts)
            ax = int(np.argmax(np.abs(n)))
            for p in pts:
                if ax == 0:
                    u, v = (p[1] if n[0] > 0 else -p[1]), p[2]
                elif ax == 1:
                    u, v = (-p[0] if n[1] > 0 else p[0]), p[2]
                else:
                    u, v = p[0], (p[1] if n[2] > 0 else -p[1])
                uvs.append((u * s, v * s))
        return uvs


# ---------------------------------------------------------------------------
# Transformationen
# ---------------------------------------------------------------------------
def frame_matrix(origin, x_axis, y_axis, z_axis):
    M = np.eye(4)
    M[:3, 0] = x_axis
    M[:3, 1] = y_axis
    M[:3, 2] = z_axis
    M[:3, 3] = origin
    return M


def apply(M, pts):
    pts = np.asarray(pts, float)
    return (pts @ M[:3, :3].T) + M[:3, 3]


# ---------------------------------------------------------------------------
# Primitive (alle in lokalem Rahmen M, Achse = lokales +Z)
# ---------------------------------------------------------------------------
def lathe(part, M, profile, seg=48, smooth=True, hint=None):
    """Rotationskoerper um lokale Z-Achse. profile = [(radius, z), ...]."""
    rings = []
    for r, z in profile:
        if r < 1e-7:
            rings.append(apply(M, [(0.0, 0.0, z)]))
        else:
            a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
            loc = np.stack([r * np.cos(a), r * np.sin(a), np.full(seg, z)], -1)
            rings.append(apply(M, loc))
    part.grid(rings, closed=True, smooth=smooth, hint=hint)


def cylinder(part, M, radius, z0, z1, seg=24, caps=True, smooth=True):
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    bottom = apply(M, np.stack([radius * np.cos(a), radius * np.sin(a), np.full(seg, z0)], -1))
    top = apply(M, np.stack([radius * np.cos(a), radius * np.sin(a), np.full(seg, z1)], -1))
    center = apply(M, [(0, 0, (z0 + z1) / 2)])[0]
    ib = part.add_verts(bottom)
    it = part.add_verts(top)
    axis = M[:3, 2]
    side_hint = hint_from_axis(center, axis)
    for j in range(seg):
        j2 = (j + 1) % seg
        part.face([ib[j], ib[j2], it[j2], it[j]], smooth, side_hint)
    if caps:
        part.face(ib, False, hint_from_point(center))
        part.face(it, False, hint_from_point(center))


def box(part, M, half, smooth=False):
    """Geschlossene Box mit geteilten Vertices (manifold, booleantauglich)."""
    hx, hy, hz = half
    corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
               (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    ids = part.add_verts(apply(M, corners))
    c = M[:3, 3]
    h = hint_from_point(c)
    for f in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]):
        part.face([ids[i] for i in f], smooth, h)


def rounded_box(part, M, half, radius, seg=3):
    """Box mit echten runden Kanten (Cube-to-Sphere-Mapping), geteilte Vertices."""
    half = np.asarray(half, float)
    radius = min(radius, float(half.min()) * 0.98)
    inner = half - radius
    phis = np.linspace(0, np.pi / 4, seg + 1)

    def coords(s, r):
        neg = [-(s - r) - r * math.tan(p) for p in phis[::-1]]
        pos = [(s - r) + r * math.tan(p) for p in phis]
        mid = []
        if s - r > 1e-6:
            mid = list(np.linspace(-(s - r), s - r, 3)[1:-1])
        return np.array(neg + mid + pos)

    lookup = {}
    center = M[:3, 3]

    def vid(q):
        inn = np.clip(q, -inner, inner)
        d = q - inn
        ln = np.linalg.norm(d)
        p = inn + (d / ln * radius if ln > 1e-12 else d)
        key = tuple(np.round(p, 7))
        if key not in lookup:
            lookup[key] = part.add_verts(apply(M, [p]))[0]
        return lookup[key]

    hint = hint_from_point(center)
    for axis in range(3):
        for sign in (-1, 1):
            a1, a2 = [i for i in range(3) if i != axis]
            c1 = coords(half[a1], radius)
            c2 = coords(half[a2], radius)
            grid = [[None] * len(c2) for _ in c1]
            for i, u in enumerate(c1):
                for j, v in enumerate(c2):
                    q = np.zeros(3)
                    q[axis] = sign * half[axis]
                    q[a1] = u
                    q[a2] = v
                    grid[i][j] = vid(q)
            for i in range(len(c1) - 1):
                for j in range(len(c2) - 1):
                    part.face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]],
                              True, hint)


def superellipse(w, h, n, count):
    t = np.linspace(0, 2 * np.pi, count, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    x = w * np.sign(c) * np.abs(c) ** (2.0 / n)
    y = h * np.sign(s) * np.abs(s) ** (2.0 / n)
    return x, y
