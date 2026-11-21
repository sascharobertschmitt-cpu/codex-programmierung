"""Aal You Ready? - modular, rigged player character (toy style) -> GLB.

Run (headless, bpy module or blender binary):
    python tools/character/character_build.py [out.glb] [--preview dir]

One GLB holds the rigged base body plus every optional part. The game switches
parts on/off by mesh name and tints materials by name:

  Base_*                always visible (Skin / Primary / Secondary / Shoe / Face)
  Hair_1..5             hairstyles          (0 = bald = none visible)
  Outfit_1..5_*         outfit parts        (0 = T-shirt = Base only + Outfit_0_*)
  Hat_1..5, Glasses_1..3, Acc_1..5
Materials (tinted at runtime): M_Skin M_Hair M_Primary M_Secondary M_Accent
Animations: Idle, Walk, Cheer.

Conventions (see skills/club-3d-asset-pipeline): meters, Z up, front = -Y,
origin at the floor between the feet. Export Y-up => front +Z.
"""
import math
import sys
import bpy
import bmesh
from mathutils import Vector

OUT = 'aal_character.glb'
PREVIEW = None
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == '--preview':
        PREVIEW = args[i + 1]
        i += 2
    else:
        OUT = args[i]
        i += 1

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

# ---------------------------------------------------------------- materials
def mk(name, color, rough=.55, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    m.diffuse_color = (*color, 1)
    return m

def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c)

MAT = {
    'M_Skin': mk('M_Skin', hexc('#e8b98f'), .6),
    'M_Hair': mk('M_Hair', hexc('#4a2f1c'), .45),
    'M_Primary': mk('M_Primary', hexc('#ff7a1a'), .6),
    'M_Secondary': mk('M_Secondary', hexc('#3b4a6b'), .65),
    'M_Accent': mk('M_Accent', hexc('#e4a324'), .5),
    'M_Shoe': mk('M_Shoe', hexc('#26282e'), .5),
    'M_Eye': mk('M_Eye', hexc('#0b0c10'), .15),
    'M_White': mk('M_White', hexc('#f4f4f4'), .5),
    'M_Mouth': mk('M_Mouth', hexc('#8a2f3a'), .5),
    'M_Dark': mk('M_Dark', hexc('#1c1d22'), .45),
    'M_Gold': mk('M_Gold', hexc('#ffcf3a'), .25, .9),
    'M_Visor': mk('M_Visor', hexc('#00cfe8'), .2, 0, hexc('#00e8ff'), 2.0),
}

# ---------------------------------------------------------------- helpers
_objs = []

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

def ell(name, loc, rad, mat, rot=(0, 0, 0), seg=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = rad
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.data.materials.append(MAT[mat])
    smooth(o)
    return o

def cyl(name, loc, r, h, mat, seg=24, rot=(0, 0, 0), r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, radius2=r if r2 is None else r2,
                                    depth=h, location=loc, end_fill_type='NGON')
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # soften the edges
    bv = o.modifiers.new('bv', 'BEVEL')
    bv.width = min(r, h) * .12
    bv.segments = 2
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='bv')
    o.data.materials.append(MAT[mat])
    smooth(o)
    return o

def tor(name, loc, major, minor, mat, rot=(0, 0, 0), seg=28, mseg=8):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=major, minor_radius=minor,
                                     major_segments=seg, minor_segments=mseg)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.data.materials.append(MAT[mat])
    smooth(o)
    return o

