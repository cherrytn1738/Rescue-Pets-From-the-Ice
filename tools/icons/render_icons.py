"""render_icons.py - the 3D half of the store and game icons (headless Blender, EEVEE).

Renders each icon's subject on a transparent background at 1024x1024, in one or more layers (back to
front), for tools/icons/compose_icons.py to put on a background with outlines, glows, sparkles and text.
Usually run through compose_icons.py (--render), which calls Blender for you:

    python tools/icons/compose_icons.py --render                 # everything
    python tools/icons/compose_icons.py --render VIP LuckyIce    # some icons

By hand (Blender 5.x; the newest under C:\\Program Files\\Blender Foundation\\):
    blender -b --factory-startup --python tools/icons/render_icons.py -- picks  <work dir>
    blender -b --factory-startup --python tools/icons/render_icons.py -- render <work dir> <IconName>
    blender -b --factory-startup --python tools/icons/render_icons.py -- ui     <work dir> <Key>
    blender -b --factory-startup --python tools/icons/render_icons.py -- tools  <work dir>

  picks   builds the six ice pick tiers from tools/blender/tools_ice_picks.py (its geometry, nothing is
          written to store-assets/tools/) into <work>/picks.blend, which the icon scenes append from.
  tools   builds the 18 tools from tools/blender/tools_tiers.py (its geometry, nothing is written to
          store-assets/tools/) into <work>/tools.blend and their head points into <work>/tools.json (the UI
          icons Tool1-Tool18 append from it).
  render  renders one icon into <work>/<IconName>/: <layer>.png per layer and meta.json (the layer order
          plus a few projected 2D points, e.g. the pick's pivot for the motion arcs).
  ui      the same for one in-game UI icon (compose_icons.py --ui) into <work>/ui/<Key>/.

What it uses: the game's own creature models (store-assets/creatures/<Id>/<Id>.blend, posed with their
own Idle/Cheer clips), the pick tiers, and two simple props made here: the ice block (a bevelled
translucent cube with crack lines, a frosted top, an optional rarity glow and a dark creature silhouette
inside) and the crystal (a faceted neon-cyan gem). Nothing is uploaded anywhere.
Axes as in the pet files: metres, Z up, the pets face -Y; the camera sits on the -Y side.
"""
import bpy, bmesh, math, os, sys, random, json
import numpy as np
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CREATURES = os.path.join(REPO, 'store-assets', 'creatures')
STUD_PNG = os.path.join(REPO, 'tools', 'pets', 'voxel', 'roblox_square_studs.png')
RES = 1024

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = argv[0] if argv else 'render'
WORK = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.join(REPO, 'tmp', 'icons')
NAMES = argv[2:]

# the Cheer frame each pet's own preview uses (tools/pets/creatures/<Id>.py, PREVIEW shots)
CHEER = {'ArcticFoxKit': 18, 'AuroraFox': 15, 'CrystalStag': 16, 'FrostDragonHatchling': 20, 'FrostMouse': 19,
         'FrostTurtle': 16, 'GlacierOtter': 10, 'IceHedgehog': 18, 'IceWolfPup': 16, 'MiniYeti': 17, 'PenguinChick': 17,
         'PolarBearCub': 17, 'PuffinPal': 17, 'SealPup': 13, 'SnowBunny': 21, 'SnowPhoenix': 19, 'SnowyOwlet': 18,
         'SpiritWhale': 14}
CRYSTAL = (120, 230, 255)          # the in-game crystal colour
GOLD = (255, 196, 60)


def lin(c):
    """sRGB 0-255 (or hex) -> linear RGBA"""
    if isinstance(c, str):
        c = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 if x / 255 > 0.04045 else x / 255 / 12.92 for x in c) + (1.0,)


def direction(yaw, pitch):
    """unit vector from the target toward a camera/light at this yaw (0 = in front, -Y) and pitch (degrees)"""
    y, p = math.radians(yaw), math.radians(pitch)
    return Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))


# ---------------------------------------------------------------- the ice picks (mode "picks")

def build_picks():
    src = open(os.path.join(REPO, 'tools', 'blender', 'tools_ice_picks.py'), encoding='utf-8').read()
    src = src.replace('\nbuild_picks()\n', '\n')          # use its geometry; don't write its sheet / fbx
    g = {'REPO': REPO, '__name__': 'tools_ice_picks', '__file__': os.path.join(REPO, 'tools', 'blender', 'tools_ice_picks.py')}
    exec(compile(src, 'tools_ice_picks.py', 'exec'), g)
    g['SCENE_NAME'] = 'B_IcePicks'
    scene = g['fresh_scene']()
    image = bpy.data.images.get('BuildingPalette') or bpy.data.images.load(os.path.join(REPO, 'assets', 'textures', 'BuildingPalette.png'))
    g['MATERIALS'] = g['palette_materials'](image)
    for tier in range(1, 7):
        g['Q'].update({'round': 1.0, 'minor': 1.0, 'corner': 2, 'edge': 2, 'bevel': 2, 'tiny': 0.6})
        b = g['Builder']('IcePickT%d' % tier, g['coll_in'](scene, 'Pick %d' % tier))
        g['pick'](b, tier)
        b.finish()
    image.pack()
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'picks.blend'))


def build_tools():
    src = open(os.path.join(REPO, 'tools', 'blender', 'tools_tiers.py'), encoding='utf-8').read()
    src = src.replace('\nbuild_tools()\n', '\n')          # use its geometry; don't write its sheets / fbx
    g = {'REPO': REPO, '__name__': 'tools_tiers', '__file__': os.path.join(REPO, 'tools', 'blender', 'tools_tiers.py')}
    exec(compile(src, 'tools_tiers.py', 'exec'), g)
    g['SCENE_NAME'] = 'B_Tools'
    scene = g['fresh_scene']()
    image = bpy.data.images.get('BuildingPalette') or bpy.data.images.load(os.path.join(REPO, 'assets', 'textures', 'BuildingPalette.png'))
    g['MATERIALS'] = g['palette_materials'](image)
    heads = {}
    for tier, look in sorted(g['TOOLS'].items()):
        g['Q'].update({'round': 1.0, 'minor': 1.0, 'corner': 2, 'edge': 2, 'bevel': 2, 'tiny': 0.6})
        b = g['Builder']('ToolT%d' % tier, g['coll_in'](scene, 'Tool %d' % tier))
        atts = g['FAMILY_BUILD'][look['family']](b, tier, look)
        b.finish()
        a, z = atts['TrailA'].translation, atts['TrailB'].translation
        heads[tier] = list((a + z) / 2)     # the middle of the striking part: the icon's glow sits behind it
    image.pack()
    os.makedirs(WORK, exist_ok=True)
    json.dump(heads, open(os.path.join(WORK, 'tools.json'), 'w'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tools.blend'))


# ---------------------------------------------------------------- scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for e in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = e
            break
        except TypeError:
            pass
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    sc.eevee.taa_render_samples = 96
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.62, 0.74, 0.95, 1)
    bg.inputs['Strength'].default_value = 0.85
    return sc


def lights(yaw, key=3.6, rim=4.5, fill=1.3):
    """key from above the camera's left, a strong rim from behind, a soft fill from the right"""
    for name, (dy, dp), energy, color in (('Key', (-35, 48), key, (1.0, 0.98, 0.94)),
                                          ('Rim', (165, 38), rim, (0.85, 0.95, 1.0)),
                                          ('Fill', (70, 12), fill, (0.9, 0.95, 1.0))):
        L = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN'))
        bpy.context.scene.collection.objects.link(L)
        L.data.energy, L.data.color = energy, color
        L.data.angle = math.radians(8)
        L.rotation_euler = (-direction(yaw + dy, dp)).to_track_quat('-Z', 'Y').to_euler()


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def world_points(objs):
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type != 'MESH' or o.hide_render:
            continue
        oe = o.evaluated_get(deps)
        me = oe.to_mesh()
        M = oe.matrix_world.copy()
        pts += [M @ v.co for v in me.vertices]
        oe.to_mesh_clear()
    return pts


# ---------------------------------------------------------------- creatures

_templates = {}


def creature_template(name):
    if name not in _templates:
        path = os.path.join(CREATURES, name, name + '.blend')
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            act_names = [str(n) for n in src.actions]
            dst.objects = [n for n in src.objects if n in (name, name + 'Rig')]
            dst.actions = list(act_names)
        rig = next(o for o in dst.objects if o.type == 'ARMATURE')
        mesh = next(o for o in dst.objects if o.type == 'MESH')
        acts = {n.split('_', 1)[1]: a for n, a in zip(act_names, dst.actions)}
        for img in bpy.data.images:
            if 'roblox_square_studs' in img.name.lower() and os.path.exists(STUD_PNG):
                img.filepath = STUD_PNG
                img.reload()
        _templates[name] = (rig, mesh, acts)
    return _templates[name]


_silhouette = None


def silhouette_material():
    global _silhouette
    if _silhouette is None:
        m = bpy.data.materials.new('Silhouette')     # flat dark navy, unlit, like the in-game silhouette
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'BSDF_PRINCIPLED':
                nt.nodes.remove(n)
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = lin('121a30')
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])
        _silhouette = m
    return _silhouette


