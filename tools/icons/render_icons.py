"""render_icons.py - the 3D half of the store and game icons (headless Blender, EEVEE).

Renders each icon's subject on a transparent background at 1024x1024, in one or more layers (back to
front), for tools/icons/compose_icons.py to put on a background with outlines, glows, sparkles and text.
Usually run through compose_icons.py (--render), which calls Blender for you:

    python tools/icons/compose_icons.py --render                 # everything
    python tools/icons/compose_icons.py --render VIP LuckyIce    # some icons

By hand (Blender 5.x; the newest under C:\\Program Files\\Blender Foundation\\):
    blender -b --factory-startup --python tools/icons/render_icons.py -- picks  <work dir>
    blender -b --factory-startup --python tools/icons/render_icons.py -- render <work dir> <IconName>

  picks   builds the six ice pick tiers from tools/blender/tools_ice_picks.py (its geometry, nothing is
          written to store-assets/tools/) into <work>/picks.blend, which the icon scenes append from.
  render  renders one icon into <work>/<IconName>/: <layer>.png per layer and meta.json (the layer order
          plus a few projected 2D points, e.g. the pick's pivot for the motion arcs).

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

if __name__ == '__main__':
    if MODE == 'picks':
        build_picks()
    elif MODE == 'render':
        for icon in NAMES or sorted(ICONS):
            reset()
            _templates.clear()
            _gem.clear()
            _silhouette = None
            ICONS[icon]()
            print('ICON_DONE', icon)
    else:
        raise SystemExit('mode must be picks or render')
