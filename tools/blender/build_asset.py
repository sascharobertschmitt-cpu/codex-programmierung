"""
Generischer Blender-Build fuer Club-Assets (Geometrie-Modul mit build()).

Aufruf (headless, Blender 4.2 LTS):
  blender -b --factory-startup --python-exit-code 1 \
      -P tools/blender/build_asset.py -- \
      --geometry speaker_geometry \
      --out aal-you-ready/play/assets/club_speaker_pa212.glb \
      --tex-dir build/textures --preview-dir aal-you-ready/play/assets/previews \
      --report aal-you-ready/play/assets/previews/ayr212_build_report.json

Ablauf:
 1. Texturen (Normal Maps, Lochblech, Gebrauchsspuren) per numpy erzeugen, als PNG speichern
 2. Geometrie aus dem Geometrie-Modul als Meshes anlegen (1 Mesh pro Material)
 3. Gehaeuse: Bevel + Boolean-Ausschnitte + Weighted Normals, dann einfrieren
 4. PBR-Materialien (Principled BSDF, glTF-kompatibel) zuweisen
 5. GLB exportieren (Y oben, Front +Z, Ursprung Bodenmitte)
 6. Optional: Cycles-Vorschaubilder rendern
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import assetlib  # noqa: E402
import importlib  # noqa: E402

import speaker_geometry as family  # noqa: E402  (gemeinsame Konstanten: UV-Massstaebe)

ASSET = "ASSET"   # wird in main() aus der Geometrie gesetzt
TEXTURED = {"M_Cabinet", "M_Grille", "M_Cone"}


def log(msg):
    print(f"[{ASSET}] {msg}", flush=True)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", required=True, help="Python-Modul mit build(), z. B. sub_geometry")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tex-dir", default="build/textures")
    ap.add_argument("--preview-dir", default="")
    ap.add_argument("--report", default="")
    ap.add_argument("--samples", type=int, default=64)
    return ap.parse_args(argv)


# ---------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def make_textures(tex_dir):
    os.makedirs(tex_dir, exist_ok=True)
    paths = {
        "grain_n": os.path.join(tex_dir, f"{ASSET.lower()}_grain_normal.png"),
        "grille_c": os.path.join(tex_dir, f"{ASSET.lower()}_grille_color.png"),
        "grille_n": os.path.join(tex_dir, f"{ASSET.lower()}_grille_normal.png"),
    }
    assetlib.write_png(paths["grain_n"], assetlib.texture_grain_normal(256))
    color, normal = assetlib.texture_grille(256)
    assetlib.write_png(paths["grille_c"], color)
    assetlib.write_png(paths["grille_n"], normal)
    orm, base = assetlib.texture_wear(512)
    paths["wear_orm_n"] = os.path.join(tex_dir, f"{ASSET.lower()}_wear_orm.png")   # _n: Non-Color
    paths["wear_base"] = os.path.join(tex_dir, f"{ASSET.lower()}_wear_base.png")
    assetlib.write_png(paths["wear_orm_n"], orm)
    assetlib.write_png(paths["wear_base"], base)
    imgs = {}
    for key, p in paths.items():
        img = bpy.data.images.load(p, check_existing=False)
        img.name = os.path.basename(p)
        if key.endswith("_n"):
            img.colorspace_settings.name = "Non-Color"
        imgs[key] = img
        log(f"Textur {os.path.basename(p)}: {os.path.getsize(p) / 1024:.0f} KB")
    return imgs


def uv_node(nt, uv_name, loc):
    n = nt.nodes.new("ShaderNodeUVMap")
    n.uv_map = uv_name
    n.location = loc
    return n


def make_material(name, base, metallic, roughness, normal_img=None, normal_strength=1.0,
                  color_img=None, alpha_from_image=False, double_sided=False,
                  rough_img=None, wear_uv=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = not double_sided      # exportiert als glTF doubleSided
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if color_img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = color_img
        tex.location = (-500, 300)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if wear_uv:
            nt.links.new(uv_node(nt, wear_uv, (-800, 300)).outputs["UV"], tex.inputs["Vector"])
        if alpha_from_image:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "DITHERED"
            else:
                m.blend_method = "CLIP"
    if rough_img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = rough_img
        tex.location = (-700, 50)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-400, 50)
        nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        if wear_uv:
            nt.links.new(uv_node(nt, wear_uv, (-900, 50)).outputs["UV"], tex.inputs["Vector"])
    if normal_img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = normal_img
        tex.location = (-700, -200)
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal_strength
        nmap.location = (-300, -200)
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def make_materials(imgs):
    # Basisfarben linear. Bewusst nicht reines Schwarz (0.0), sonst wirkt PBR "tot".
    return {
        "M_Cabinet": make_material("M_Cabinet", (0.020, 0.020, 0.022), 0.0, 0.62,
                                   imgs["grain_n"], 0.45, color_img=imgs["wear_base"],
                                   rough_img=imgs["wear_orm_n"], wear_uv="UVWear"),
        "M_Grille": make_material("M_Grille", (0.03, 0.03, 0.03), 0.35, 0.42,
                                  imgs["grille_n"], 1.0, color_img=imgs["grille_c"],
                                  alpha_from_image=True, double_sided=True),
        "M_MetalDark": make_material("M_MetalDark", (0.045, 0.045, 0.05), 0.85, 0.38),
        "M_Steel": make_material("M_Steel", (0.62, 0.62, 0.64), 1.0, 0.28),
        "M_Rubber": make_material("M_Rubber", (0.014, 0.014, 0.014), 0.0, 0.55),
        "M_Cone": make_material("M_Cone", (0.028, 0.028, 0.03), 0.0, 0.88,
                                imgs["grain_n"], 0.5),
        "M_DustCap": make_material("M_DustCap", (0.02, 0.02, 0.022), 0.0, 0.22),
        "M_Horn": make_material("M_Horn", (0.016, 0.016, 0.018), 0.0, 0.36, double_sided=True),
        "M_Panel": make_material("M_Panel", (0.40, 0.40, 0.42), 1.0, 0.45),
    }


def part_to_object(part, coll, material=None):
    me = bpy.data.meshes.new(part.name)
    verts = [tuple(v) for v in part.verts]
    me.from_pydata(verts, [], part.faces)
    me.polygons.foreach_set("use_smooth", part.smooth)
    if material is None or part.material in TEXTURED:
        uv = me.uv_layers.new(name="UVMap")
        uvs = part.box_uvs()
        uv.data.foreach_set("uv", [c for xy in uvs for c in xy])
    if material is not None:
        me.materials.append(material)
    me.update()
    obj = bpy.data.objects.new(part.name, me)
    coll.objects.link(obj)
    return obj


def box_uv_mesh(me, scale, layer="UVMap"):
    """Box-Projektion direkt auf ein Mesh (erhaelt eigene Normalen)."""
    if layer not in me.uv_layers:
        me.uv_layers.new(name=layer)
    uv = me.uv_layers[layer].data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = (p.y if n.x > 0 else -p.y), p.z
            elif ax == 1:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            else:
                u, v = p.x, (p.y if n.z > 0 else -p.y)
            uv[li].uv = (u * scale, v * scale)


def build_cabinet(spec, coll, mat):
    cab = part_to_object(spec["cabinet"], coll)
    bev = cab.modifiers.new("Bevel", "BEVEL")
    bev.width = spec["bevel"]
    bev.segments = 4
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(30)
    bev.harden_normals = True
    bev.use_clamp_overlap = True

    cut_coll = bpy.data.collections.new("Cutters")
    bpy.context.scene.collection.children.link(cut_coll)
    for c in spec["cutters"]:
        o = part_to_object(c, cut_coll)
        o.hide_render = True
    boo = cab.modifiers.new("Cutouts", "BOOLEAN")
    boo.operation = "DIFFERENCE"
    boo.solver = "EXACT"
    boo.operand_type = "COLLECTION"
    boo.collection = cut_coll
    # Hard-Surface-Shading: grosse Flaechen bleiben plan, Fasen weich (auch nach Boolean)
    wn = cab.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.mode = "FACE_AREA"
    wn.weight = 50
    wn.keep_sharp = True

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = cab.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.name = f"{ASSET}_Cabinet"
    me.materials.clear()
    me.materials.append(mat)
    me.polygons.foreach_set("material_index", [0] * len(me.polygons))
    box_uv_mesh(me, family.UV_CAB)
    box_uv_mesh(me, family.UV_WEAR, "UVWear")
    me.update()

    # Hilfsobjekte entfernen
    old = cab.data
    bpy.data.objects.remove(cab)
    bpy.data.meshes.remove(old)
    for o in list(cut_coll.objects):
        m = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(m)
    bpy.data.collections.remove(cut_coll)

    obj = bpy.data.objects.new(f"{ASSET}_Cabinet", me)
    coll.objects.link(obj)
    if len(me.polygons) < 50:
        raise RuntimeError("Gehaeuse nach Bevel/Boolean unerwartet leer")
    return obj


def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_asset(imgs, spec):
    mats = make_materials(imgs)
    coll = bpy.data.collections.new(ASSET)
    bpy.context.scene.collection.children.link(coll)

    root = bpy.data.objects.new(ASSET, None)
    root.empty_display_size = 0.3
    coll.objects.link(root)

    objs = [build_cabinet(spec, coll, mats["M_Cabinet"])]
    for part in spec["parts"]:
        objs.append(part_to_object(part, coll, mats[part.material]))
    for o in objs:
        o.parent = root
    return root, objs, spec


def export_glb(path, root, objs):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in [root] + objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_cameras=False,
        export_lights=False,
    )
    if not os.path.isfile(path) or os.path.getsize(path) < 1000:
        raise RuntimeError(f"GLB-Export fehlgeschlagen: {path}")


# ---------------------------------------------------------------------------
# Vorschau (nur zur visuellen Kontrolle, wird NICHT exportiert)
# ---------------------------------------------------------------------------
def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def add_area(name, loc, target, power, size, color):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = power
    light.size = size
    light.color = color
    o = bpy.data.objects.new(name, light)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    return o


def render_previews(outdir, samples, shots):
    scene = bpy.context.scene
    os.makedirs(outdir, exist_ok=True)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    try:
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception as e:  # pragma: no cover
        log(f"Denoiser nicht verfuegbar: {e}")
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.006, 1)
    scene.world = world

    floor_me = bpy.data.meshes.new("PreviewFloor")
    floor_me.from_pydata([(-6, -6, 0), (6, -6, 0), (6, 6, 0), (-6, 6, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("PreviewFloor", floor_me)
    scene.collection.objects.link(floor)
    fm = bpy.data.materials.new("PreviewConcrete")
    fm.use_nodes = True
    b = fm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.035, 0.035, 0.038, 1)
    b.inputs["Roughness"].default_value = 0.55
    floor_me.materials.append(fm)

    tgt = (0, 0, 0.5)
    add_area("Key", (-1.6, -2.0, 2.0), tgt, 170, 1.2, (1.0, 0.95, 0.9))
    add_area("Fill", (2.2, -1.2, 0.9), tgt, 35, 1.5, (0.85, 0.9, 1.0))
    add_area("RimMagenta", (1.4, 1.8, 1.8), tgt, 160, 0.6, (1.0, 0.15, 0.7))
    add_area("RimCyan", (-1.6, 1.4, 1.2), tgt, 110, 0.6, (0.1, 0.8, 1.0))

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    shots = {f"{ASSET.lower()}_{k}.jpg": v for k, v in shots.items()}
    out = []
    for fname, (loc, target) in shots.items():
        cam.location = loc
        look_at(cam, target)
        scene.render.filepath = os.path.join(outdir, fname)
        t = time.time()
        bpy.ops.render.render(write_still=True)
        log(f"Vorschau {fname} in {time.time() - t:.1f}s")
        out.append(scene.render.filepath)
    return out


# ---------------------------------------------------------------------------
def main():
    global ASSET
    args = parse_args()
    t0 = time.time()
    log(f"Blender {bpy.app.version_string}")
    reset_scene()
    spec = importlib.import_module(args.geometry).build()
    ASSET = spec["name"]
    imgs = make_textures(args.tex_dir)
    root, objs, spec = build_asset(imgs, spec)

    stats = {o.name: {"triangles": tri_count(o), "vertices": len(o.data.vertices),
                      "material": o.data.materials[0].name if o.data.materials else None}
             for o in objs}
    total = sum(s["triangles"] for s in stats.values())
    for n, s in stats.items():
        log(f"{n:24s} {s['triangles']:6d} Dreiecke  {s['material']}")
    log(f"Summe: {total} Dreiecke, {len(objs)} Meshes")

    export_glb(args.out, root, objs)
    size = os.path.getsize(args.out)
    log(f"GLB geschrieben: {args.out} ({size / 1024:.0f} KB)")

    previews = []
    if args.preview_dir:
        previews = render_previews(args.preview_dir, args.samples, spec["shots"])

    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump({
                "asset": ASSET,
                "blender": bpy.app.version_string,
                "glb": args.out,
                "glb_bytes": size,
                "triangles_total": total,
                "meshes": stats,
                "dims_m": spec["dims"],
                "previews": previews,
                "seconds": round(time.time() - t0, 1),
            }, fh, indent=2)
    log(f"Fertig in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