def add_pet(name, loc=(0, 0, 0), yaw=0.0, size=1.0, clip='Idle', frame=0, silhouette=False, tilt=(0.0, 0.0)):
    """A posed copy of a game creature. size = its biggest dimension (height or length), like the game's
    3-stud pets; the pet stands on loc (its own z = 0 is the ground)."""
    rig0, mesh0, acts = creature_template(name)
    rig = link(rig0.copy())
    ob = link(mesh0.copy())
    ob.parent = rig
    ob.matrix_parent_inverse = Matrix()
    ob.matrix_basis = Matrix()
    ob.modifiers['Armature'].object = rig
    rig.location, rig.rotation_euler, rig.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    if clip == 'Cheer' and frame is None:
        frame = CHEER.get(name, 18)
    rig.animation_data_create()
    act = acts[clip]
    rig.animation_data.action = act
    try:
        if rig.animation_data.action_slot is None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    except AttributeError:
        pass
    bpy.context.scene.frame_set(int(frame or 0))
    pose = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = pose[pb.name]
    bpy.context.view_layer.update()
    pts = world_points([ob])
    h = max(p.z for p in pts) - min(min(p.z for p in pts), 0.0)
    d = max(p.y for p in pts) - min(p.y for p in pts)
    s = size / max(h, d)
    rig.scale = (s, s, s)
    rig.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(yaw))
    rig.location = loc
    if silhouette:
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = silhouette_material()
    bpy.context.view_layer.update()
    return ob


# ---------------------------------------------------------------- the ice block

def crack_image(name, seed, amount=1.0, res=1024):
    """white branching crack lines on black (numpy), used as a mask on the ice faces"""
    rng = random.Random(seed)
    a = np.zeros((res, res), np.float32)
    yy, xx = np.mgrid[-8:9, -8:9]
    dist = np.sqrt(xx * xx + yy * yy)

    def stamp(x, y, w, v):
        x, y = int(x), int(y)
        if not (8 <= x < res - 8 and 8 <= y < res - 8):
            return
        disc = np.clip(w + 0.5 - dist, 0, 1) * v
        np.maximum(a[y - 8:y + 9, x - 8:x + 9], disc, out=a[y - 8:y + 9, x - 8:x + 9])

    def ray(x, y, ang, length, w, depth):
        travelled = 0.0
        while travelled < length and w > 0.8:
            step = rng.uniform(30, 70)
            ang += rng.uniform(-0.35, 0.35)
            nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
            n = int(step / 1.5) + 1
            for i in range(n + 1):
                t = i / n
                px, py = x + (nx - x) * t, y + (ny - y) * t
                stamp(px, py, w + 2.2, 0.35)       # soft frosty edge
                stamp(px, py, w, 1.0)               # bright core
            x, y = nx, ny
            travelled += step
            w *= 0.9
            if depth < 1 and rng.random() < 0.22:
                ray(x, y, ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0), length * 0.4, w * 0.75, depth + 1)

    centres = [(0.32, 0.3), (0.7, 0.68), (0.72, 0.25)][:1 + int(round(2 * amount))]
    for cx, cy in centres:
        x, y = (cx + rng.uniform(-0.06, 0.06)) * res, (cy + rng.uniform(-0.06, 0.06)) * res
        n = rng.randint(5, 6)
        for k in range(n):
            ray(x, y, k * math.tau / n + rng.uniform(-0.35, 0.35), res * rng.uniform(0.22, 0.42) * (0.6 + 0.5 * amount), 4.2, 0)
    img = bpy.data.images.new(name, res, res, alpha=True)
    img.colorspace_settings.name = 'Non-Color'      # before the pixels: changing it later reloads (blanks) the image
    px = np.ones((res, res, 4), np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = a
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def _rainbow_ramp(nt, fac_socket):
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cols = ['ff4d6d', 'ffa43a', 'fff04a', '5dff7a', '3ff2ff', '5a7dff', 'c45cff', 'ff4d6d']
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, lin(cols[0])
    el[1].position, el[1].color = 1.0, lin(cols[-1])
    for i, c in enumerate(cols[1:-1], 1):
        e = el.new(i / (len(cols) - 1))
        e.color = lin(c)
    nt.links.new(fac_socket, ramp.inputs['Fac'])
    return ramp.outputs['Color']


def _math(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new('ShaderNodeMath')
    m.operation = op
    m.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def ice_material(name, glow=None, glow_strength=0.35, cracks=0.6, seed=1, alpha=0.38, tint=(40, 160, 235),
                 inner=(25, 115, 225), inner_alpha=0.88):
    """translucent pale-blue ice: whiter, more opaque edges, a frosted top, white crack lines;
    glow = None, an (r, g, b) colour or 'rainbow' (tints the ice and makes it glow)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    for attr, val in (('surface_render_method', 'DITHERED'), ('blend_method', 'HASHED')):
        try:
            setattr(m, attr, val)
            break
        except (AttributeError, TypeError):
            pass
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    P = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    tc = N.new('ShaderNodeTexCoord')
    lw = N.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.25
    edge = lw.outputs['Facing']
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Normal'], sep.inputs[0])
    frost = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', sep.outputs['Z'], 0.55, clamp=True), 2.4, clamp=True)
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.5
    L.new(tc.outputs['Object'], noise.inputs['Vector'])
    cloud = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', noise.outputs['Fac'], 0.47, clamp=True), 0.6)
    crack = 0.0
    if cracks > 0:
        tex = N.new('ShaderNodeTexImage')
        tex.image = crack_image(name + 'Cracks', seed, cracks)
        tex.projection = 'BOX'
        tex.projection_blend = 0.15
        L.new(tc.outputs['Generated'], tex.inputs['Vector'])
        crack = tex.outputs['Color']
    white = _math(nt, 'MAXIMUM', _math(nt, 'MAXIMUM', _math(nt, 'MULTIPLY', frost, 0.7), _math(nt, 'MULTIPLY', edge, 0.8)), cloud)
    if cracks > 0:
        white = _math(nt, 'MAXIMUM', white, crack)
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = lin(tint)
    mix.inputs[7].default_value = lin((225, 250, 255))
    L.new(white, mix.inputs['Factor'])
    colour = mix.outputs[2]
    # the ice's colour comes mostly from emission (the scene's bright pet lighting would bleach it to white);
    # a dim diffuse keeps some shading between the faces
    dim = N.new('ShaderNodeVectorMath')
    dim.operation = 'SCALE'
    dim.inputs['Scale'].default_value = 0.16
    L.new(colour, dim.inputs[0])
    L.new(dim.outputs[0], P.inputs['Base Color'])
    a = _math(nt, 'ADD', _math(nt, 'ADD', alpha, _math(nt, 'MULTIPLY', edge, 0.7)), _math(nt, 'ADD', _math(nt, 'MULTIPLY', frost, 0.4), _math(nt, 'MULTIPLY', cloud, 0.4)), clamp=True)
    if cracks > 0:
        a = _math(nt, 'ADD', a, crack, clamp=True)
    # coverage is an explicit mix with a Transparent BSDF (Principled's own Alpha came out far too opaque)
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    tr = N.new('ShaderNodeBsdfTransparent')
    ms = N.new('ShaderNodeMixShader')
    L.new(a, ms.inputs['Fac'])
    L.new(tr.outputs[0], ms.inputs[1])
    L.new(P.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs['Surface'])
    P.inputs['Roughness'].default_value = 0.12
    for k, v in (('Coat Weight', 0.6), ('Specular IOR Level', 0.8)):
        if k in P.inputs:
            P.inputs[k].default_value = v
    # the inside walls (back faces) are a deeper, nearly opaque blue: through the near faces the block then
    # reads as blue ice (not the icon background), with the dark silhouette and the glow in front of them
    inner_col = N.new('ShaderNodeMix')
    inner_col.data_type = 'RGBA'
    inner_col.inputs[6].default_value = lin(inner)
    inner_col.inputs[7].default_value = lin((150, 220, 255))
    L.new(_math(nt, 'MULTIPLY', crack, 0.7) if cracks > 0 else _math(nt, 'MULTIPLY', cloud, 0.0), inner_col.inputs['Factor'])
    back = geo.outputs['Backfacing']

    def tinted(src, k):
        if not glow:
            return src
        gm = N.new('ShaderNodeMix')
        gm.data_type = 'RGBA'
        gm.inputs['Factor'].default_value = glow_strength * k
        L.new(src, gm.inputs[6])
        if glow == 'rainbow':
            sg = N.new('ShaderNodeSeparateXYZ')
            L.new(tc.outputs['Generated'], sg.inputs[0])
            fac = _math(nt, 'FRACT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', sg.outputs['X'], 0.45), _math(nt, 'MULTIPLY', sg.outputs['Z'], 0.75)))
            L.new(_rainbow_ramp(nt, fac), gm.inputs[7])
        else:
            gm.inputs[7].default_value = lin(glow)
        return gm.outputs[2]

    emit = N.new('ShaderNodeMix')
    emit.data_type = 'RGBA'
    L.new(back, emit.inputs['Factor'])
    L.new(tinted(colour, 1.0), emit.inputs[6])
    L.new(tinted(inner_col.outputs[2], 0.8 if glow == 'rainbow' else 0.35), emit.inputs[7])
    L.new(emit.outputs[2], P.inputs['Emission Color'])
    L.new(emit.outputs[2], dim.inputs[0])
    P.inputs['Emission Strength'].default_value = 0.8
    a_mix = N.new('ShaderNodeMix')
    a_mix.data_type = 'FLOAT'
    L.new(back, a_mix.inputs['Factor'])
    L.new(a, a_mix.inputs[2])
    a_mix.inputs[3].default_value = inner_alpha
    L.new(a_mix.outputs[0], ms.inputs['Fac'])
    m.use_backface_culling = not inner_alpha
    return m


def glow_material(name, color, strength=4.0, falloff=1.2):
    """a soft glowing orb: bright in the middle, fading to nothing at its edges"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    for attr, val in (('surface_render_method', 'DITHERED'), ('blend_method', 'HASHED')):
        try:
            setattr(m, attr, val)
            break
        except (AttributeError, TypeError):
            pass
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED':
            N.remove(n)
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    em = N.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    tc = N.new('ShaderNodeTexCoord')
    sg = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Generated'], sg.inputs[0])
    gx = _math(nt, 'SUBTRACT', sg.outputs['X'], 0.5)
    gy = _math(nt, 'SUBTRACT', sg.outputs['Y'], 0.5)
    if color == 'rainbow':      # hue goes round the disc
        ang = _math(nt, 'ADD', _math(nt, 'DIVIDE', _math(nt, 'ARCTAN2', gy, gx), math.tau), 0.5)
        L.new(_rainbow_ramp(nt, ang), em.inputs['Color'])
    else:
        em.inputs['Color'].default_value = lin(color)
    dist = _math(nt, 'MULTIPLY', _math(nt, 'SQRT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', gx, gx), _math(nt, 'MULTIPLY', gy, gy))), 2.0)
    centre = _math(nt, 'POWER', _math(nt, 'SUBTRACT', 1.0, dist, clamp=True), falloff)
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(centre, mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def ice_block(loc=(0, 0, 0), size=(1.0, 1.0, 1.25), yaw=0.0, glow=None, glow_strength=0.35, cracks=0.6, seed=1,
              alpha=0.38, pet=None, pet_size=0.8, pet_yaw=-20, pet_clip='Idle', pet_frame=0, orb=None, orb_strength=4.0,
              view=(-25, 20), inner=(25, 115, 225), name='IceBlock'):
    """the in-game ice block: returns the list of its objects (cube, optional glow orb, optional silhouette)"""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, sz / 2)) @ Matrix.Diagonal((sx, sy, sz, 1)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = link(bpy.data.objects.new(name, me))
    bev = ob.modifiers.new('Bevel', 'BEVEL')
    bev.width = 0.07 * min(sx, sy, sz)
    bev.segments = 3
    try:
        bev.harden_normals = True
    except AttributeError:
        pass
    me.materials.append(ice_material(name + 'Ice', glow, glow_strength, cracks, seed, alpha, inner=inner))
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(yaw))
    made = [ob]
    centre = Vector(loc) + Vector((0, 0, sz * 0.5))
    if orb:     # the rarity glow: a soft glowing disc facing the camera, behind the silhouette
        d = direction(*view)
        bm = bmesh.new()
        r = max(sx, sz) * 0.5
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=r)
        me2 = bpy.data.meshes.new(name + 'Orb')
        bm.to_mesh(me2)
        bm.free()
        o = link(bpy.data.objects.new(name + 'Orb', me2))
        o.location = centre - d * (min(sx, sy) * 0.3)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        me2.materials.append(glow_material(name + 'OrbGlow', orb, orb_strength))
        made.append(o)
    if pet:
        pet_ob = add_pet(pet, loc=(loc[0], loc[1], loc[2] + 0.06 * sz), yaw=yaw + pet_yaw, size=pet_size * min(sx, sz),
                         clip=pet_clip, frame=pet_frame, silhouette=True)
        # centre the silhouette in the block
        pts = world_points([pet_ob])
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        shift = centre - (lo + hi) / 2
        pet_ob.parent.location = Vector(pet_ob.parent.location) + shift
        bpy.context.view_layer.update()
        made.append(pet_ob)
    return made


