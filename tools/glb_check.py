#!/usr/bin/env python3
"""
glb_check.py: Pruefung (und kleine Korrekturen) von GLB-Dateien fuer Aal You Ready.

Nur Python-Standardbibliothek. Prueft:
  - gueltiger GLB-Container (glTF 2.0)
  - sichtbare Geometrie, Dreiecke, Vertices, Draw Calls (Primitive)
  - Materialien, alphaMode, doubleSided, eingebettete Bilder
  - Weltmasse (inkl. Node-Transformationen), Ursprung am Boden, zentriert
  - Front-Ausrichtung (Material X liegt vorne = +Z, glTF/Babylon-Konvention)
  - Datei- und Polygonbudget

Optional: --mask-materials setzt alphaMode MASK (+ alphaCutoff) fuer Materialien,
die der Blender-Exporter als BLEND exportiert (Lochblech soll Alpha-Test sein).

Exit-Code 0 = alle Pflichtpruefungen bestanden, 1 = mindestens ein FAIL.
"""
import argparse
import json
import math
import struct
import sys

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError("Keine GLB-Datei (Magic falsch)")
    if version != 2:
        raise ValueError(f"GLB-Version {version}, erwartet 2")
    off = 12
    js, binc = None, b""
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == CHUNK_JSON:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == CHUNK_BIN:
            binc = chunk
        off += 8 + clen
    if js is None:
        raise ValueError("JSON-Chunk fehlt")
    return js, binc, len(data)


def write_glb(path, js, binc):
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * ((4 - len(jb) % 4) % 4)
    bb = binc + b"\x00" * ((4 - len(binc) % 4) % 4)
    total = 12 + 8 + len(jb) + (8 + len(bb) if bb else 0)
    out = struct.pack("<III", GLB_MAGIC, 2, total) + struct.pack("<II", len(jb), CHUNK_JSON) + jb
    if bb:
        out += struct.pack("<II", len(bb), CHUNK_BIN) + bb
    open(path, "wb").write(out)


# --- Mathe ---------------------------------------------------------------
def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def node_matrix(n):
    if "matrix" in n:
        m = n["matrix"]  # spaltenweise
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    t = n.get("translation", [0, 0, 0])
    q = n.get("rotation", [0, 0, 0, 1])
    s = n.get("scale", [1, 1, 1])
    x, y, z, w = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[0][0] * s[0], r[0][1] * s[1], r[0][2] * s[2], t[0]],
            [r[1][0] * s[0], r[1][1] * s[1], r[1][2] * s[2], t[1]],
            [r[2][0] * s[0], r[2][1] * s[1], r[2][2] * s[2], t[2]],
            [0, 0, 0, 1]]


def xform(m, p):
    return [sum(m[i][k] * p[k] for k in range(3)) + m[i][3] for i in range(3)]