def cut(o, keep):
    """Delete vertices for which keep(co) is False."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    mw = o.matrix_world
    kill = [v for v in bm.verts if not keep(mw @ v.co)]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    return o

def solid(o, t=.012):
    m = o.modifiers.new('sol', 'SOLIDIFY')
    m.thickness = t
    m.offset = 1
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='sol')
    smooth(o)
    return o

def join(name, objs):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    return o

# ---------------------------------------------------------------- armature
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm_obj = bpy.context.active_object
arm_obj.name = 'Rig'
arm = arm_obj.data
arm.name = 'RigData'
eb = arm.edit_bones
eb.remove(eb[0])

def bone(name, head, parent=None):
    b = eb.new(name)
    b.head = head
    b.tail = (head[0], head[1], head[2] + .06)  # always point up => local axes == world axes
    b.roll = 0
    if parent:
        b.parent = eb[parent]
    return b

bone('Hips', (0, 0, .30))
bone('Spine', (0, 0, .31), 'Hips')
bone('Head', (0, 0, .57), 'Spine')
bone('ArmL', (-.165, 0, .52), 'Spine')
bone('ArmR', (.165, 0, .52), 'Spine')
bone('LegL', (-.075, 0, .28), 'Hips')
bone('LegR', (.075, 0, .28), 'Hips')
bpy.ops.object.mode_set(mode='OBJECT')

SK = {}  # bone -> list of objects

def bind(bn, o):
    SK.setdefault(bn, []).append(o)
    vg = o.vertex_groups.new(name=bn)
    vg.add([v.index for v in o.data.vertices], 1.0, 'REPLACE')
    return o

def part(name, items):
    """items: list of (bone, object). Joins them into one skinned mesh."""
    objs = []
    for bn, o in items:
        bind(bn, o)
        objs.append(o)
    o = join(name, objs)
    # materials: dedupe slots
    o.parent = arm_obj
    mod = o.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm_obj
    _objs.append(o)
    return o

# ---------------------------------------------------------------- base body
HEAD_C = (0, 0, .745)
def head_sphere():
    return ell('head', HEAD_C, (.205, .19, .195), 'M_Skin', seg=32, rings=20)

base_skin = [
    ('Head', head_sphere()),
    ('Head', ell('earL', (-.198, 0, .735), (.032, .03, .04), 'M_Skin', seg=12, rings=8)),
    ('Head', ell('earR', (.198, 0, .735), (.032, .03, .04), 'M_Skin', seg=12, rings=8)),
    ('Head', ell('nose', (0, -.186, .722), (.022, .02, .02), 'M_Skin', seg=12, rings=8)),
    ('Head', ell('neck', (0, 0, .575), (.065, .06, .05), 'M_Skin', seg=12, rings=8)),
    ('ArmL', ell('armLs', (-.19, 0, .43), (.042, .042, .105), 'M_Skin', seg=16, rings=10)),
    ('ArmR', ell('armRs', (.19, 0, .43), (.042, .042, .105), 'M_Skin', seg=16, rings=10)),
    ('ArmL', ell('handL', (-.19, 0, .315), (.05, .05, .052), 'M_Skin', seg=16, rings=10)),
    ('ArmR', ell('handR', (.19, 0, .315), (.05, .05, .052), 'M_Skin', seg=16, rings=10)),
]
part('Base_Skin', base_skin)

part('Base_Primary', [('Spine', ell('torso', (0, 0, .43), (.152, .115, .155), 'M_Primary', seg=28, rings=16))])
part('Base_Secondary', [
    ('Hips', ell('pelvis', (0, 0, .29), (.135, .10, .085), 'M_Secondary', seg=24, rings=12)),
    ('LegL', ell('legLs', (-.07, 0, .165), (.055, .055, .115), 'M_Secondary', seg=16, rings=10)),
    ('LegR', ell('legRs', (.07, 0, .165), (.055, .055, .115), 'M_Secondary', seg=16, rings=10)),
])
part('Base_Shoe', [
    ('LegL', ell('shoeL', (-.07, -.025, .04), (.062, .105, .048), 'M_Shoe', seg=16, rings=10)),
    ('LegR', ell('shoeR', (.07, -.025, .04), (.062, .105, .048), 'M_Shoe', seg=16, rings=10)),
])

# face: eyes, highlights, mouth
mouth = tor('mouth', (0, -.178, .685), .038, .0085, 'M_Mouth', rot=(math.pi / 2, 0, 0), seg=20, mseg=6)
cut(mouth, lambda c: c.z < .685 - .004)  # keep the lower half => smile
part('Base_Face', [
    ('Head', ell('eyeL', (-.075, -.17, .76), (.032, .02, .048), 'M_Eye', seg=16, rings=10)),
    ('Head', ell('eyeR', (.075, -.17, .76), (.032, .02, .048), 'M_Eye', seg=16, rings=10)),
    ('Head', ell('hlL', (-.067, -.186, .778), (.011, .008, .014), 'M_White', seg=8, rings=6)),
    ('Head', ell('hlR', (.083, -.186, .778), (.011, .008, .014), 'M_White', seg=8, rings=6)),
    ('Head', mouth),
])

# ---------------------------------------------------------------- hair (M_Hair)
def hair_cap(top=.835, lift=.012):
    o = ell('cap', (0, .012, HEAD_C[2] + lift), (.222, .212, .21), 'M_Hair', seg=32, rings=20)
    cut(o, lambda c: not (c.y < -.085 and c.z < top) and c.z > .60 and not (c.y < -.03 and c.z < .70))
    return solid(o, .012)

part('Hair_1', [('Head', hair_cap())])
curls = []
import random
rnd = random.Random(7)
for k in range(15):
    a = k / 15 * math.tau
    rr = .165 if k % 2 else .13
    zc = .83 + (k % 3) * .02
    y = math.cos(a) * rr + .01
    x = math.sin(a) * rr
    if y < -.09 and zc < .86:
        continue
    curls.append(('Head', ell('curl%d' % k, (x, y, zc), (.07, .07, .065), 'M_Hair', seg=12, rings=8)))
curls.append(('Head', ell('curlTop', (0, 0, .9), (.1, .1, .07), 'M_Hair', seg=12, rings=8)))
part('Hair_2', curls)
moh = []
for k in range(6):
    yy = -.1 + k * .05
    hh = .11 + (.06 if k in (2, 3) else 0)
    moh.append(('Head', ell('moh%d' % k, (0, yy, .87 + hh * .55), (.04, .05, hh), 'M_Hair', seg=10, rings=8)))
part('Hair_3', moh)
part('Hair_4', [
    ('Head', hair_cap()),
    ('Head', ell('tail', (0, .215, .73), (.06, .07, .15), 'M_Hair', rot=(.35, 0, 0), seg=14, rings=10)),
    ('Head', ell('tie', (0, .185, .81), (.04, .04, .04), 'M_Accent', seg=10, rings=6)),
])
part('Hair_5', [
    ('Head', hair_cap()),
    ('Head', ell('back', (0, .115, .68), (.215, .105, .27), 'M_Hair', seg=20, rings=12)),
    ('Head', ell('lockL', (-.195, .01, .66), (.04, .06, .14), 'M_Hair', seg=12, rings=8)),
    ('Head', ell('lockR', (.195, .01, .66), (.04, .06, .14), 'M_Hair', seg=12, rings=8)),
])

# ---------------------------------------------------------------- hats
def dome(r, z, flat=1.0, zmin=None):
    o = ell('dome', (0, .005, z), (r, r * .97, r * flat), 'M_Accent', seg=28, rings=16)
    zm = zmin if zmin is not None else z
    cut(o, lambda c: c.z > zm)
    return o

capd = dome(.232, .80, .85, .822)
part('Hat_1', [
    ('Head', solid(capd, .008)),
    ('Head', ell('brim', (0, -.215, .826), (.125, .115, .014), 'M_Accent', rot=(-.12, 0, 0), seg=20, rings=8)),
])
bean = dome(.235, .775, 1.0, .80)
bean.data.materials.clear()
bean.data.materials.append(MAT['M_Accent'])
part('Hat_2', [
    ('Head', solid(bean, .012)),
    ('Head', tor('cuff', (0, .005, .80), .222, .026, 'M_White', seg=28, mseg=8)),
    ('Head', ell('pom', (0, .005, .995), (.055, .055, .055), 'M_White', seg=12, rings=8)),
])
part('Hat_3', [
    ('Head', cyl('hatTop', (0, 0, .985), .12, .24, 'M_Dark', seg=28)),
    ('Head', cyl('hatBrim', (0, 0, .875), .215, .024, 'M_Dark', seg=32)),
    ('Head', cyl('hatBand', (0, 0, .915), .123, .045, 'M_Accent', seg=28)),
])
crown = [('Head', tor('crownRing', (0, 0, .93), .12, .024, 'M_Gold', seg=24, mseg=8))]
for k in range(5):
    a = k / 5 * math.tau
    crown.append(('Head', cyl('spike%d' % k, (math.cos(a) * .12, math.sin(a) * .12, .985), .035, .1, 'M_Gold', seg=10, r2=.004)))
part('Hat_4', crown)
band = tor('hpBand', (0, 0, .745), .215, .014, 'M_Dark', rot=(math.pi / 2, 0, 0), seg=36, mseg=8)
cut(band, lambda c: c.z > .745)
part('Hat_5', [
    ('Head', band),
    ('Head', cyl('cupL', (-.215, 0, .735), .062, .052, 'M_Accent', seg=20, rot=(0, math.pi / 2, 0))),
    ('Head', cyl('cupR', (.215, 0, .735), .062, .052, 'M_Accent', seg=20, rot=(0, math.pi / 2, 0))),
])

# ---------------------------------------------------------------- glasses
part('Glasses_1', [
    ('Head', tor('gl', (-.075, -.185, .765), .05, .008, 'M_Dark', rot=(math.pi / 2, 0, 0), seg=24, mseg=6)),
    ('Head', tor('gr', (.075, -.185, .765), .05, .008, 'M_Dark', rot=(math.pi / 2, 0, 0), seg=24, mseg=6)),
    ('Head', ell('gb', (0, -.188, .775), (.03, .008, .008), 'M_Dark', seg=8, rings=6)),
])
part('Glasses_2', [
    ('Head', ell('sl', (-.075, -.186, .762), (.058, .012, .045), 'M_Dark', seg=14, rings=8)),
    ('Head', ell('sr', (.075, -.186, .762), (.058, .012, .045), 'M_Dark', seg=14, rings=8)),
    ('Head', ell('sb', (0, -.186, .78), (.1, .01, .01), 'M_Dark', seg=10, rings=6)),
])
part('Glasses_3', [('Head', ell('visor', (0, -.18, .762), (.15, .028, .05), 'M_Visor', seg=20, rings=10))])

# ---------------------------------------------------------------- outfits (parts shown on top of Base_Primary / Base_Secondary)
def sleeves(prefix, long_):
    z, rz = (.43, .108) if long_ else (.485, .06)
    return [('ArmL', ell(prefix + 'sL', (-.19, 0, z), (.05, .05, rz), 'M_Primary', seg=16, rings=10)),
            ('ArmR', ell(prefix + 'sR', (.19, 0, z), (.05, .05, rz), 'M_Primary', seg=16, rings=10))]

part('Outfit_0', sleeves('t', False))
part('Outfit_1', sleeves('h', True) + [
    ('Spine', ell('hood', (0, .09, .585), (.13, .075, .085), 'M_Primary', seg=16, rings=10)),
    ('Spine', ell('pocket', (0, -.108, .37), (.095, .02, .05), 'M_Accent', seg=14, rings=8)),
])
part('Outfit_2', [
    ('Spine', ell('jacket', (0, 0, .435), (.16, .121, .16), 'M_Dark', seg=28, rings=16)),
    ('ArmL', ell('jsL', (-.19, 0, .43), (.051, .051, .108), 'M_Dark', seg=16, rings=10)),
    ('ArmR', ell('jsR', (.19, 0, .43), (.051, .051, .108), 'M_Dark', seg=16, rings=10)),
    ('LegL', ell('jlL', (-.07, 0, .165), (.059, .059, .118), 'M_Dark', seg=16, rings=10)),
    ('LegR', ell('jlR', (.07, 0, .165), (.059, .059, .118), 'M_Dark', seg=16, rings=10)),
    ('Spine', ell('shirt', (0, -.095, .46), (.045, .03, .105), 'M_White', seg=12, rings=8)),
    ('Spine', ell('tie', (0, -.123, .43), (.02, .012, .085), 'M_Accent', seg=10, rings=8)),
])
part('Outfit_3', sleeves('j', True) + [
    ('Spine', ell('stripeF', (0, -.108, .43), (.02, .02, .14), 'M_White', seg=10, rings=8)),
])
part('Outfit_4', sleeves('d', False) + [
    ('Hips', cyl('skirt', (0, 0, .235), .215, .2, 'M_Primary', seg=32, r2=.13)),
])
part('Outfit_5', sleeves('o', False) + [
    ('Spine', ell('bib', (0, -.1, .405), (.105, .03, .105), 'M_Secondary', seg=16, rings=10)),
    ('Spine', ell('strapL', (-.075, -.095, .515), (.022, .028, .075), 'M_Secondary', seg=10, rings=6)),
    ('Spine', ell('strapR', (.075, -.095, .515), (.022, .028, .075), 'M_Secondary', seg=10, rings=6)),
    ('Spine', ell('button1', (-.075, -.12, .475), (.014, .01, .014), 'M_Gold', seg=8, rings=6)),
    ('Spine', ell('button2', (.075, -.12, .475), (.014, .01, .014), 'M_Gold', seg=8, rings=6)),
])
# make the T-shirt-type sleeves use Primary (dress/overall sleeves too); suits use M_Dark.

# ---------------------------------------------------------------- accessories
part('Acc_1', [
    ('Spine', ell('bag', (0, .15, .44), (.115, .07, .14), 'M_Accent', seg=18, rings=10)),
    ('Spine', ell('bagPocket', (0, .215, .39), (.075, .02, .06), 'M_Dark', seg=12, rings=8)),
    ('Spine', ell('bagStrapL', (-.085, -.06, .5), (.018, .06, .085), 'M_Dark', rot=(.0, 0, 0), seg=10, rings=6)),
    ('Spine', ell('bagStrapR', (.085, -.06, .5), (.018, .06, .085), 'M_Dark', seg=10, rings=6)),
])
part('Acc_2', [
    ('Spine', tor('scarf', (0, 0, .575), .115, .04, 'M_Accent', seg=24, mseg=10)),
    ('Spine', ell('scarfTail', (.06, -.1, .5), (.04, .022, .095), 'M_Accent', rot=(0, .12, 0), seg=12, rings=8)),
])
part('Acc_3', [
    ('Spine', ell('bowL', (-.045, -.112, .575), (.04, .022, .03), 'M_Accent', seg=12, rings=8)),
    ('Spine', ell('bowR', (.045, -.112, .575), (.04, .022, .03), 'M_Accent', seg=12, rings=8)),
    ('Spine', ell('knot', (0, -.114, .575), (.018, .018, .018), 'M_Accent', seg=8, rings=6)),
])
part('Acc_4', [
    ('Spine', tor('chain', (0, -.018, .5), .125, .009, 'M_Gold', rot=(.35, 0, 0), seg=28, mseg=6)),
    ('Spine', ell('pendant', (0, -.128, .43), (.028, .014, .028), 'M_Gold', seg=12, rings=8)),
])
part('Acc_5', [
    ('Spine', ell('cape', (0, .125, .42), (.175, .026, .235), 'M_Accent', rot=(.14, 0, 0), seg=20, rings=12)),
    ('Spine', ell('clasp', (0, -.02, .575), (.03, .02, .02), 'M_Gold', seg=8, rings=6)),
])

# ---------------------------------------------------------------- animation
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')
pb = arm_obj.pose.bones
for b in pb:
    b.rotation_mode = 'XYZ'
FPS = 30
scene.render.fps = FPS

def action(name, frames, keys):
    """keys: {bone: {'rotation_euler': [(frame,(x,y,z))...], 'location': [...]}}"""
    act = bpy.data.actions.new(name)
    arm_obj.animation_data_create()
    arm_obj.animation_data.action = act
    for bn, chans in keys.items():
        for path, pts in chans.items():
            for f, v in pts:
                if path == 'rotation_euler':
                    pb[bn].rotation_euler = v
                else:
                    pb[bn].location = v
                pb[bn].keyframe_insert(path, frame=f)
    # reset pose for the next action
    for b in pb:
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
    act.use_fake_user = True
    return act

def cyc(n, fn, lo=0):
    return [(f, fn(f / n)) for f in range(lo, n + 1)]

TAU = math.tau
W = 26  # walk cycle frames (two steps) -> .867 s
sw = lambda t, ph=0, a=.7: math.sin(TAU * t + ph) * a
action('Walk', W, {
    'LegL': {'rotation_euler': cyc(W, lambda t: (sw(t), 0, 0))},
    'LegR': {'rotation_euler': cyc(W, lambda t: (sw(t, math.pi), 0, 0))},
    'ArmL': {'rotation_euler': cyc(W, lambda t: (sw(t, math.pi, .6), 0, .05))},
    'ArmR': {'rotation_euler': cyc(W, lambda t: (sw(t, 0, .6), 0, -.05))},
    'Hips': {'location': cyc(W, lambda t: (0, 0, abs(math.sin(TAU * t)) * .018 - .008))},
    'Spine': {'rotation_euler': cyc(W, lambda t: (0, 0, math.sin(TAU * t) * .08))},
    'Head': {'rotation_euler': cyc(W, lambda t: (0, 0, -math.sin(TAU * t) * .05))},
})
I = 60
action('Idle', I, {
    'Spine': {'rotation_euler': cyc(I, lambda t: (math.sin(TAU * t) * .02, 0, 0))},
    'Head': {'rotation_euler': cyc(I, lambda t: (math.sin(TAU * t + 1) * .03, 0, math.sin(TAU * t) * .05))},
    'ArmL': {'rotation_euler': cyc(I, lambda t: (0, 0, .05 + math.sin(TAU * t) * .03))},
    'ArmR': {'rotation_euler': cyc(I, lambda t: (0, 0, -.05 - math.sin(TAU * t) * .03))},
    'Hips': {'location': cyc(I, lambda t: (0, 0, math.sin(TAU * t) * .006))},
})
C = 24
action('Cheer', C, {
    'ArmL': {'rotation_euler': cyc(C, lambda t: (0, 0, -(2.55 + math.sin(TAU * t * 2) * .35)))},
    'ArmR': {'rotation_euler': cyc(C, lambda t: (0, 0, 2.55 + math.sin(TAU * t * 2) * .35))},
    'Hips': {'location': cyc(C, lambda t: (0, 0, abs(math.sin(TAU * t)) * .06))},
    'Head': {'rotation_euler': cyc(C, lambda t: (-.15, 0, math.sin(TAU * t) * .15))},
    'LegL': {'rotation_euler': cyc(C, lambda t: (abs(math.sin(TAU * t)) * -.3, 0, 0))},
    'LegR': {'rotation_euler': cyc(C, lambda t: (abs(math.sin(TAU * t)) * -.3, 0, 0))},
})
bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.animation_data.action = None
# sleeves/legs: cheering arm values are signed per side (see above): left arm lifts toward -X.

# ---------------------------------------------------------------- stats + export
tris = 0
for o in _objs:
    me = o.data
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
print('PARTS', len(_objs), 'TRIS', tris)

bpy.ops.object.select_all(action='DESELECT')
arm_obj.select_set(True)
for o in _objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.export_scene.gltf(
    filepath=OUT, export_format='GLB', use_selection=True, export_yup=True,
    export_apply=False, export_skins=True, export_animations=True,
    export_animation_mode='ACTIONS', export_force_sampling=True,
    export_image_format='NONE', export_materials='EXPORT',
    export_extras=False,
)
print('WROTE', OUT)

# ---------------------------------------------------------------- optional preview renders (Cycles CPU)
if PREVIEW:
    import os
    os.makedirs(PREVIEW, exist_ok=True)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 520
    scene.render.resolution_y = 700
    scene.world = bpy.data.worlds.new('w')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.06, .07, .09, 1)
    bpy.ops.object.light_add(type='AREA', location=(-1.4, -2.2, 2.2))
    L = bpy.context.active_object
    L.data.energy = 220
    L.data.size = 2.5
    L.rotation_euler = (math.radians(55), 0, math.radians(-30))
    bpy.ops.object.light_add(type='AREA', location=(1.8, -1.4, 1.2))
    L2 = bpy.context.active_object
    L2.data.energy = 80
    L2.data.size = 2
    L2.rotation_euler = (math.radians(70), 0, math.radians(40))
    bpy.ops.object.camera_add(location=(0, -3.0, .62))
    cam = bpy.context.active_object
    cam.data.lens = 70
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam
    keep = {'Base_Skin', 'Base_Primary', 'Base_Secondary', 'Base_Shoe', 'Base_Face'}

    def show(names):
        for o in _objs:
            vis = o.name in keep or o.name in names
            o.hide_render = not vis
    shots = {
        'plain': [], 'hoodie_cap': ['Outfit_1', 'Hair_1', 'Hat_1'],
        'suit': ['Outfit_2', 'Hair_5', 'Hat_3', 'Glasses_2', 'Acc_3'],
        'dress': ['Outfit_4', 'Hair_4', 'Acc_5', 'Glasses_1'],
        'overall': ['Outfit_5', 'Hair_2', 'Hat_2', 'Acc_1'],
        'punk': ['Outfit_3', 'Hair_3', 'Glasses_3', 'Acc_4', 'Hat_5'],
    }
    for k, names in shots.items():
        show(names)
        scene.render.filepath = os.path.join(PREVIEW, k + '.png')
        bpy.ops.render.render(write_still=True)
    print('PREVIEWS', PREVIEW)