def shard(loc, size, seed, mat, stretch=1.8, rot=None):
    """a broken piece of ice: the convex hull of a few random points, flat shaded (rot in radians, or random)"""
    rng = random.Random(seed)
    bm = bmesh.new()
    for _ in range(9):
        v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if v.length < 0.2:
            continue
        v = v.normalized() * rng.uniform(0.7, 1.0)
        bm.verts.new((v.x * 0.5 * size, v.y * 0.35 * size, v.z * 0.5 * size * stretch))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new('Shard')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = link(bpy.data.objects.new('Shard', me))
    ob.location = loc
    ob.rotation_euler = rot if rot is not None else (rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28))
    return ob


def broken_rim(sx, sy, top, mat, seed, count=12, height=0.42):
    """jagged ice spikes standing round the top edge of a block that has burst open"""
    rng = random.Random(seed)
    made = []
    perim = 2 * (sx + sy)
    for i in range(count):
        u = (i + rng.uniform(-0.25, 0.25)) / count * perim
        if u < sx:
            x, y, out = -sx / 2 + u, -sy / 2, (0, -1)
        elif u < sx + sy:
            x, y, out = sx / 2, -sy / 2 + (u - sx), (1, 0)
        elif u < 2 * sx + sy:
            x, y, out = sx / 2 - (u - sx - sy), sy / 2, (0, 1)
        else:
            x, y, out = -sx / 2, sy / 2 - (u - 2 * sx - sy), (-1, 0)
        x, y = x * 0.9, y * 0.9
        h = height * rng.uniform(0.6, 1.15)
        tilt = math.radians(rng.uniform(15, 35))
        rot = (-out[1] * tilt, out[0] * tilt, 0.0)
        made.append(shard((x, y, top + h * 0.35), h / 1.9, seed * 100 + i, mat, stretch=1.9, rot=rot))
    return made


# ---------------------------------------------------------------- crystals

_gem = {}


def gem_material():
    if 'mat' not in _gem:
        m = bpy.data.materials.new('Crystal')
        m.use_nodes = True
        P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        P.inputs['Base Color'].default_value = lin((0, 165, 225))     # deeper than the neon colour so the facets read under the bright lights
        P.inputs['Roughness'].default_value = 0.12
        P.inputs['Emission Color'].default_value = lin(CRYSTAL)
        P.inputs['Emission Strength'].default_value = 0.06
        for k, v in (('Coat Weight', 0.0), ('Specular IOR Level', 0.6)):
            if k in P.inputs:
                P.inputs[k].default_value = v
        _gem['mat'] = m
    return _gem['mat']


def gem_mesh():
    """a six-sided crystal: pointed top and bottom, a short straight band in the middle, flat facets"""
    if 'mesh' not in _gem:
        bm = bmesh.new()
        top = bm.verts.new((0, 0, 0.72))
        bot = bm.verts.new((0, 0, -0.62))
        r1 = [bm.verts.new((0.36 * math.cos(i * math.tau / 6), 0.36 * math.sin(i * math.tau / 6), 0.24)) for i in range(6)]
        r2 = [bm.verts.new((0.36 * math.cos(i * math.tau / 6), 0.36 * math.sin(i * math.tau / 6), -0.18)) for i in range(6)]
        for i in range(6):
            j = (i + 1) % 6
            bm.faces.new((top, r1[i], r1[j]))
            bm.faces.new((r1[j], r1[i], r2[i], r2[j]))
            bm.faces.new((bot, r2[j], r2[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new('Gem')
        bm.to_mesh(me)
        bm.free()
        me.materials.append(gem_material())
        _gem['mesh'] = me
    return _gem['mesh']


def gem(loc, size=0.3, rot=(0, 0, 0)):
    ob = link(bpy.data.objects.new('Crystal', gem_mesh()))
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = (size, size, size)
    return ob


def gem_pile(centre=(0, 0, 0), radius=1.0, height=0.7, size=0.3, seed=1, density=1.0):
    """a heap of crystals: gems spread over two nested dome surfaces (the inside never shows)"""
    rng = random.Random(seed)
    made = []
    cx, cy, cz = centre
    for layer, (rf, hf) in enumerate(((1.0, 1.0), (0.72, 0.8))):
        R, H = radius * rf, height * hf
        area = math.pi * (R * R + H * H)
        count = max(3, int(area / (size * size * 0.55) * density))
        for i in range(count):
            t = (i + 0.5) / count
            r = R * math.sqrt(t)
            a = i * 2.39996 + layer * 1.3 + rng.uniform(-0.2, 0.2)
            z = H * (1 - (r / R) ** 2) if R > 0 else H
            p = (cx + r * math.cos(a) + rng.uniform(-0.05, 0.05), cy + r * math.sin(a) + rng.uniform(-0.05, 0.05),
                 cz + max(z, 0) + size * 0.15 + rng.uniform(-0.06, 0.06))
            lean = 35 + 45 * (r / R) ** 2           # upright on top, lying over at the rim
            rot = (math.radians(rng.uniform(-lean, lean)), math.radians(rng.uniform(-lean, lean)), rng.uniform(0, math.tau))
            made.append(gem(p, size * rng.uniform(0.8, 1.25), rot))
    return made


def gem_burst(centre, radius, count, size, seed, up=1.0, spread=1.0):
    """crystals flying out of a point (an arc of gems above and around it)"""
    rng = random.Random(seed)
    made = []
    for i in range(count):
        a = math.radians(rng.uniform(-80, 80) * spread) + (math.pi / 2 if up else 0)
        r = radius * rng.uniform(0.75, 1.15)
        p = Vector(centre) + Vector((math.cos(a) * r, rng.uniform(-0.3, 0.1) * r, math.sin(a) * r * up))
        rot = (rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7), rng.uniform(0, 6.28))
        made.append(gem(p, size * rng.uniform(0.75, 1.2), rot))
    return made


# ---------------------------------------------------------------- picks

def add_pick(tier, loc, rot_deg, scale=1.0):
    path = os.path.join(WORK, 'picks.blend')
    prefix = 'IcePickT%d' % tier
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == prefix or (n.startswith(prefix) and not n[len(prefix):][:1].isdigit())]
    root = None
    for o in dst.objects:
        link(o)
        if o.type == 'EMPTY':
            root = o
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot_deg]
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return [o for o in dst.objects if o.type == 'MESH'], root


def add_tool(tier, loc, rot_deg, scale=1.0):
    path = os.path.join(WORK, 'tools.blend')
    prefix = 'ToolT%d' % tier
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == prefix or (n.startswith(prefix) and not n[len(prefix):][:1].isdigit())]
    root = None
    for o in dst.objects:
        link(o)
        if o.type == 'EMPTY':
            root = o
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot_deg]
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return [o for o in dst.objects if o.type == 'MESH'], root


# ---------------------------------------------------------------- camera + output