def analyse(js, file_bytes, front_material=None):
    acc = js.get("accessors", [])
    meshes = js.get("meshes", [])
    mats = js.get("materials", [])
    nodes = js.get("nodes", [])
    res = {"file_bytes": file_bytes, "triangles": 0, "vertices": 0, "primitives": 0,
           "meshes": len(meshes), "materials": [], "images": [], "textures": len(js.get("textures", []))}

    for m in mats:
        pbr = m.get("pbrMetallicRoughness", {})
        res["materials"].append({
            "name": m.get("name"),
            "alphaMode": m.get("alphaMode", "OPAQUE"),
            "alphaCutoff": m.get("alphaCutoff"),
            "doubleSided": m.get("doubleSided", False),
            "baseColorFactor": pbr.get("baseColorFactor"),
            "metallic": pbr.get("metallicFactor", 1.0),
            "roughness": pbr.get("roughnessFactor", 1.0),
            "baseColorTexture": "baseColorTexture" in pbr,
            "normalTexture": "normalTexture" in m,
        })
    for img in js.get("images", []):
        res["images"].append({"name": img.get("name"), "mimeType": img.get("mimeType"),
                              "embedded": "bufferView" in img,
                              "uri": img.get("uri") if "uri" in img and not img["uri"].startswith("data:") else None,
                              "bytes": js["bufferViews"][img["bufferView"]]["byteLength"] if "bufferView" in img else None})

    # Weltgrenzen ueber den Szenengraphen
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    mat_bounds = {}
    scene_idx = js.get("scene", 0)
    roots = js["scenes"][scene_idx]["nodes"] if js.get("scenes") else list(range(len(nodes)))
    stack = [(r, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) for r in roots]
    while stack:
        ni, parent = stack.pop()
        n = nodes[ni]
        m = mat_mul(parent, node_matrix(n))
        if "mesh" in n:
            for prim in meshes[n["mesh"]]["primitives"]:
                res["primitives"] += 1
                pa = acc[prim["attributes"]["POSITION"]]
                res["vertices"] += pa["count"]
                mode = prim.get("mode", 4)
                cnt = acc[prim["indices"]]["count"] if "indices" in prim else pa["count"]
                if mode == 4:
                    res["triangles"] += cnt // 3
                mn, mx = pa.get("min"), pa.get("max")
                if mn and mx:
                    plo = [math.inf] * 3
                    phi = [-math.inf] * 3
                    for cx in (mn[0], mx[0]):
                        for cy in (mn[1], mx[1]):
                            for cz in (mn[2], mx[2]):
                                p = xform(m, [cx, cy, cz])
                                for i in range(3):
                                    lo[i] = min(lo[i], p[i])
                                    hi[i] = max(hi[i], p[i])
                                    plo[i] = min(plo[i], p[i])
                                    phi[i] = max(phi[i], p[i])
                    mname = mats[prim["material"]].get("name") if "material" in prim else None
                    b = mat_bounds.setdefault(mname, [[math.inf] * 3, [-math.inf] * 3])
                    for i in range(3):
                        b[0][i] = min(b[0][i], plo[i])
                        b[1][i] = max(b[1][i], phi[i])
        for c in n.get("children", []):
            stack.append((c, m))
    res["bounds_min"] = [round(v, 4) for v in lo]
    res["bounds_max"] = [round(v, 4) for v in hi]
    res["size_m"] = [round(hi[i] - lo[i], 4) for i in range(3)]
    res["material_bounds"] = {k: {"min": [round(x, 4) for x in v[0]], "max": [round(x, 4) for x in v[1]]}
                              for k, v in mat_bounds.items()}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    ap.add_argument("--warn-bytes", type=int, default=1_000_000)
    ap.add_argument("--max-tris", type=int, default=40_000)
    ap.add_argument("--max-primitives", type=int, default=16)
    ap.add_argument("--expect-size", type=float, nargs=3, metavar=("X", "Y", "Z"),
                    help="erwartete Masse in Metern (glTF: X Breite, Y Hoehe, Z Tiefe)")
    ap.add_argument("--size-tolerance", type=float, default=0.03)
    ap.add_argument("--center-tolerance", type=float, default=0.1)
    ap.add_argument("--front-material", help="Material, das vorne (+Z) liegen muss")
    ap.add_argument("--mask-materials", default="", help="Kommagetrennt: alphaMode MASK setzen")
    ap.add_argument("--alpha-cutoff", type=float, default=0.45)
    ap.add_argument("--json-out")
    ap.add_argument("--summary", help="Markdown anhaengen (z.B. $GITHUB_STEP_SUMMARY)")
    a = ap.parse_args()

    checks = []

    def check(name, ok, detail="", level="FAIL"):
        checks.append({"name": name, "status": "PASS" if ok else level, "detail": detail})

    try:
        js, binc, size = read_glb(a.glb)
        check("GLB-Container glTF 2.0 lesbar", True, js.get("asset", {}).get("generator", ""))
    except Exception as e:
        check("GLB-Container glTF 2.0 lesbar", False, str(e))
        report(a, checks, {})
        return 1

    if a.mask_materials:
        names = {n.strip() for n in a.mask_materials.split(",") if n.strip()}
        changed = []
        for m in js.get("materials", []):
            if m.get("name") in names and m.get("alphaMode") != "MASK":
                m["alphaMode"] = "MASK"
                m["alphaCutoff"] = a.alpha_cutoff
                changed.append(m["name"])
        if changed:
            write_glb(a.glb, js, binc)
            js, binc, size = read_glb(a.glb)
        found = names & {m.get("name") for m in js.get("materials", [])}
        check("alphaMode MASK gesetzt", found == names,
              f"geaendert: {changed or 'nichts'}; fehlend: {sorted(names - found) or '-'}")

    r = analyse(js, size, a.front_material)

    check("Sichtbare Geometrie vorhanden", r["triangles"] > 0, f"{r['triangles']} Dreiecke")
    check(f"Dreiecksbudget <= {a.max_tris}", r["triangles"] <= a.max_tris, f"{r['triangles']}")
    check(f"Draw Calls (Primitive) <= {a.max_primitives}", r["primitives"] <= a.max_primitives,
          f"{r['primitives']}")
    check(f"Dateigroesse <= {a.max_bytes / 1e6:.1f} MB", size <= a.max_bytes, f"{size / 1024:.0f} KB")
    if size > a.warn_bytes:
        check(f"Dateigroesse <= {a.warn_bytes / 1e6:.1f} MB (Empfehlung)", False,
              f"{size / 1024:.0f} KB", level="WARN")
    ext = [i for i in r["images"] if not i["embedded"]]
    check("Alle Bilder eingebettet", not ext, f"{len(r['images'])} Bilder, extern: {len(ext)}")
    check("Materialien vorhanden", len(r["materials"]) > 0, f"{len(r['materials'])}")

    lo, hi = r["bounds_min"], r["bounds_max"]
    check("Ursprung am Boden (min Y ~ 0)", abs(lo[1]) <= 0.01, f"min Y = {lo[1]}")
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    check("Ursprung horizontal mittig", abs(cx) <= a.center_tolerance and abs(cz) <= a.center_tolerance,
          f"Mitte X = {cx:.3f}, Z = {cz:.3f}")
    if a.expect_size:
        dev = [abs(r["size_m"][i] - a.expect_size[i]) for i in range(3)]
        check("Masse plausibel", max(dev) <= a.size_tolerance,
              f"ist {r['size_m']} m, erwartet {a.expect_size} m (Toleranz {a.size_tolerance})")
    if a.front_material:
        mb = r["material_bounds"].get(a.front_material)
        if mb is None:
            check("Front zeigt nach +Z", False, f"Material {a.front_material} nicht gefunden")
        else:
            front_z = mb["max"][2]
            check("Front zeigt nach +Z", front_z >= hi[2] - 0.02 and front_z > cz,
                  f"{a.front_material} max Z = {front_z}, Gesamt max Z = {hi[2]}")

    report(a, checks, r)
    return 0 if all(c["status"] != "FAIL" for c in checks) else 1


