"""
Import von Avataren aus "100Avatars" (Polygonal Mind, CC BY 4.0) fuer "Aal You Ready?".

Blender headless:
  blender -b --factory-startup --python-exit-code 1 -P tools/avatars/import_avatars.py -- \
      --src build/100avatars --list tools/avatars/candidates.txt \
      --out aal-you-ready/play/assets/avatars --sheet aal-you-ready/play/assets/previews/avatars_sheet.jpg

Pro Avatar (VRM = glTF-Binärdatei):
  1. glTF-Import (VRM-Erweiterungen werden ignoriert)
  2. normalisieren: Hoehe 1.0, Blick nach -Y (glTF +Z), Fuesse auf z = 0, mittig
  3. Texturen auf max. 512 px verkleinern
  4. GLB mit Skelett exportieren (club_av_<nr>.glb), Knochennamen im Bericht
Zum Schluss alle nebeneinander mit Namen als Uebersichtsbild rendern (Cycles).
"""
import argparse
import json
import math
import os
import shutil
import sys
import time

import bpy
from mathutils import Vector, Matrix


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--list", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet", default="")
    ap.add_argument("--tex", type=int, default=512)
    ap.add_argument("--samples", type=int, default=24)
    return ap.parse_args(argv)


def log(m):
    print("[AV] " + m, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def world_bounds(objs):
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
        ev.to_mesh_clear()
    return lo, hi


def import_one(path, tmpdir):
    glb = os.path.join(tmpdir, "in.glb")
    shutil.copyfile(path, glb)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    return [o for o in bpy.data.objects if o not in before]


def normalize(objs, front_flip):
    roots = [o for o in objs if o.parent is None]
    root = bpy.data.objects.new("AV_Root", None)
    bpy.context.scene.collection.objects.link(root)
    for o in roots:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
    bpy.context.view_layer.update()
    lo, hi = world_bounds(objs)
    h = hi.z - lo.z
    s = 1.0 / h if h > 1e-6 else 1.0
    c = (lo + hi) / 2
    # VRM 0.x blickt in glTF nach -Z (Blender +Y); unser Standard ist glTF +Z (Blender -Y)
    rot = Matrix.Rotation(math.pi if front_flip else 0.0, 4, "Z")
    root.matrix_world = rot @ Matrix.Scale(s, 4) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z)))
    bpy.context.view_layer.update()
    return root, h


def shrink_textures(maxpx):
    for img in bpy.data.images:
        if img.size[0] > maxpx or img.size[1] > maxpx:
            f = maxpx / max(img.size[0], img.size[1])
            img.scale(max(1, int(img.size[0] * f)), max(1, int(img.size[1] * f)))
        if not img.packed_file:
            try:
                img.pack()
            except Exception:
                pass


def export(path, root, objs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in [root] + objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_skins=True, export_animations=False,
                              export_cameras=False, export_lights=False, export_image_format="AUTO")


def bones(objs):
    for o in objs:
        if o.type == "ARMATURE":
            return [b.name for b in o.data.bones]
    return []


def render_sheet(entries, sheet, samples):
    """Alle exportierten GLBs in einer Reihe/Gitter aufstellen und rendern."""
    reset()
    sc = bpy.context.scene
    cols = 11
    gap = 0.9
    for k, e in enumerate(entries):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=e["glb"])
        new = [o for o in bpy.data.objects if o not in before]
        holder = bpy.data.objects.new("H%d" % k, None)
        sc.collection.objects.link(holder)
        for o in new:
            if o.parent is None:
                o.parent = holder
        r, c = divmod(k, cols)
        holder.location = (c * gap - (cols - 1) * gap / 2, r * 1.6, 0)
        cu = bpy.data.curves.new("T%d" % k, "FONT")
        cu.body = e["id"] + " " + e["name"][:12]
        cu.size = 0.09
        cu.align_x = "CENTER"
        t = bpy.data.objects.new("T%d" % k, cu)
        sc.collection.objects.link(t)
        t.location = (holder.location.x, holder.location.y - 0.35, 0.01)
        mt = bpy.data.materials.new("txt%d" % k)
        mt.use_nodes = True
        mt.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 1, 1, 1)
        mt.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0
        cu.materials.append(mt)
    rows = (len(entries) + cols - 1) // cols
    floor = bpy.data.meshes.new("F")
    floor.from_pydata([(-20, -5, 0), (20, -5, 0), (20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new("F", floor)
    sc.collection.objects.link(fo)
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.25, 0.28, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = w
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy = 3.0
    so = bpy.data.objects.new("S", sun)
    so.rotation_euler = (math.radians(50), 0, math.radians(-25))
    sc.collection.objects.link(so)
    cam = bpy.data.cameras.new("C")
    cam.type = "ORTHO"
    cam.ortho_scale = cols * gap + 0.6
    co = bpy.data.objects.new("C", cam)
    sc.collection.objects.link(co)
    mid_y = (rows - 1) * 1.6 / 2
    co.location = (0, mid_y - 9.0, 6.0 + 0.0)
    d = Vector((0, mid_y, 0.45)) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.resolution_x = 2200
    sc.render.resolution_y = int(2200 * (rows * 1.6 * 0.62 + 0.8) / (cols * gap + 0.6))
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 85
    sc.render.filepath = sheet
    bpy.ops.render.render(write_still=True)
    log("Uebersicht: " + sheet)


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.abspath("build/av_tmp")
    os.makedirs(tmp, exist_ok=True)
    entries = []
    for line in open(a.list):
        rel = line.strip()
        if not rel:
            continue
        base = os.path.basename(rel)[:-4]                 # 100Avatars_002_CoolAlien
        parts = base.split("_", 2)
        nr, name = parts[1], parts[2] if len(parts) > 2 else parts[1]
        src = os.path.join(a.src, rel)
        if not os.path.isfile(src):
            log("fehlt: " + rel)
            continue
        t = time.time()
        reset()
        objs = import_one(src, tmp)
        root, h = normalize(objs, front_flip=True)
        shrink_textures(a.tex)
        out = os.path.join(a.out, "club_av_%s.glb" % nr)
        export(out, root, objs)
        tris = sum(len(o.data.polygons) for o in objs if o.type == "MESH")
        e = {"id": nr, "name": name, "glb": out, "bytes": os.path.getsize(out), "orig_height": round(h, 3),
             "polys": tris, "bones": bones(objs), "meshes": sum(1 for o in objs if o.type == "MESH")}
        entries.append(e)
        log("%s %-16s %5d KB  %5d Polys  %d Knochen  %.1fs" % (nr, name, e["bytes"] // 1024, tris, len(e["bones"]), time.time() - t))
    json.dump(entries, open(os.path.join(a.out, "avatars.json"), "w"), indent=1)
    if a.sheet:
        render_sheet(entries, a.sheet, a.samples)


if __name__ == "__main__":
    main()