def camera(objs, yaw=-25, pitch=22, lens=60, fill=0.88, ortho=False, points=None, roll=0.0):
    """aim a camera from (yaw, pitch) and fit the objects (or explicit world points) to `fill` of the frame"""
    sc = bpy.context.scene
    cam = link(bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')))
    sc.camera = cam
    cam.data.clip_end = 500
    pts = points if points is not None else world_points([o for o in objs if 'Orb' not in o.name])
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    d = direction(yaw, pitch)
    radius = (hi - lo).length / 2
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = radius * 2
        dist = radius * 8 + 10
    else:
        cam.data.lens = lens
        dist = radius / math.tan(math.atan(18 / lens)) / fill
    q = (-d).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    for it in range(9):
        cam.location = c + d * dist
        cam.rotation_euler = q.to_euler()
        cam.data.shift_x = cam.data.shift_y = 0
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(sc, cam, p) for p in pts]
        xs, ys = [v.x for v in ndc], [v.y for v in ndc]
        if it == 8:
            break
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        if ortho:
            cam.data.ortho_scale *= span / fill
        else:
            dist *= span / fill
    cam.data.shift_x = (max(xs) + min(xs)) / 2 - 0.5
    cam.data.shift_y = (max(ys) + min(ys)) / 2 - 0.5
    bpy.context.view_layer.update()
    lights(yaw)
    return cam


def to_pixels(p):
    v = world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, Vector(p))
    return [round(v.x * RES, 1), round((1 - v.y) * RES, 1)]


def render_layers(icon, layers, points=None):
    """layers: [(name, [objects]) or (name, [objects], [holdouts])] back to front. Each renders alone (the
    others hidden); holdouts are drawn as holes, so a layer stays correct where those objects are nearer."""
    out = os.path.join(WORK, icon)
    os.makedirs(out, exist_ok=True)
    every = [o for layer in layers for o in layer[1]]
    sc = bpy.context.scene
    for layer in layers:
        name, objs = layer[0], layer[1]
        keep, holds = set(objs), set(layer[2] if len(layer) > 2 else ())
        for o in every:
            o.hide_render = o not in keep and o not in holds
            o.is_holdout = o in holds
        sc.render.filepath = os.path.join(out, name + '.png')
        bpy.ops.render.render(write_still=True)
    for o in every:
        o.hide_render = False
        o.is_holdout = False
    meta = {'layers': [layer[0] for layer in layers], 'points': {k: to_pixels(v) for k, v in (points or {}).items()}}
    json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'), indent=1)


def top_point(objs):
    pts = world_points(objs)
    zmax = max(p.z for p in pts)
    top = [p for p in pts if p.z > zmax - 0.04]
    return sum(top, Vector()) / len(top)