def report(a, checks, r):
    for c in checks:
        print(f"[{c['status']}] {c['name']}  {c['detail']}")
    if r:
        print(f"Masse (m): {r['size_m']}  min {r['bounds_min']}  max {r['bounds_max']}")
        for m in r["materials"]:
            print(f"  Material {m['name']}: alpha={m['alphaMode']} doubleSided={m['doubleSided']} "
                  f"metal={m['metallic']} rough={m['roughness']} "
                  f"baseTex={m['baseColorTexture']} normalTex={m['normalTexture']}")
        for i in r["images"]:
            print(f"  Bild {i['name']}: {i['mimeType']} {i['bytes']} B eingebettet={i['embedded']}")
    if a.json_out:
        with open(a.json_out, "w") as fh:
            json.dump({"checks": checks, "analysis": r}, fh, indent=2)
    if a.summary:
        with open(a.summary, "a") as fh:
            fh.write(f"### GLB-Pruefung `{a.glb}`\n\n| Status | Pruefung | Detail |\n|---|---|---|\n")
            for c in checks:
                icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[c["status"]]
                fh.write(f"| {icon} | {c['name']} | {c['detail']} |\n")
            if r:
                fh.write(f"\nDreiecke: **{r['triangles']}**, Vertices: {r['vertices']}, "
                         f"Draw Calls: {r['primitives']}, Groesse: {r['file_bytes'] / 1024:.0f} KB, "
                         f"Masse: {r['size_m']} m\n\n")


if __name__ == "__main__":
    sys.exit(main())