def bbox_points(lo, hi):
    return [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


# ---------------------------------------------------------------- the icons

def icon_DoubleCrystals():
    pile = gem_pile((0, 0, 0), 1.05, 0.62, 0.38, seed=3)
    hero = [gem((0.0, -0.2, 1.0), 0.85, (math.radians(8), math.radians(-12), math.radians(20)))]
    burst = gem_burst((0, -0.1, 0.65), 1.3, 8, 0.34, seed=11, spread=1.0)
    objs = pile + hero + burst
    camera(objs, yaw=-18, pitch=30, lens=55, fill=0.9)
    render_layers('DoubleCrystals', [('main', objs)])


def icon_AutoPick():
    block = ice_block((0, 0, 0), (1.0, 1.0, 0.82), cracks=0.9, seed=4, glow=None)
    chips = [shard((0.05 + 0.3 * i, -0.45, 1.0 + 0.2 * (i % 2)), 0.17, 40 + i, ice_material('Chip', cracks=0, alpha=0.62)) for i in range(3)]
    sparks = gem_burst((0.3, -0.3, 0.85), 0.55, 4, 0.16, seed=7, spread=0.7)
    picks, root = add_pick(4, (1.55, -0.2, 2.38), (0, -118, 0), 0.62)
    objs = block + chips + sparks + picks
    camera(objs, yaw=-14, pitch=20, lens=55, fill=0.9)
    pivot = root.matrix_world @ Vector((0, 0, 0.3))
    head = root.matrix_world @ Vector((0, 0, 3.15))
    render_layers('AutoPick', [('main', objs)], {'pivot': pivot, 'head': head})


def icon_VIP():
    pet = add_pet('SnowBunny', (0, 0, 0), yaw=-22, size=1.0, clip='Cheer', frame=CHEER['SnowBunny'])
    camera([pet], yaw=-10, pitch=12, lens=60, fill=0.9)
    render_layers('VIP', [('main', [pet])], {'head_top': top_point([pet])})


def icon_ExtraPetSlot():
    pet = add_pet('ArcticFoxKit', (0, 0, 0), yaw=-30, size=1.0, clip='Idle', frame=0)
    camera([pet], yaw=-8, pitch=14, lens=60, fill=0.9)
    render_layers('ExtraPetSlot', [('main', [pet])])


def icon_PetSquad():
    a = add_pet('PenguinChick', (-0.66, 0.2, 0), yaw=8, size=1.05, clip='Cheer', frame=CHEER['PenguinChick'])
    b = add_pet('PolarBearCub', (0.0, -0.35, 0), yaw=-18, size=1.0, clip='Idle', frame=0)
    c = add_pet('PuffinPal', (0.66, 0.2, 0), yaw=-30, size=1.05, clip='Cheer', frame=CHEER['PuffinPal'])
    camera([a, b, c], yaw=-8, pitch=14, lens=55, fill=0.92)
    render_layers('PetSquad', [('back', [a, c]), ('front', [b])])


def icon_LuckyIce():
    block = ice_block((0, 0, 0), (1.0, 1.0, 1.2), glow=None, cracks=0.45, seed=6,
                      pet='FrostDragonHatchling', pet_size=0.72, pet_yaw=-25, orb=(255, 214, 90), orb_strength=8.0, view=(-28, 20))
    camera(block, yaw=-28, pitch=20, lens=55, fill=0.86)
    render_layers('LuckyIce', [('main', block)])


def _pile_frame():
    return bbox_points((-1.35, -1.35, -0.1), (1.35, 1.35, 1.55))


def icon_CrystalPouch():
    objs = gem_pile((0, 0, 0), 0.62, 0.32, 0.34, seed=21, density=1.2)
    objs += [gem((0.02, -0.08, 0.55), 0.52, (math.radians(10), math.radians(-14), 0.3))]
    camera(objs, yaw=-18, pitch=32, lens=55, fill=0.92, points=_pile_frame())
    render_layers('CrystalPouch', [('main', objs)])


def icon_CrystalSack():
    objs = gem_pile((0, 0, 0), 0.95, 0.6, 0.32, seed=22)
    objs += [gem((0.0, -0.12, 0.9), 0.62, (math.radians(10), math.radians(-14), 0.3))]
    camera(objs, yaw=-18, pitch=32, lens=55, fill=0.92, points=_pile_frame())
    render_layers('CrystalSack', [('main', objs)])


def icon_CrystalChest():
    objs = gem_pile((0, 0, 0), 1.3, 0.95, 0.31, seed=23)
    objs += [gem((0.0, -0.2, 1.3), 0.7, (math.radians(10), math.radians(-14), 0.3))]
    objs += gem_burst((0, -0.2, 1.0), 0.75, 7, 0.24, seed=24)
    camera(objs, yaw=-18, pitch=32, lens=55, fill=0.92, points=_pile_frame())
    render_layers('CrystalChest', [('main', objs)])


def icon_GiantCrystalChest():
    objs = gem_pile((0, 0, 0), 1.45, 1.15, 0.30, seed=25, density=1.15)
    objs += [gem((0.0, -0.2, 1.5), 0.78, (math.radians(10), math.radians(-14), 0.3))]
    objs += gem_burst((0, -0.2, 1.15), 0.95, 11, 0.24, seed=26)
    camera(objs, yaw=-18, pitch=32, lens=55, fill=0.92, points=_pile_frame())
    render_layers('GiantCrystalChest', [('main', objs)])


def icon_ShatterNow():
    block = ice_block((0, 0, 0), (1.3, 1.3, 0.6), cracks=1.0, seed=9)
    mat = ice_material('ShardIce', cracks=0, alpha=0.5, tint=(120, 200, 245))
    pet = add_pet('MiniYeti', (-0.1, 0.0, -0.1), yaw=-14, size=1.75, clip='Cheer', frame=CHEER['MiniYeti'])
    rim = broken_rim(1.3, 1.3, 0.6, mat, seed=5, count=12, height=0.45)
    rng = random.Random(5)
    shards = []
    for i, deg in enumerate((-5, 15, 35, 55, 125, 145, 165, 185)):     # out to the sides, clear of the face
        a = math.radians(deg + rng.uniform(-6, 6))
        r = rng.uniform(1.0, 1.25)
        shards.append(shard((math.cos(a) * r - 0.1, rng.uniform(-0.2, 0.4), 0.7 + math.sin(a) * r * 0.95),
                            rng.uniform(0.22, 0.34), 100 + i, mat))
    gems = gem_burst((-0.1, 0.1, 1.2), 1.1, 4, 0.24, seed=13)
    picks, root = add_pick(4, (1.85, -0.45, 1.5), (0, -115, 0), 0.47)
    objs = block + rim + shards + gems + picks
    camera(objs + [pet], yaw=-10, pitch=15, lens=40, fill=0.94)
    render_layers('ShatterNow', [('pet', [pet]), ('ice', objs, [pet])])


def icon_ServerFrostRush():
    pets = [add_pet('PenguinChick', (-0.78, 0.2, 0), yaw=10, size=1.0, clip='Cheer', frame=CHEER['PenguinChick']),
            add_pet('IceWolfPup', (0.0, -0.3, 0), yaw=-32, size=1.1, clip='Idle', frame=0),
            add_pet('SealPup', (0.8, 0.2, 0), yaw=-30, size=1.0, clip='Cheer', frame=CHEER['SealPup'])]
    camera(pets, yaw=-6, pitch=14, lens=55, fill=0.92)
    render_layers('ServerFrostRush', [('pets', pets)])


def icon_MythicBlock():
    block = ice_block((0, 0, 0), (1.0, 1.0, 1.2), glow='rainbow', glow_strength=0.65, cracks=0.4, seed=12, inner=(80, 45, 200),
                      pet='SpiritWhale', pet_size=0.74, pet_yaw=-35, orb='rainbow', orb_strength=8.0, view=(-28, 20))
    camera(block, yaw=-28, pitch=20, lens=55, fill=0.86)
    render_layers('MythicBlock', [('main', block)])


def icon_MythicBlock3():
    # three Mythic Blocks: two behind, one in front, each with a dark silhouette inside
    left = ice_block((-0.95, 0.45, 0), (0.78, 0.78, 0.95), glow='rainbow', glow_strength=0.65, cracks=0.35, seed=31, inner=(80, 45, 200),
                     pet='AuroraFox', pet_size=0.6, pet_yaw=-20, orb='rainbow', orb_strength=7.0, view=(-28, 20))
    right = ice_block((0.95, 0.45, 0), (0.78, 0.78, 0.95), glow='rainbow', glow_strength=0.65, cracks=0.35, seed=32, inner=(80, 45, 200),
                      pet='SnowPhoenix', pet_size=0.6, pet_yaw=-40, orb='rainbow', orb_strength=7.0, view=(-28, 20))
    front = ice_block((0, -0.55, 0), (0.9, 0.9, 1.08), glow='rainbow', glow_strength=0.65, cracks=0.4, seed=12, inner=(80, 45, 200),
                      pet='SpiritWhale', pet_size=0.68, pet_yaw=-35, orb='rainbow', orb_strength=8.0, view=(-28, 20))
    camera(left + right + front, yaw=-12, pitch=18, lens=55, fill=0.88)
    render_layers('MythicBlock3', [('back', left + right), ('front', front)])


def icon_concept_1():
    block = ice_block((0, 0, 0), (1.45, 1.45, 0.75), cracks=1.0, seed=17)
    mat = ice_material('ShardIce', cracks=0, alpha=0.5, tint=(120, 200, 245))
    pet = add_pet('SnowBunny', (0, -0.05, -0.05), yaw=-14, size=1.85, clip='Cheer', frame=CHEER['SnowBunny'])
    rim = broken_rim(1.45, 1.45, 0.75, mat, seed=3, count=13, height=0.5)
    rng = random.Random(8)
    shards = []
    for i in range(8):
        a = math.radians(-5 + i * 190 / 7 + rng.uniform(-8, 8))
        r = rng.uniform(1.05, 1.3)
        shards.append(shard((math.cos(a) * r, rng.uniform(-0.6, 0.3), 0.75 + math.sin(a) * r * 1.0),
                            rng.uniform(0.2, 0.32), 200 + i, mat))
    gems = gem_burst((0, -0.3, 1.35), 1.15, 6, 0.28, seed=19, spread=1.15)
    objs = block + rim + shards + gems
    frame_pts = world_points([pet]) + bbox_points((-0.95, -0.9, 0.35), (0.95, 0.9, 1.0))
    camera(objs + [pet], yaw=-12, pitch=16, lens=40, fill=0.97, points=frame_pts)
    render_layers('icon_concept_1', [('pet', [pet]), ('ice', objs, [pet])])


def icon_concept_2():
    block = ice_block((0, 0, 0), (1.45, 1.25, 1.25), glow='rainbow', glow_strength=0.6, cracks=0.55, seed=27,
                      orb='rainbow', orb_strength=4.0, view=(-10, 16), alpha=0.55)
    pet = add_pet('PolarBearCub', (0.0, -0.1, 0.55), yaw=-14, size=1.3, clip='Idle', frame=0)
    gems = [gem((-0.92, -0.55, 1.55), 0.22, (0.4, 0.2, 0.3)), gem((0.9, -0.6, 1.8), 0.18, (0.1, 0.6, 0.2)),
            gem((-0.68, -0.65, 2.05), 0.15, (1.0, 0.3, 0.6))]
    frame_pts = world_points([pet]) + bbox_points((-0.72, -0.62, 0.3), (0.72, 0.62, 1.25))
    camera(block + [pet] + gems, yaw=-10, pitch=16, lens=50, fill=0.98, points=frame_pts)
    render_layers('icon_concept_2', [('back', block[1:]), ('pet', [pet]), ('front', [block[0]] + gems, [pet])])


def icon_concept_3():
    block = ice_block((0, 0.75, 0), (1.4, 1.1, 1.55), glow=None, cracks=0.6, seed=33,
                      pet='FrostDragonHatchling', pet_size=0.7, pet_yaw=-25, orb=(255, 214, 90), orb_strength=8.0, view=(-6, 12))
    picks, root = add_pick(4, (1.7, 0.3, 2.2), (0, -110, 0), 0.47)
    pets = [add_pet('PenguinChick', (-0.82, -0.45, 0), yaw=14, size=1.0, clip='Cheer', frame=CHEER['PenguinChick']),
            add_pet('SnowBunny', (0.0, -0.8, 0), yaw=-8, size=1.05, clip='Idle', frame=0),
            add_pet('ArcticFoxKit', (0.85, -0.45, 0), yaw=-32, size=1.05, clip='Cheer', frame=CHEER['ArcticFoxKit'])]
    camera(block + picks + pets, yaw=-6, pitch=12, lens=45, fill=0.95)
    render_layers('icon_concept_3', [('block', block + picks), ('pets', pets)])


ICONS = {k if k.startswith('icon_concept') else k[5:]: v for k, v in globals().items() if k.startswith('icon_') and callable(v)}


# ================================================================ UI icons (mode "ui")
# The in-game button and window icons: one subject each, no background or text (compose_icons.py --ui adds the
# outline, glow and sparkles). Layers go to <work>/ui/<Key>/. The buildings come from their own .blend files
# (store-assets/buildings/<Id>/<Id>.blend, the tier-1 "Scrappy" station); the other props are simple shapes made here.

BUILDINGS = os.path.join(REPO, 'store-assets', 'buildings')
BUILDING_IDS = ['IcePickPost', 'ChiselMill', 'IceDrill', 'HeatLamp', 'WreckingCrane', 'FlamethrowerTurret', 'LavaPump', 'SunMirrorTower']
BUILDING_VIEW = dict(yaw=-34, pitch=24, lens=50, fill=0.9)      # one camera for every building icon
PICK_ROT = (0, 38, -12)                                          # the picks lean right, head at the top
GREEN = (70, 215, 90)


def ui_out(key):
    return 'ui/' + key


def plastic(name, colour, rough=0.35, metal=0.0, emit=0.0, emit_colour=None, coat=0.3):
    """a plain toy-like material (sRGB 0-255 colour); emit adds a little self-light so it stays saturated"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    P.inputs['Base Color'].default_value = lin(colour)
    P.inputs['Roughness'].default_value = rough
    P.inputs['Metallic'].default_value = metal
    P.inputs['Emission Color'].default_value = lin(emit_colour or colour)
    P.inputs['Emission Strength'].default_value = emit
    if 'Coat Weight' in P.inputs:
        P.inputs['Coat Weight'].default_value = coat
    return m


def finish_mesh(name, bm, mats, bevel=0.0, smooth=True, segments=3):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = smooth
    ob = link(bpy.data.objects.new(name, me))
    if bevel:
        bev = ob.modifiers.new('Bevel', 'BEVEL')
        bev.width = bevel
        bev.segments = segments
        bev.limit_method = 'ANGLE'
        try:
            bev.harden_normals = True
        except AttributeError:
            pass
    return ob


def box_into(bm, size, loc=(0, 0, 0), rot=(0, 0, 0), mat_index=0):
    """add a box (size, centre loc, rot in degrees XYZ) to a bmesh"""
    M = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Diagonal(tuple(size) + (1,))
    ret = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    for f in {f for v in ret['verts'] for f in v.link_faces}:
        f.material_index = mat_index


def cyl_into(bm, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat_index=0, segments=20, radius2=None):
    """a cylinder (or a cone with radius2) along its local Z"""
    M = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                                radius2=radius if radius2 is None else radius2, depth=depth, matrix=M)
    for f in {f for v in ret['verts'] for f in v.link_faces}:
        f.material_index = mat_index


def boxes(name, parts, mats, bevel=0.05):
    """one object from [(size, loc, rot, material index)] boxes, bevelled"""
    bm = bmesh.new()
    for size, loc, rot, mi in parts:
        box_into(bm, size, loc, rot, mi)
    return finish_mesh(name, bm, mats, bevel)


def slab(name, outline, depth, mat, round_edge=0.06, loc=(0, 0, 0), rot=(90, 0, 0), scale=1.0, tube=False, radii=None):
    """a chunky flat shape: the 2D outline (x, y points, counter-clockwise) filled and made `depth` thick with
    rounded edges (a filled curve, turned into a mesh). rot (degrees) stands it up: the default faces -Y.
    tube=True instead runs a round tube of radius round_edge along the (open) outline."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D' if tube else '2D'
    sp = cu.splines.new('POLY')
    pts = [tuple(p) + ((0.0,) if len(p) == 2 else ()) for p in outline]
    sp.points.add(len(pts) - 1)
    for i, (p, xyz) in enumerate(zip(sp.points, pts)):
        p.co = (xyz[0], xyz[1], xyz[2], 1.0)
        if radii:
            p.radius = radii[i]
    if tube:
        cu.bevel_depth = round_edge
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
    else:
        sp.use_cyclic_u = True
        cu.fill_mode = 'BOTH'
        cu.extrude = max(depth / 2 - round_edge, 0.001)
        cu.bevel_depth = round_edge
        cu.bevel_resolution = 3
    tmp = link(bpy.data.objects.new(name + 'Curve', cu))
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return ob


def arrow_outline(w=0.5, head=1.25, h=1.7, head_h=0.75):
    """an up-arrow, its base at y = 0"""
    return [(-w / 2, 0), (w / 2, 0), (w / 2, h - head_h), (head / 2, h - head_h), (0, h), (-head / 2, h - head_h), (-w / 2, h - head_h)]


def plus_outline(arm=0.42, span=1.4):
    a, s = arm / 2, span / 2
    return [(-a, -s), (a, -s), (a, -a), (s, -a), (s, a), (a, a), (a, s), (-a, s), (-a, a), (-s, a), (-s, -a), (-a, -a)]


def ring_arrow_outline(r=1.0, band=0.26, a0=20, a1=160, head=0.62, head_len=34):
    """a curved arrow: a band round the circle from angle a0 to a1 (degrees, counter-clockwise), with a head at a1"""
    out, inn = r + band / 2, r - band / 2
    steps = 24
    end = a1 - head_len
    pts = []
    for i in range(steps + 1):          # outer edge, a0 -> end
        a = math.radians(a0 + (end - a0) * i / steps)
        pts.append((math.cos(a) * out, math.sin(a) * out))
    e = math.radians(end)
    pts.append((math.cos(e) * (r + head / 2), math.sin(e) * (r + head / 2)))
    t = math.radians(a1)
    pts.append((math.cos(t) * r, math.sin(t) * r))
    pts.append((math.cos(e) * (r - head / 2), math.sin(e) * (r - head / 2)))
    for i in range(steps + 1):          # inner edge, end -> a0
        a = math.radians(end + (a0 - end) * i / steps)
        pts.append((math.cos(a) * inn, math.sin(a) * inn))
    return pts


def snowflake(name, radius, loc, mat, thick=0.08, rot=(90, 0, 0)):
    """a chunky six-armed snowflake (bars and chevrons), in the XY plane before rot (default: faces -Y)"""
    bm = bmesh.new()
    w = radius * 0.2
    for k in range(3):
        box_into(bm, (radius * 2, w, thick), (0, 0, 0), (0, 0, k * 60))
    for k in range(6):
        a = math.radians(k * 60)
        tip = Vector((math.cos(a), math.sin(a), 0)) * radius * 0.6
        for turn in (-50, 50):
            b = math.radians(k * 60 + turn)
            c = tip + Vector((math.cos(b), math.sin(b), 0)) * radius * 0.18
            box_into(bm, (radius * 0.38, w * 0.85, thick), c, (0, 0, k * 60 + turn))
    cyl_into(bm, radius * 0.22, thick * 1.1, segments=6)
    ob = finish_mesh(name, bm, [mat], bevel=min(thick, w) * 0.3)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.view_layer.update()
    return ob


def turn(objs, yaw, tilt=0.0):
    """turn a group of objects together round the origin: yaw about Z, then tilt (roll) about Y, in degrees"""
    bpy.context.view_layer.update()
    M = Matrix.Rotation(math.radians(tilt), 4, 'Y') @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
    for o in objs:
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()


def add_building(bid, tier=1, loc=(0, 0, 0), yaw=0.0):
    """the tier's station from the building's own .blend: its meshes (not the upgrade parts, effects or attachments)"""
    path = os.path.join(BUILDINGS, bid, bid + '.blend')
    prefix = '%sT%d' % (bid, tier)

    def wanted(n):
        if not n.startswith(prefix):
            return False
        rest = n[len(prefix):]
        if rest == '':
            return True
        return not (rest[0].isdigit() or rest[0] == '_' or rest.startswith('Fx') or (rest[0] == 'U' and rest[1:2].isdigit()))

    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if wanted(n)]
    root = None
    for o in dst.objects:
        link(o)
        if o.name == prefix:
            root = o
    palette = os.path.join(REPO, 'assets', 'textures', 'BuildingPalette.png')
    for img in bpy.data.images:
        if img.name.startswith('BuildingPalette') and os.path.exists(palette):
            img.filepath = palette
            img.reload()
    meshes = [o for o in dst.objects if o.type == 'MESH']
    if root is None:
        root = next(o for o in dst.objects if o.parent is None)
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    return meshes


def ui_building(bid):
    objs = add_building(bid)
    camera(objs, **BUILDING_VIEW)
    render_layers(ui_out('Building_' + bid), [('main', objs)])


for _bid in BUILDING_IDS:
    globals()['ui_Building_' + _bid] = (lambda b: (lambda: ui_building(b)))(_bid)


# The pick icons push each tier's head colour much further than the game models' palette swatches, so the six
# tiers tell apart at 48 px (the models themselves are unchanged). Per tier: (dark, main, light) sRGB that the
# head's own palette shading is remapped to (its most common shade becomes `main`), metallic, self-light.
PICK_HEADS = {
    1: ((74, 32, 8), (172, 84, 32), (228, 150, 88), 0.0, 0.15),       # warm brown wood
    2: ((52, 54, 60), (150, 153, 160), (226, 228, 232), 0.0, 0.05),   # grey stone
    3: ((14, 26, 58), (58, 92, 160), (150, 190, 245), 0.45, 0.08),    # dark steel-blue iron
    4: ((140, 70, 0), (255, 196, 20), (255, 245, 150), 0.55, 0.12),   # gold
    5: ((0, 110, 160), (40, 220, 255), (210, 255, 255), 0.0, 0.35),   # cyan crystal
    6: ((45, 0, 120), (120, 45, 255), (205, 150, 255), 0.0, 0.5),     # violet cosmic
}


PICK_HEAD_SCALE = 1.15


def _median_luminance(ob):
    """the area-weighted median linear luminance of the palette swatches on the head's two points (the faces
    away from the handle, |x| > 0.35; the collar, rope and gems don't count)"""
    me = ob.data
    img = next(n for n in me.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE').image
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    uv = me.uv_layers.active.data
    samples = []
    for p in me.polygons:
        if abs(p.center.x) < 0.35:
            continue
        u = sum(uv[i].uv.x for i in p.loop_indices) / p.loop_total
        v = sum(uv[i].uv.y for i in p.loop_indices) / p.loop_total
        r, g, b = px[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w))), :3]
        if img.colorspace_settings.name == 'sRGB':
            r, g, b = (((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in (r, g, b))
        samples.append((0.2126 * r + 0.7152 * g + 0.0722 * b, p.area))
    samples.sort()
    half, acc = sum(a for _, a in samples) / 2, 0.0
    for lum, a in samples:
        acc += a
        if acc >= half:
            return max(lum, 1e-3)
    return 0.2


def pick_head_material(tier, ob):
    """the palette texture's luminance, divided by the head's median, through a dark-main-light ramp"""
    dark, main, light, metal, emit = PICK_HEADS[tier]
    median = _median_luminance(ob)
    src = ob.data.materials[0]
    img = next(n for n in src.node_tree.nodes if n.type == 'TEX_IMAGE').image
    m = bpy.data.materials.new('PickHeadT%d' % tier)
    m.use_nodes = True
    nt = m.node_tree
    P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image, tex.interpolation = img, 'Closest'
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    scale = nt.nodes.new('ShaderNodeMath')
    scale.operation, scale.inputs[1].default_value = 'MULTIPLY', 0.5 / median    # the median shade lands at 0.5
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.15, lin(dark)
    els[1].position, els[1].color = 0.9, lin(light)
    mid = els.new(0.5)
    mid.color = lin(main)
    nt.links.new(tex.outputs['Color'], bw.inputs[0])
    nt.links.new(bw.outputs[0], scale.inputs[0])
    nt.links.new(scale.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], P.inputs['Base Color'])
    nt.links.new(ramp.outputs['Color'], P.inputs['Emission Color'])
    P.inputs['Emission Strength'].default_value = emit
    P.inputs['Metallic'].default_value = metal
    P.inputs['Roughness'].default_value = 0.32 if metal else 0.45
    if 'Coat Weight' in P.inputs:
        P.inputs['Coat Weight'].default_value = 0.3
    return m


def _pick_icon(tier):
    picks, root = add_pick(tier, (0, 0, 0), PICK_ROT)
    for o in picks:
        # the cosmic head's points are glow meshes: tint them too (they keep some self-light)
        if 'Head' in o.name and o.data.materials and o.data.materials[0].name.startswith('BuildingPalette') \
                and ('Glow' not in o.data.materials[0].name or tier == 6):
            o.data.materials[0] = pick_head_material(tier, o)
    head = root.matrix_world @ Vector((0, 0, 3.15))
    grow = Matrix.Translation(head) @ Matrix.Scale(PICK_HEAD_SCALE, 4) @ Matrix.Translation(-head)
    for o in picks:
        if 'Head' in o.name:            # a slightly bigger head: more of the tier colour at 48 px
            o.matrix_world = grow @ o.matrix_world
    bpy.context.view_layer.update()
    camera(picks, yaw=0, pitch=8, lens=60, fill=0.9)
    render_layers(ui_out('Pick%d' % tier), [('main', picks)], {'head': head})


for _t in range(1, 7):
    globals()['ui_Pick%d' % _t] = (lambda t: (lambda: _pick_icon(t)))(_t)


# The 18 tools (Tool1-Tool18): each tool leaning right with its head at the top, the striking side out; the
# composer puts its tier colour behind the head and its tier number in a badge.
TOOL_ROT = (0, 40, -14)


def _tool_icon(tier):
    objs, root = add_tool(tier, (0, 0, 0), TOOL_ROT)
    heads = json.load(open(os.path.join(WORK, 'tools.json')))
    head = root.matrix_world @ Vector(heads[str(tier)])
    camera(objs, yaw=0, pitch=8, lens=60, fill=0.9)
    render_layers(ui_out('Tool%d' % tier), [('main', objs)], {'head': head})


for _t in range(1, 19):
    globals()['ui_Tool%d' % _t] = (lambda t: (lambda: _tool_icon(t)))(_t)


def ui_Build():
    objs = add_building('IcePickPost')
    wood, steel = plastic('HammerWood', (165, 100, 50), 0.5), plastic('HammerSteel', (175, 185, 200), 0.3, metal=0.5)
    bm = bmesh.new()
    cyl_into(bm, 0.16, 2.6, (0, 0, 1.3), mat_index=0, segments=12)
    box_into(bm, (1.25, 0.55, 0.6), (0.15, 0, 2.75), mat_index=1)
    box_into(bm, (0.2, 0.62, 0.68), (-0.5, 0, 2.75), mat_index=1)
    hammer = finish_mesh('Hammer', bm, [wood, steel], bevel=0.08)
    hammer.location = (1.9, -2.2, 0.4)
    hammer.rotation_euler = (math.radians(8), math.radians(-28), math.radians(-30))
    bpy.context.view_layer.update()
    camera(objs + [hammer], **BUILDING_VIEW)
    render_layers(ui_out('Build'), [('station', objs), ('hammer', [hammer])])


def ui_Upgrades():
    arrow = slab('Arrow', arrow_outline(0.62, 1.5, 2.1, 0.9), 0.45, plastic('ArrowGreen', GREEN, 0.3, emit=0.12),
                 round_edge=0.12, loc=(0.75, 0.6, 0.7), rot=(90, 0, 0), scale=1.35)
    picks, root = add_pick(4, (-0.5, -0.4, 0.0), (0, 38, -12), 1.0)
    camera(picks + [arrow], yaw=0, pitch=8, lens=60, fill=0.92)
    render_layers(ui_out('Upgrades'), [('arrow', [arrow]), ('pick', picks)])


def ui_Pets():
    pet = add_pet('SnowBunny', (0, 0, 0), yaw=-22, size=1.0, clip='Cheer', frame=CHEER['SnowBunny'])
    camera([pet], yaw=-10, pitch=12, lens=60, fill=0.92)
    render_layers(ui_out('Pets'), [('main', [pet])])


def ui_Book():
    cover, pages, gold = plastic('Cover', (60, 150, 235), 0.4, emit=0.08), plastic('Pages', (250, 244, 225), 0.6), \
        plastic('Gold', GOLD, 0.3, metal=0.4, emit=0.1)
    W, D, H = 1.5, 0.62, 1.85
    parts = [((W, 0.12, H), (0.04, -D / 2 + 0.06, H / 2), (0, 0, 0), 0),         # front cover
             ((W, 0.12, H), (0.04, D / 2 - 0.06, H / 2), (0, 0, 0), 0),          # back cover
             ((0.18, D, H), (-W / 2 + 0.07, 0, H / 2), (0, 0, 0), 0),            # spine
             ((W - 0.2, D - 0.2, H - 0.14), (0.06, 0, H / 2), (0, 0, 0), 1)]     # pages
    for z in (0.28, H - 0.28):                                                   # gold bands on the spine
        parts.append(((0.24, D + 0.04, 0.14), (-W / 2 + 0.07, 0, z), (0, 0, 0), 2))
    book = boxes('Book', parts, [cover, pages, gold], bevel=0.05)
    bm = bmesh.new()                                                              # a gold paw on the front cover
    y = -D / 2 - 0.02
    cyl_into(bm, 0.3, 0.08, (0.08, y, 0.78), (90, 0, 0), segments=24)
    for dx, dz in ((-0.3, 1.1), (-0.11, 1.24), (0.11, 1.24), (0.3, 1.1)):
        cyl_into(bm, 0.12, 0.08, (0.08 + dx * 1.05, y, dz), (90, 0, 0), segments=16)
    paw = finish_mesh('Paw', bm, [gold], bevel=0.025)
    paw.scale = (1, 1, 1)
    pet = add_pet('PenguinChick', (0.1, 0.45, 0.95), yaw=20, size=1.9, clip='Cheer', frame=CHEER['PenguinChick'])
    turn([book, paw, pet.parent], -30)
    camera([book, paw, pet], yaw=5, pitch=14, lens=60, fill=0.92)
    render_layers(ui_out('Book'), [('pet', [pet]), ('book', [book, paw])])


def ui_Rebirth():
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.78)
    core = finish_mesh('FrostCore', bm, [plastic('Core', (120, 205, 255), 0.08, emit=0.55, emit_colour=(150, 230, 255), coat=0.8)], smooth=False)
    core.rotation_euler = (0.3, 0.2, 0.4)
    ring_mat = plastic('RingArrow', (255, 205, 70), 0.3, metal=0.3, emit=0.12)
    arrows = [slab('RingA', ring_arrow_outline(1.32, 0.32, 15, 165, 0.75, 36), 0.36, ring_mat, 0.1, loc=(0, 0.15, 0), rot=(90, 0, 0)),
              slab('RingB', ring_arrow_outline(1.32, 0.32, 195, 345, 0.75, 36), 0.36, ring_mat, 0.1, loc=(0, 0.15, 0), rot=(90, 0, 0))]
    camera([core] + arrows, yaw=0, pitch=6, lens=60, fill=0.92)
    render_layers(ui_out('Rebirth'), [('arrows', arrows), ('core', [core])])


def ui_Home():
    """a cosy igloo: ice bricks round a dome, a snow cap, a tunnel with a warm glowing doorway"""
    ice_a, ice_b = plastic('IceA', (150, 215, 255), 0.25, emit=0.1), plastic('IceB', (205, 238, 255), 0.25, emit=0.1)
    inner = plastic('IceInner', (110, 180, 235), 0.4)
    snow = plastic('Snow', (250, 252, 255), 0.6, emit=0.05)
    door = plastic('Door', (255, 175, 70), 0.5, emit=2.2, emit_colour=(255, 170, 70))
    R = 1.3
    bm = bmesh.new()
    rows = 5
    for row in range(rows):
        phi0, phi1 = row / rows * 78, (row + 1) / rows * 78
        phi = math.radians((phi0 + phi1) / 2)
        r = R * math.cos(phi)
        count = max(5, int(round(2 * math.pi * r / 0.62)))
        h = R * math.radians(phi1 - phi0) * 0.92
        for k in range(count):
            a = (k + 0.5 * (row % 2)) / count * 360
            ar = math.radians(a)
            loc = (math.cos(ar) * r, math.sin(ar) * r, R * math.sin(phi))
            box_into(bm, (0.24, 2 * math.pi * r / count * 0.93, h), loc, (0, -math.degrees(phi), a), (row + k) % 2)
    dome = finish_mesh('Dome', bm, [ice_a, ice_b], bevel=0.045)
    bm = bmesh.new()                                                     # the solid dome behind the bricks
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=R - 0.1)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    shell = finish_mesh('Shell', bm, [inner])
    bm = bmesh.new()                                                     # the snow cap
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.62)
    cap = finish_mesh('Cap', bm, [snow])
    cap.location, cap.scale = (0.05, 0.0, R - 0.02), (1.0, 1.0, 0.55)
    bm = bmesh.new()                                                     # the tunnel: a half cylinder of bricks
    tr, tl = 0.62, 0.8
    for k in range(7):
        a = k / 6 * 180
        ar = math.radians(a)
        box_into(bm, (0.26, tl, 0.3), (math.cos(ar) * tr, 0, math.sin(ar) * tr), (0, -a, 0), k % 2)
    tunnel_bricks = finish_mesh('Tunnel', bm, [ice_a, ice_b], bevel=0.045)
    tunnel_bricks.location = (0, -R + 0.05, 0)
    bm = bmesh.new()
    cyl_into(bm, tr - 0.04, tl * 0.98, (0, 0, 0), (90, 0, 0), segments=24)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    tunnel_core = finish_mesh('TunnelCore', bm, [inner])
    tunnel_core.location = (0, -R + 0.05, 0)
    bm = bmesh.new()                                                     # the warm doorway
    cyl_into(bm, tr - 0.2, 0.06, (0, 0, 0), (90, 0, 0), segments=24)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    doorway = finish_mesh('Doorway', bm, [door])
    doorway.location = (0, -R + 0.05 - tl / 2 - 0.03, 0)
    bm = bmesh.new()                                                     # snow drifts round the foot
    for k, (x, y, s) in enumerate(((-1.25, -0.35, 0.42), (1.2, -0.5, 0.38), (0.75, -1.25, 0.3), (-0.8, -1.2, 0.28), (1.35, 0.5, 0.36))):
        ret = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=s)
        bmesh.ops.scale(bm, vec=(1.4, 1.1, 0.55), verts=ret['verts'])
        bmesh.ops.translate(bm, vec=(x, y, 0.02), verts=ret['verts'])
    drifts = finish_mesh('Drifts', bm, [snow])
    objs = [dome, shell, cap, tunnel_bricks, tunnel_core, doorway, drifts]
    turn(objs, -20)
    camera(objs, yaw=-14, pitch=20, lens=55, fill=0.92)
    render_layers(ui_out('Home'), [('main', objs)])


def ui_Shop():
    """an open treasure chest heaped with crystals"""
    wood, wood_dark, gold = plastic('ChestWood', (185, 105, 50), 0.55), plastic('ChestWoodDark', (130, 70, 35), 0.6), \
        plastic('ChestGold', GOLD, 0.3, metal=0.45, emit=0.1)
    W, D, H = 1.9, 1.2, 0.95
    parts = [((W, D, H), (0, 0, H / 2), (0, 0, 0), 0)]
    for x in (-W / 2 + 0.28, W / 2 - 0.28):                                     # gold straps
        parts.append(((0.2, D + 0.06, H + 0.04), (x, 0, H / 2), (0, 0, 0), 2))
    parts.append(((W + 0.06, D + 0.06, 0.14), (0, 0, H - 0.07), (0, 0, 0), 2))   # gold rim
    parts.append(((W + 0.04, D + 0.04, 0.1), (0, 0, 0.05), (0, 0, 0), 1))        # dark foot
    parts.append(((0.34, 0.14, 0.4), (0, -D / 2 - 0.05, H - 0.3), (0, 0, 0), 2))  # the lock
    body = boxes('ChestBody', parts, [wood, wood_dark, gold], bevel=0.04)
    lid_parts = [((W, D, 0.34), (0, -D / 2, 0.17), (0, 0, 0), 0),
                 ((W + 0.06, D + 0.06, 0.12), (0, -D / 2, 0.06), (0, 0, 0), 2)]
    for x in (-W / 2 + 0.28, W / 2 - 0.28):
        lid_parts.append(((0.2, D + 0.06, 0.38), (x, -D / 2, 0.17), (0, 0, 0), 2))
    lid = boxes('ChestLid', lid_parts, [wood, wood_dark, gold], bevel=0.04)
    lid.location = (0, D / 2, H)
    lid.rotation_euler = (math.radians(-105), 0, 0)
    bpy.context.view_layer.update()
    gems = gem_pile((0, -0.05, H - 0.25), 0.82, 0.5, 0.3, seed=31, density=1.3)
    gems += [gem((0.05, -0.15, H + 0.55), 0.62, (math.radians(10), math.radians(-14), 0.3))]
    gems += [gem((-1.05, -0.75, 0.12), 0.3, (0.3, 1.3, 0.2)), gem((1.1, -0.7, 0.1), 0.26, (1.2, 0.4, 0.8))]
    objs = [body, lid]
    turn(objs + gems, -22)
    camera(objs + gems, yaw=-6, pitch=24, lens=55, fill=0.92)
    render_layers(ui_out('Shop'), [('main', objs + gems)])


def ui_Codes():
    """a gold ticket with a snowflake on it"""
    W, H, notch = 2.4, 1.3, 0.24
    corner = 0.16
    pts = [(-W / 2 + corner, -H / 2), (W / 2 - corner, -H / 2), (W / 2, -H / 2 + corner)]
    for i in range(13):                                       # the right notch
        a = math.radians(-90 + 180 * i / 12)
        pts.append((W / 2 - math.cos(a) * notch, math.sin(a) * notch))
    pts += [(W / 2, H / 2 - corner), (W / 2 - corner, H / 2), (-W / 2 + corner, H / 2), (-W / 2, H / 2 - corner)]
    for i in range(13):                                       # the left notch
        a = math.radians(90 - 180 * i / 12)
        pts.append((-W / 2 + math.cos(a) * notch, math.sin(a) * notch))
    pts.append((-W / 2, -H / 2 + corner))
    ticket = slab('Ticket', pts, 0.22, plastic('Ticket', (255, 200, 60), 0.35, emit=0.12), round_edge=0.07, rot=(90, 0, 0))
    bm = bmesh.new()                                           # the tear line: a row of dashes
    for i in range(5):
        box_into(bm, (0.07, 0.06, 0.16), (-0.42, -0.13, -0.48 + i * 0.24))
    dashes = finish_mesh('Dashes', bm, [plastic('TicketDark', (215, 130, 30), 0.5)], bevel=0.02)
    flake = snowflake('Flake', 0.42, (0.4, -0.14, 0.0), plastic('Flake', (90, 185, 255), 0.3, emit=0.15), thick=0.08)
    star = snowflake('FlakeSmall', 0.2, (-0.82, -0.14, 0.0), plastic('Flake2', (255, 255, 255), 0.3, emit=0.1), thick=0.06)
    objs = [ticket, dashes, flake, star]
    turn(objs, -14, tilt=-16)
    camera(objs, yaw=-6, pitch=14, lens=60, fill=0.92)
    render_layers(ui_out('Codes'), [('main', objs)])


def ui_FrostTouch():
    """the pick wrapped in a frost swirl"""
    picks, root = add_pick(3, (0, 0, 0), PICK_ROT)
    pts, radii = [], []
    turns, z0, z1 = 1.6, 0.5, 3.6
    for i in range(80):
        t = i / 79
        a = t * turns * math.tau + 0.6
        r = 0.55 + 0.35 * math.sin(t * math.pi)
        pts.append((math.cos(a) * r, math.sin(a) * r, z0 + (z1 - z0) * t))
        radii.append(0.25 + 0.75 * math.sin(t * math.pi) ** 0.7)
    swirl = slab('Swirl', pts, 0, plastic('Frost', (120, 215, 255), 0.2, emit=0.9, emit_colour=(130, 215, 255)), round_edge=0.11,
                 rot=(0, 0, 0), tube=True, radii=radii)
    swirl.parent = root
    frost = ice_material('FrostChip', cracks=0, alpha=0.7, tint=(120, 200, 245))
    chips = []
    rng = random.Random(4)
    for i in range(7):                                       # ice crusted on the head
        x = rng.uniform(-1.0, 1.0)
        s = shard((x, rng.uniform(-0.2, 0.2), 3.05 + rng.uniform(-0.15, 0.2)), rng.uniform(0.25, 0.4), 70 + i, frost, stretch=1.3)
        s.parent = root
        chips.append(s)
    bpy.context.view_layer.update()
    camera(picks + [swirl] + chips, yaw=0, pitch=8, lens=60, fill=0.9)
    render_layers(ui_out('FrostTouch'), [('main', picks + chips + [swirl])])


def ui_BiggerBurst():
    block = ice_block((0, 0, 0), (1.5, 1.5, 0.55), cracks=1.0, seed=41)
    mat = ice_material('ShardIce', cracks=0, alpha=0.5, tint=(120, 200, 245))
    rim = broken_rim(1.5, 1.5, 0.55, mat, seed=7, count=13, height=0.5)
    gems = [gem((0.0, -0.1, 1.45), 0.7, (math.radians(8), math.radians(-10), 0.3))]
    for i, (deg, r, size) in enumerate(((20, 1.35, 0.42), (48, 1.5, 0.48), (78, 1.75, 0.4), (104, 1.65, 0.46), (133, 1.5, 0.48),
                                        (160, 1.3, 0.42), (64, 0.95, 0.32), (118, 1.0, 0.34))):
        a = math.radians(deg)
        gems.append(gem((math.cos(a) * r * 1.05, -0.15, 0.55 + math.sin(a) * r * 0.95), size,
                        (math.radians(10), -(a - math.pi / 2) * 0.8, 0.4 * i)))
    objs = block + rim + gems
    camera(objs, yaw=-14, pitch=18, lens=50, fill=0.92)
    render_layers(ui_out('BiggerBurst'), [('main', objs)])


def ui_CrystalYield():
    pile = gem_pile((0, 0, 0), 0.95, 0.6, 0.36, seed=51)
    pile += [gem((-0.1, -0.15, 0.95), 0.72, (math.radians(10), math.radians(-14), 0.3))]
    plus = slab('Plus', plus_outline(0.55, 1.5), 0.4, plastic('PlusGreen', GREEN, 0.3, emit=0.12), round_edge=0.12,
                loc=(1.05, -0.9, 1.35), rot=(90, 0, -18), scale=0.8)
    camera(pile + [plus], yaw=-16, pitch=24, lens=55, fill=0.92)
    render_layers(ui_out('CrystalYield'), [('pile', pile), ('plus', [plus])])


def ui_FastSled():
    """a wooden sled on two metal runners, carrying an ice block (the speed streaks are 2D, in compose)"""
    wood, wood_dark = plastic('SledWood', (200, 120, 55), 0.5), plastic('SledWoodDark', (150, 80, 35), 0.55)
    steel = plastic('Runner', (190, 200, 215), 0.25, metal=0.6)
    L, Wd = 2.5, 1.3
    parts = []
    for i, y in enumerate((-0.42, 0.0, 0.42)):
        parts.append(((L, 0.38, 0.12), (0, y, 0.55), (0, 0, 0), i % 2))
    for x in (-0.85, 0.0, 0.85):
        parts.append(((0.2, Wd + 0.1, 0.12), (x, 0, 0.44), (0, 0, 0), 1))
        for y in (-0.55, 0.55):
            parts.append(((0.14, 0.12, 0.38), (x, y, 0.25), (0, 0, 0), 1))
    deck = boxes('SledDeck', parts, [wood, wood_dark], bevel=0.035)
    runner_pts = []
    for i in range(9):
        runner_pts.append((-1.3 + i * 0.28, 0.06))
    for i in range(1, 15):                                  # the curl at the front
        a = math.radians(-90 + i * 18)
        runner_pts.append((1.0 + math.cos(a) * 0.42, 0.48 + math.sin(a) * 0.42))
    runners = []
    for y in (-0.55, 0.55):
        runners.append(slab('Runner', [(x, y, z) for x, z in runner_pts], 0, steel, round_edge=0.075, rot=(0, 0, 0), tube=True))
    block = ice_block((-0.1, 0, 0.61), (1.05, 1.0, 1.0), cracks=0.5, seed=61, pet='SealPup', pet_size=0.75, pet_yaw=-60,
                      orb=(140, 220, 255), orb_strength=5.0, view=(-22, 16))
    objs = [deck] + runners + block
    camera(objs, yaw=-22, pitch=16, lens=55, fill=0.92)
    render_layers(ui_out('FastSled'), [('main', objs)])


def ui_UpgradeBadge():
    arrow = slab('Arrow', arrow_outline(0.62, 1.5, 2.0, 0.9), 0.5, plastic('ArrowGreen', GREEN, 0.3, emit=0.12),
                 round_edge=0.13, rot=(90, 0, -14))
    camera([arrow], yaw=0, pitch=8, lens=60, fill=0.9)
    render_layers(ui_out('UpgradeBadge'), [('main', [arrow])])


UI_ICONS = {k[3:]: v for k, v in globals().items() if k.startswith('ui_') and k != 'ui_out' and k != 'ui_building' and callable(v)}

if __name__ == '__main__':
    if MODE == 'picks':
        build_picks()
    elif MODE == 'tools':
        build_tools()
    elif MODE in ('render', 'ui'):
        table = ICONS if MODE == 'render' else UI_ICONS
        for icon in NAMES or sorted(table):
            reset()
            _templates.clear()
            _gem.clear()
            _silhouette = None
            table[icon]()
            print('ICON_DONE', icon)
    else:
        raise SystemExit('mode must be picks, tools, render or ui')
